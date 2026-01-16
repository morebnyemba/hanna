from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import WarrantyClaim, Warranty
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


@receiver(post_save, sender=Warranty)
def apply_warranty_rule(sender, instance, created, **kwargs):
    """
    Automatically apply warranty rule when a warranty is created.
    Only applies if end_date is not already set or matches start_date.
    """
    if created:
        from .services import WarrantyRuleService
        
        # Check if end_date needs to be calculated
        # Apply rule if end_date equals start_date (meaning it wasn't explicitly set)
        if instance.end_date == instance.start_date:
            try:
                rule, was_applied = WarrantyRuleService.apply_rule_to_warranty(instance)
                
                if was_applied:
                    logger.info(
                        f"Applied warranty rule '{rule.name}' to warranty {instance.id}. "
                        f"Duration: {rule.warranty_duration_days} days"
                    )
                else:
                    logger.warning(
                        f"No warranty rule found for product {instance.serialized_item.product.name} "
                        f"(ID: {instance.serialized_item.product.id})"
                    )
            except Exception as e:
                logger.error(f"Error applying warranty rule to warranty {instance.id}: {str(e)}")