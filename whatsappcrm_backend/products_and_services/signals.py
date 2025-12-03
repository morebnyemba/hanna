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
from .models import Product, ProductImage

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


# ============================================================================
# Product Image Signals - Trigger re-sync when images are added/updated
# ============================================================================

@receiver(post_save, sender=ProductImage)
def sync_product_on_image_change(sender, instance, created, **kwargs):
    """
    Trigger a re-sync of the parent product when a ProductImage is added or updated.
    
    This fixes the issue where images are not detected during initial product creation
    because inline images are saved AFTER the parent product in Django admin.
    
    Args:
        sender: The model class (ProductImage)
        instance: The actual ProductImage instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    product = instance.product
    
    # Skip if product doesn't have a primary key yet (shouldn't happen normally)
    if not product.pk:
        logger.debug(
            f"Skipping ProductImage signal - parent product has no PK"
        )
        return
    
    # Only trigger re-sync for products that need it:
    # 1. Products that failed sync due to missing image (likely using placeholder)
    # 2. Products that haven't been synced yet (no whatsapp_catalog_id)
    # 3. New images being added (created=True)
    
    needs_resync = False
    reason = ""
    
    if not product.whatsapp_catalog_id:
        # Product was never synced successfully - might have failed due to missing image
        needs_resync = True
        reason = "product has no catalog ID (may have failed initial sync)"
    elif created:
        # New image added to an existing product - update the catalog
        needs_resync = True
        reason = "new image added to product"
    
    if not needs_resync:
        logger.debug(
            f"Skipping ProductImage signal for '{product.name}' (ID: {product.id}) - "
            "product already synced and this is an image update, not addition"
        )
        return
    
    # Check if product is eligible for sync (has SKU and is active)
    if not product.sku:
        logger.debug(
            f"Skipping ProductImage re-sync for '{product.name}' (ID: {product.id}) - no SKU"
        )
        return
    
    if not product.is_active:
        logger.debug(
            f"Skipping ProductImage re-sync for '{product.name}' (ID: {product.id}) - inactive"
        )
        return
    
    logger.info(
        f"ProductImage saved for '{product.name}' (ID: {product.id}) - {reason}. "
        f"Triggering Meta Catalog re-sync."
    )
    
    # Reset sync attempts if the product failed previously
    # This gives the product a fresh chance to sync with the new image
    if product.meta_sync_attempts > 0:
        logger.info(
            f"Resetting sync attempts for '{product.name}' (ID: {product.id}) "
            f"from {product.meta_sync_attempts} to 0 due to new image"
        )
        Product.objects.filter(pk=product.pk).update(
            meta_sync_attempts=0,
            meta_sync_last_error=None
        )
        # Refresh the instance to get updated values
        product.refresh_from_db()
    
    # Trigger the product save which will activate the post_save signal
    # Use update_fields to indicate this is NOT a sync-related internal update
    # This will trigger sync_product_to_meta_catalog signal
    product.save(update_fields=['updated_at'])


# ============================================================================
# Item Location Tracking Signals
# ============================================================================

from warranty.models import WarrantyClaim
from customer_data.models import JobCard, Order
from .models import SerializedItem, ItemLocationHistory
from .services import ItemTrackingService


@receiver(post_save, sender=WarrantyClaim)
def track_warranty_claim_item(sender, instance, created, **kwargs):
    """
    Auto-track item location when warranty claim is created or updated.
    """
    if not instance.warranty.serialized_item:
        return
    
    item = instance.warranty.serialized_item
    
    # On creation, move item to manufacturer
    if created:
        ItemTrackingService.send_to_manufacturer(
            item=item,
            warranty_claim=instance,
            notes=f"Warranty claim {instance.claim_id} created: {instance.description_of_fault[:100]}"
        )
    
    # On status updates, track accordingly
    elif not created:
        if instance.status == WarrantyClaim.ClaimStatus.COMPLETED:
            # Return to warehouse when claim completed
            ItemTrackingService.return_to_warehouse(
                item=item,
                warranty_claim=instance,
                notes=f"Warranty claim {instance.claim_id} completed",
                mark_as_stock=True
            )
        
        elif instance.status == WarrantyClaim.ClaimStatus.REPLACED:
            # Mark old item as decommissioned
            item.status = SerializedItem.Status.DECOMMISSIONED
            item.save(update_fields=['status', 'updated_at'])


@receiver(post_save, sender=JobCard)
def track_job_card_item(sender, instance, created, **kwargs):
    """
    Auto-track item location when job card status changes.
    """
    if not instance.serialized_item:
        return
    
    item = instance.serialized_item
    
    # Skip if this is the initial creation
    if created:
        # On creation, mark as awaiting collection if item is with customer
        if item.current_location == SerializedItem.Location.CUSTOMER:
            ItemTrackingService.mark_item_awaiting_collection(
                item=item,
                job_card=instance,
                notes=f"Job card {instance.job_card_number} created: {instance.reported_fault[:100] if instance.reported_fault else 'Service required'}"
            )
        return
    
    # Track based on status changes
    if instance.status == JobCard.Status.IN_PROGRESS:
        # Assign to technician when in progress
        if instance.technician and item.current_location != SerializedItem.Location.TECHNICIAN:
            ItemTrackingService.assign_to_technician(
                item=item,
                technician=instance.technician.user,
                job_card=instance,
                notes=f"Job card {instance.job_card_number} in progress"
            )
    
    elif instance.status == JobCard.Status.AWAITING_PARTS:
        # Update item status to awaiting parts
        if item.status != SerializedItem.Status.AWAITING_PARTS:
            item.status = SerializedItem.Status.AWAITING_PARTS
            item.save(update_fields=['status', 'updated_at'])
            
            # Create history entry
            ItemLocationHistory.objects.create(
                serialized_item=item,
                from_location=item.current_location,
                to_location=item.current_location,  # Location doesn't change
                transfer_reason=ItemLocationHistory.TransferReason.REPAIR,
                notes=f"Job card {instance.job_card_number} awaiting parts",
                related_job_card=instance
            )
    
    elif instance.status == JobCard.Status.RESOLVED:
        # Mark repair as completed
        if item.status != SerializedItem.Status.REPAIR_COMPLETED:
            item.status = SerializedItem.Status.REPAIR_COMPLETED
            item.save(update_fields=['status', 'updated_at'])
            
            # If item is with technician, prepare for return
            if item.current_location == SerializedItem.Location.TECHNICIAN:
                ItemLocationHistory.objects.create(
                    serialized_item=item,
                    from_location=item.current_location,
                    to_location=item.current_location,
                    transfer_reason=ItemLocationHistory.TransferReason.REPAIR,
                    notes=f"Job card {instance.job_card_number} resolved - ready for return",
                    related_job_card=instance
                )
    
    elif instance.status == JobCard.Status.CLOSED:
        # Return to warehouse when job closed
        if item.current_location != SerializedItem.Location.WAREHOUSE:
            ItemTrackingService.return_to_warehouse(
                item=item,
                job_card=instance,
                notes=f"Job card {instance.job_card_number} closed",
                mark_as_stock=True
            )


@receiver(post_save, sender=Order)
def track_order_item_delivery(sender, instance, created, **kwargs):
    """
    Track item location when order is delivered.
    Handles serialized items in order items.
    """
    # Only process when order is marked as delivered/closed_won
    if instance.stage != Order.Stage.CLOSED_WON:
        return
    
    # Check if payment is complete
    if instance.payment_status != Order.PaymentStatus.PAID:
        return
    
    # Process each order item
    for order_item in instance.items.all():
        # Check if product has serialized items that need tracking
        # This would require additional logic to link order items to specific serialized items
        # For now, we'll just update any serialized items that are marked for this order
        serialized_items = SerializedItem.objects.filter(
            product=order_item.product,
            status=SerializedItem.Status.SOLD,
            location_history__related_order=instance
        ).distinct()
        
        for item in serialized_items:
            if item.status != SerializedItem.Status.DELIVERED:
                item.status = SerializedItem.Status.DELIVERED
                item.save(update_fields=['status', 'updated_at'])
                
                # Create history entry
                ItemLocationHistory.objects.create(
                    serialized_item=item,
                    from_location=item.current_location,
                    to_location=SerializedItem.Location.CUSTOMER,
                    transfer_reason=ItemLocationHistory.TransferReason.DELIVERY,
                    notes=f"Order {instance.order_number} delivered",
                    related_order=instance
                )
