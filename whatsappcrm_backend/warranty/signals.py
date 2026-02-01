from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.db import transaction
from .models import WarrantyClaim, Warranty
from .tasks import send_manufacturer_notification_task
from notifications.services import queue_notifications_to_users
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=WarrantyClaim)
def trigger_manufacturer_notification(sender, instance: WarrantyClaim, created, **kwargs):
    """
    When a new WarrantyClaim is created, trigger a task to notify the manufacturer
    and send notifications to customer and admin.
    """
    if created:
        log_prefix = f"[WarrantyClaim Signal for ID: {instance.id}]"
        logger.info(f"{log_prefix} New WarrantyClaim created. Checking for manufacturer email.")

        warranty = instance.warranty
        if not warranty:
            logger.warning(f"{log_prefix} Claim has no associated warranty. Cannot send notification.")
            return

        # Send notification to customer that claim was submitted
        customer_contact = warranty.customer.contact if warranty.customer and hasattr(warranty.customer, 'contact') else None
        if customer_contact:
            context = {
                'customer_name': warranty.customer.get_full_name() if warranty.customer else 'Customer',
                'claim_number': instance.claim_id,
                'product_name': warranty.serialized_item.product.name if warranty.serialized_item else 'Product',
                'reported_issue': instance.description_of_fault,
            }
            transaction.on_commit(
                lambda: queue_notifications_to_users(
                    template_name='pfungwa_warranty_claim_submitted',
                    contact_ids=[customer_contact.id],
                    related_contact=customer_contact,
                    template_context=context
                )
            )
            logger.info(f"{log_prefix} Queued customer notification for warranty claim submission.")

        manufacturer_email = warranty.manufacturer_email

        if manufacturer_email:
            logger.info(f"{log_prefix} Manufacturer email '{manufacturer_email}' found. Scheduling notification task.")
            # Use transaction.on_commit to ensure the task runs only after the claim is saved.
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
    Also sends notification to customer when warranty is registered.
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
        
        # Send warranty registration notification to customer
        customer_contact = instance.customer.contact if instance.customer and hasattr(instance.customer, 'contact') else None
        if customer_contact:
            context = {
                'customer_name': instance.customer.get_full_name() if instance.customer else 'Customer',
                'product_name': instance.serialized_item.product.name if instance.serialized_item else 'Product',
                'serial_number': instance.serialized_item.serial_number if instance.serialized_item else 'N/A',
                'warranty_end_date': instance.end_date.strftime('%Y-%m-%d') if instance.end_date else 'N/A',
            }
            transaction.on_commit(
                lambda: queue_notifications_to_users(
                    template_name='pfungwa_warranty_registered',
                    contact_ids=[customer_contact.id],
                    related_contact=customer_contact,
                    template_context=context
                )
            )
            logger.info(f"Queued warranty registration notification for customer {customer_contact.id}.")


@receiver(post_save, sender=WarrantyClaim)
def notify_warranty_claim_status_change(sender, instance: WarrantyClaim, created, **kwargs):
    """
    Send notification to customer when warranty claim status changes to approved.
    """
    if not created and instance.status == WarrantyClaim.ClaimStatus.APPROVED:
        log_prefix = f"[WarrantyClaim Signal for ID: {instance.id}]"
        logger.info(f"{log_prefix} Warranty claim approved. Sending notification to customer.")
        
        warranty = instance.warranty
        if not warranty:
            logger.warning(f"{log_prefix} Claim has no associated warranty. Cannot send notification.")
            return
        
        customer_contact = warranty.customer.contact if warranty.customer and hasattr(warranty.customer, 'contact') else None
        if customer_contact:
            context = {
                'customer_name': warranty.customer.get_full_name() if warranty.customer else 'Customer',
                'claim_number': instance.claim_id,
                'resolution_type': instance.get_status_display(),
                'resolution_notes_section': f"*Notes:*\n{instance.resolution_notes}\n" if instance.resolution_notes else '',
            }
            transaction.on_commit(
                lambda: queue_notifications_to_users(
                    template_name='pfungwa_warranty_claim_approved',
                    contact_ids=[customer_contact.id],
                    related_contact=customer_contact,
                    template_context=context
                )
            )
            logger.info(f"{log_prefix} Queued warranty claim approval notification for customer {customer_contact.id}.")