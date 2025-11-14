"""
Signal handlers for syncing Product instances with Meta (Facebook) Catalog.

These signals automatically trigger catalog operations when products are
created, updated, or deleted in the local database.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product

logger = logging.getLogger(__name__)


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
    
    try:
        catalog_service = MetaCatalogService()
        
        if created:
            # New product - create in catalog
            logger.info(
                f"Creating new product in Meta Catalog: '{instance.name}' "
                f"(ID: {instance.id}, SKU: {instance.sku})"
            )
            response = catalog_service.create_product_in_catalog(instance)
            
            # Store the catalog ID returned by Meta
            if response and 'id' in response:
                instance.whatsapp_catalog_id = response['id']
                # Use update() to avoid triggering another signal
                Product.objects.filter(pk=instance.pk).update(
                    whatsapp_catalog_id=response['id']
                )
                logger.info(
                    f"Successfully created product in Meta Catalog. "
                    f"Catalog ID: {response['id']}"
                )
            else:
                logger.warning(
                    f"Meta API response for product '{instance.name}' "
                    f"did not contain expected 'id' field. Response: {response}"
                )
                
        else:
            # Existing product - update in catalog if it has a catalog ID
            if instance.whatsapp_catalog_id:
                logger.info(
                    f"Updating product in Meta Catalog: '{instance.name}' "
                    f"(ID: {instance.id}, Catalog ID: {instance.whatsapp_catalog_id})"
                )
                response = catalog_service.update_product_in_catalog(instance)
                logger.info(
                    f"Successfully updated product in Meta Catalog. "
                    f"Response: {response}"
                )
            else:
                # Product was updated but never synced - create it
                logger.info(
                    f"Product '{instance.name}' (ID: {instance.id}) was updated but "
                    f"has no catalog ID. Creating in Meta Catalog."
                )
                response = catalog_service.create_product_in_catalog(instance)
                
                if response and 'id' in response:
                    Product.objects.filter(pk=instance.pk).update(
                        whatsapp_catalog_id=response['id']
                    )
                    logger.info(
                        f"Successfully created product in Meta Catalog. "
                        f"Catalog ID: {response['id']}"
                    )
                        
    except ValueError as e:
        # Configuration errors (missing tokens, catalog ID, etc.)
        logger.error(
            f"Configuration error syncing product '{instance.name}' "
            f"(ID: {instance.id}): {str(e)}"
        )
    except Exception as e:
        # Network errors, API errors, etc.
        logger.error(
            f"Error syncing product '{instance.name}' (ID: {instance.id}) "
            f"to Meta Catalog: {str(e)}",
            exc_info=True
        )


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
