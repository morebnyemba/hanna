from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import WarrantyClaim
from .tasks import send_manufacturer_notification_task
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=WarrantyClaim)
def trigger_manufacturer_notification(sender, instance: WarrantyClaim, created, **kwargs):
    """
    When a new WarrantyClaim is created, trigger a task to notify the manufacturer.
    """
    if created:
        log_prefix = f"[WarrantyClaim Signal for ID: {instance.id}]"
        logger.info(f"{log_prefix} New WarrantyClaim created. Checking for manufacturer email.")

        warranty = instance.warranty
        if not warranty:
            logger.warning(f"{log_prefix} Claim has no associated warranty. Cannot send notification.")
            return

        manufacturer_email = warranty.manufacturer_email

        if manufacturer_email:
            logger.info(f"{log_prefix} Manufacturer email '{manufacturer_email}' found. Scheduling notification task.")
            # Use transaction.on_commit to ensure the task runs only after the claim is saved.
            from django.db import transaction
            transaction.on_commit(
                lambda: send_manufacturer_notification_task.delay(
                    claim_id=str(instance.id),
                    manufacturer_email=manufacturer_email
                )
            )
        else:
            logger.info(f"{log_prefix} No manufacturer email on the associated warranty. Skipping notification.")