"""
Signal handlers for syncing Product instances with Meta (Facebook) Catalog.

These signals automatically trigger catalog operations when products are
created, updated, or deleted in the local database.
"""
import logging
import threading
from datetime import timedelta
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Product

logger = logging.getLogger(__name__)

# Thread-local storage to prevent recursive signal calls
_thread_locals = threading.local()

# Maximum sync attempts before giving up
MAX_SYNC_ATTEMPTS = 5
# Minimum time between retry attempts (exponential backoff)
MIN_RETRY_DELAY_MINUTES = 5


@receiver(post_save, sender=Product)
def sync_product_to_meta_catalog(sender, instance, created, **kwargs):
    """
    Sync product to Meta Catalog when a Product is created or updated.
    
    Args:
        sender: The model class (Product)
        instance: The actual Product instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Prevent recursive calls - check if we're already processing this product
    processing_key = f"syncing_product_{instance.pk}"
    if getattr(_thread_locals, processing_key, False):
        logger.debug(
            f"Skipping recursive signal for Product '{instance.name}' (ID: {instance.id})"
        )
        return
    
    # Skip sync if this is an internal update (e.g., only updating meta sync tracking fields)
    update_fields = kwargs.get('update_fields')
    if update_fields is not None:
        sync_related_fields = {'whatsapp_catalog_id', 'meta_sync_attempts', 'meta_sync_last_error', 
                               'meta_sync_last_attempt', 'meta_sync_last_success'}
        if set(update_fields).issubset(sync_related_fields):
            logger.debug(
                f"Skipping Meta sync for Product '{instance.name}' (ID: {instance.id}) - "
                "internal sync tracking update only"
            )
            return
    
    # Import here to avoid circular imports
    from meta_integration.catalog_service import MetaCatalogService
    
    # Only sync active products with valid SKU
    if not instance.sku:
        logger.warning(
            f"Product '{instance.name}' (ID: {instance.id}) has no SKU. "
            "Skipping Meta Catalog sync."
        )
        return
    
    if not instance.is_active:
        logger.info(
            f"Product '{instance.name}' (ID: {instance.id}) is inactive. "
            "Skipping Meta Catalog sync."
        )
        return
    
    # Check if we've exceeded max sync attempts
    if instance.meta_sync_attempts >= MAX_SYNC_ATTEMPTS:
        logger.warning(
            f"Product '{instance.name}' (ID: {instance.id}) has exceeded maximum sync attempts "
            f"({MAX_SYNC_ATTEMPTS}). Skipping sync. Last error: {instance.meta_sync_last_error}"
        )
        return
    
    # Implement exponential backoff for retries
    if instance.meta_sync_attempts > 0 and instance.meta_sync_last_attempt:
        # Calculate minimum delay: 5min, 15min, 45min, 2.25hr, 6.75hr
        delay_minutes = MIN_RETRY_DELAY_MINUTES * (3 ** (instance.meta_sync_attempts - 1))
        next_retry_time = instance.meta_sync_last_attempt + timedelta(minutes=delay_minutes)
        
        if timezone.now() < next_retry_time:
            logger.info(
                f"Product '{instance.name}' (ID: {instance.id}) is in backoff period. "
                f"Next retry at {next_retry_time.isoformat()}. "
                f"Attempt {instance.meta_sync_attempts}/{MAX_SYNC_ATTEMPTS}"
            )
            return
    
    # Set processing flag to prevent recursion
    setattr(_thread_locals, processing_key, True)
    
    # Track the sync attempt
    sync_attempt_time = timezone.now()
    
    try:
        catalog_service = MetaCatalogService()
        
        if created:
            # New product - create in catalog
            logger.info(
                f"Creating new product in Meta Catalog: '{instance.name}' "
                f"(ID: {instance.id}, SKU: {instance.sku}) - Attempt {instance.meta_sync_attempts + 1}/{MAX_SYNC_ATTEMPTS}"
            )
            response = catalog_service.create_product_in_catalog(instance)
            
            # Store the catalog ID returned by Meta
            if response and 'id' in response:
                # Success! Update with catalog ID and reset error tracking
                Product.objects.filter(pk=instance.pk).update(
                    whatsapp_catalog_id=response['id'],
                    meta_sync_attempts=0,
                    meta_sync_last_error=None,
                    meta_sync_last_attempt=sync_attempt_time,
                    meta_sync_last_success=sync_attempt_time
                )
                logger.info(
                    f"✓ Successfully created product in Meta Catalog. "
                    f"Catalog ID: {response['id']}"
                )
            else:
                # Unexpected response format
                error_msg = f"Meta API response did not contain expected 'id' field. Response: {response}"
                logger.error(f"✗ {error_msg}")
                Product.objects.filter(pk=instance.pk).update(
                    meta_sync_attempts=instance.meta_sync_attempts + 1,
                    meta_sync_last_error=error_msg[:1000],  # Truncate to fit in DB
                    meta_sync_last_attempt=sync_attempt_time
                )
                
        else:
            # Existing product - update in catalog if it has a catalog ID
            if instance.whatsapp_catalog_id:
                logger.info(
                    f"Updating product in Meta Catalog: '{instance.name}' "
                    f"(ID: {instance.id}, Catalog ID: {instance.whatsapp_catalog_id}) - "
                    f"Attempt {instance.meta_sync_attempts + 1}/{MAX_SYNC_ATTEMPTS}"
                )
                response = catalog_service.update_product_in_catalog(instance)
                
                # Success! Reset error tracking
                Product.objects.filter(pk=instance.pk).update(
                    meta_sync_attempts=0,
                    meta_sync_last_error=None,
                    meta_sync_last_attempt=sync_attempt_time,
                    meta_sync_last_success=sync_attempt_time
                )
                logger.info(
                    f"✓ Successfully updated product in Meta Catalog. "
                    f"Response: {response}"
                )
            else:
                # Product was updated but never synced - create it
                logger.info(
                    f"Product '{instance.name}' (ID: {instance.id}) was updated but "
                    f"has no catalog ID. Creating in Meta Catalog - "
                    f"Attempt {instance.meta_sync_attempts + 1}/{MAX_SYNC_ATTEMPTS}"
                )
                response = catalog_service.create_product_in_catalog(instance)
                
                if response and 'id' in response:
                    # Success! Update with catalog ID and reset error tracking
                    Product.objects.filter(pk=instance.pk).update(
                        whatsapp_catalog_id=response['id'],
                        meta_sync_attempts=0,
                        meta_sync_last_error=None,
                        meta_sync_last_attempt=sync_attempt_time,
                        meta_sync_last_success=sync_attempt_time
                    )
                    logger.info(
                        f"✓ Successfully created product in Meta Catalog. "
                        f"Catalog ID: {response['id']}"
                    )
                else:
                    # Unexpected response format
                    error_msg = f"Meta API response did not contain expected 'id' field. Response: {response}"
                    logger.error(f"✗ {error_msg}")
                    Product.objects.filter(pk=instance.pk).update(
                        meta_sync_attempts=instance.meta_sync_attempts + 1,
                        meta_sync_last_error=error_msg[:1000],
                        meta_sync_last_attempt=sync_attempt_time
                    )
                        
    except ValueError as e:
        # Configuration errors (missing tokens, catalog ID, etc.)
        error_msg = f"Configuration error: {str(e)}"
        logger.error(
            f"✗ Configuration error syncing product '{instance.name}' "
            f"(ID: {instance.id}): {str(e)}"
        )
        Product.objects.filter(pk=instance.pk).update(
            meta_sync_attempts=instance.meta_sync_attempts + 1,
            meta_sync_last_error=error_msg[:1000],
            meta_sync_last_attempt=sync_attempt_time
        )
    except Exception as e:
        # Network errors, API errors, etc.
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(
            f"✗ Error syncing product '{instance.name}' (ID: {instance.id}) "
            f"to Meta Catalog: {error_msg}",
            exc_info=True
        )
        Product.objects.filter(pk=instance.pk).update(
            meta_sync_attempts=instance.meta_sync_attempts + 1,
            meta_sync_last_error=error_msg[:1000],
            meta_sync_last_attempt=sync_attempt_time
        )
    finally:
        # Always clear the processing flag
        setattr(_thread_locals, processing_key, False)


@receiver(post_delete, sender=Product)
def delete_product_from_meta_catalog(sender, instance, **kwargs):
    """
    Delete product from Meta Catalog when a Product is deleted.
    
    Args:
        sender: The model class (Product)
        instance: The actual Product instance being deleted
        **kwargs: Additional keyword arguments
    """
    # Import here to avoid circular imports
    from meta_integration.catalog_service import MetaCatalogService
    
    # Only attempt deletion if the product was synced to catalog
    if not instance.whatsapp_catalog_id:
        logger.info(
            f"Product '{instance.name}' (ID: {instance.id}) has no catalog ID. "
            "No deletion needed from Meta Catalog."
        )
        return
    
    try:
        catalog_service = MetaCatalogService()
        logger.info(
            f"Deleting product from Meta Catalog: '{instance.name}' "
            f"(ID: {instance.id}, Catalog ID: {instance.whatsapp_catalog_id})"
        )
        response = catalog_service.delete_product_from_catalog(instance)
        logger.info(
            f"Successfully deleted product from Meta Catalog. "
            f"Response: {response}"
        )
    except ValueError as e:
        # Configuration errors
        logger.error(
            f"Configuration error deleting product '{instance.name}' "
            f"(ID: {instance.id}): {str(e)}"
        )
    except Exception as e:
        # Network errors, API errors, etc.
        logger.error(
            f"Error deleting product '{instance.name}' (ID: {instance.id}) "
            f"from Meta Catalog: {str(e)}",
            exc_info=True
        )
