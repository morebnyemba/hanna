"""
Celery tasks for products_and_services app.
"""
import logging
from celery import shared_task
from typing import Dict, Any

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_sync_zoho_products(self) -> Dict[str, Any]:
    """
    Celery task to sync products from Zoho Inventory to the database.
    
    This task wraps the sync logic to run asynchronously, preventing
    the UI from freezing during large syncs.
    
    Returns:
        Dict containing sync statistics and results
    """
    from .services import sync_zoho_products_to_db
    
    logger.info("Starting Zoho product sync task...")
    
    try:
        result = sync_zoho_products_to_db()
        logger.info(f"Zoho sync task completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Zoho sync task failed: {str(e)}")
        # Retry the task if it fails
        raise self.retry(exc=e)


@shared_task(queue='celery')
def check_low_stock_products():
    """
    Check for products with low stock levels and send alerts to admins.
    Should be run daily or multiple times per day via Celery Beat.
    
    Default threshold: Alert when stock_quantity <= 10
    """
    from .models import Product
    from notifications.services import queue_notifications_to_users
    
    logger.info("Starting low stock check task")
    
    try:
        # Configurable threshold (could be moved to settings or database)
        LOW_STOCK_THRESHOLD = 10
        
        # Find products with low stock (active products only)
        low_stock_products = Product.objects.filter(
            is_active=True,
            stock_quantity__lte=LOW_STOCK_THRESHOLD,
            stock_quantity__gt=0  # Don't alert on completely out of stock
        ).select_related('category')
        
        notifications_sent = 0
        
        for product in low_stock_products:
            context = {
                'product_name': product.name,
                'product_sku': product.sku or 'No SKU',
                'stock_quantity': str(product.stock_quantity),
            }
            
            # Send to System Admins and Inventory Manager groups
            queue_notifications_to_users(
                template_name='pfungwa_low_stock_alert',
                group_names=["System Admins", "Inventory Manager"],
                template_context=context
            )
            
            notifications_sent += 1
            logger.info(f"Queued low stock alert for product {product.id} ({product.name}).")
        
        logger.info(f"Low stock check complete. Sent {notifications_sent} alerts.")
        
        return {
            'success': True,
            'alerts_sent': notifications_sent,
            'threshold': LOW_STOCK_THRESHOLD
        }
        
    except Exception as e:
        logger.error(f"Error in low stock check task: {str(e)}")
        raise

