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
