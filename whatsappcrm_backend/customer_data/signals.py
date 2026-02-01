# customer_data/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Order, OrderItem

from warranty.models import Warranty
from dateutil.relativedelta import relativedelta
from django.utils import timezone
import logging

from notifications.services import queue_notifications_to_users

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def on_new_order_created(sender, instance, created, **kwargs):
    """
    When a new Order is created, send a notification to the admin group.
    """
    if created:
        logger.info(f"New order created (ID: {instance.id}), queueing admin notification.")
        
        # Construct a serializable context dictionary
        context = {
            'order': {
                'id': str(instance.id),  # Convert UUID to string for JSON serialization
                'name': instance.name,
                'order_number': instance.order_number,
                'amount': float(instance.amount) if instance.amount is not None else 0.0,
                'customer': {
                    'get_full_name': instance.customer.get_full_name() if instance.customer else '',
                    'contact': {
                        'name': instance.customer.contact.name if instance.customer and instance.customer.contact else ''
                    }
                }
            }
        }
        
        queue_notifications_to_users(
            template_name='pfungwa_new_order_created',
            group_names=["System Admins", "Sales Team"],
            related_contact=instance.customer.contact if instance.customer else None,
            template_context=context
        )


@receiver(post_save, sender=Order)
def send_payment_notifications(sender, instance: Order, created, **kwargs):
    """
    Send notifications to customer when payment status changes.
    """
    if not created:
        # Check if payment_status changed to 'paid'
        if instance.payment_status == Order.PaymentStatus.PAID:
            customer_contact = instance.customer.contact if instance.customer and hasattr(instance.customer, 'contact') else None
            if customer_contact:
                context = {
                    'customer_name': instance.customer.get_full_name() if instance.customer else 'Customer',
                    'order_number': instance.order_number or str(instance.id),
                    'order_amount': str(instance.amount) if instance.amount else '0.00',
                    'payment_method': instance.get_payment_method_display() if instance.payment_method else 'N/A',
                }
                transaction.on_commit(
                    lambda: queue_notifications_to_users(
                        template_name='pfungwa_payment_received',
                        contact_ids=[customer_contact.id],
                        related_contact=customer_contact,
                        template_context=context
                    )
                )
                logger.info(f"Queued payment received notification for order {instance.id}.")


@receiver(post_save, sender=Order)
def send_order_confirmation(sender, instance: Order, created, **kwargs):
    """
    Send order confirmation to customer when order stage changes to closed_won.
    """
    if not created and instance.stage == Order.Stage.CLOSED_WON:
        customer_contact = instance.customer.contact if instance.customer and hasattr(instance.customer, 'contact') else None
        if customer_contact:
            # Build cart items list
            items_list = []
            for item in instance.items.all():
                product_name = item.product.name if item.product else (item.product_name or 'Unknown Product')
                items_list.append(f"- {item.quantity} x {product_name}")
            cart_items_list = '\n'.join(items_list) if items_list else '(No items)'
            
            context = {
                'customer_name': instance.customer.get_full_name() if instance.customer else 'Customer',
                'order_number': instance.order_number or str(instance.id),
                'order_amount': str(instance.amount) if instance.amount else '0.00',
                'cart_items_list': cart_items_list,
            }
            transaction.on_commit(
                lambda: queue_notifications_to_users(
                    template_name='pfungwa_order_confirmation',
                    contact_ids=[customer_contact.id],
                    related_contact=customer_contact,
                    template_context=context
                )
            )
            logger.info(f"Queued order confirmation notification for order {instance.id}.")


@receiver([post_save, post_delete], sender=OrderItem)
def update_order_amount(sender, instance, **kwargs):
    """
    When an OrderItem is created, updated, or deleted,
    recalculate the total amount of the parent Order.
    """
    order = instance.order
    order.update_total_amount()
    order.save(update_fields=['amount'])


@receiver(post_save, sender='customer_data.JobCard')
def send_job_card_notifications(sender, instance, created, **kwargs):
    """
    Send notifications when job card is created or status changes.
    """
    if created:
        # Notify customer that job card was created
        customer_contact = instance.customer.contact if instance.customer and hasattr(instance.customer, 'contact') else None
        if customer_contact:
            context = {
                'customer_name': instance.customer.get_full_name() if instance.customer else 'Customer',
                'job_card_number': instance.job_card_number,
                'product_description': instance.serialized_item.product.name if instance.serialized_item else 'Product',
                'reported_fault': instance.reported_fault or 'Not specified',
            }
            transaction.on_commit(
                lambda: queue_notifications_to_users(
                    template_name='pfungwa_job_card_created',
                    contact_ids=[customer_contact.id],
                    related_contact=customer_contact,
                    template_context=context
                )
            )
            logger.info(f"Queued job card creation notification for customer {customer_contact.id}.")
    
    elif instance.status in ['resolved', 'closed']:
        # Notify customer that job is completed
        customer_contact = instance.customer.contact if instance.customer and hasattr(instance.customer, 'contact') else None
        if customer_contact:
            # Get resolution notes from warranty claim if available
            resolution_notes = ''
            if instance.warranty_claim and instance.warranty_claim.resolution_notes:
                resolution_notes = f"*Resolution:*\n{instance.warranty_claim.resolution_notes}\n"
            
            context = {
                'customer_name': instance.customer.get_full_name() if instance.customer else 'Customer',
                'job_card_number': instance.job_card_number,
                'resolution_notes_section': resolution_notes,
            }
            transaction.on_commit(
                lambda: queue_notifications_to_users(
                    template_name='pfungwa_job_card_completed',
                    contact_ids=[customer_contact.id],
                    related_contact=customer_contact,
                    template_context=context
                )
            )
            logger.info(f"Queued job card completion notification for customer {customer_contact.id}.")


@receiver(post_save, sender='customer_data.InstallationRequest')
def send_installation_scheduled_notification(sender, instance, created, **kwargs):
    """
    Send notification when installation request status changes to scheduled.
    """
    if not created and instance.status == 'scheduled':
        customer_contact = instance.customer.contact if instance.customer and hasattr(instance.customer, 'contact') else None
        if customer_contact:
            # Get assigned technician name
            technician = instance.technicians.first()
            technician_name = technician.user.get_full_name() if technician else 'To be assigned'
            
            # Format preferred_datetime properly
            if instance.preferred_datetime:
                # Try to parse if it's a string, otherwise use as-is
                try:
                    from datetime import datetime
                    if isinstance(instance.preferred_datetime, str):
                        # Assuming format like "2024-01-15 14:00" or similar
                        installation_date = instance.preferred_datetime
                    else:
                        installation_date = instance.preferred_datetime.strftime('%Y-%m-%d %H:%M')
                except Exception:
                    installation_date = str(instance.preferred_datetime)
            else:
                installation_date = 'To be confirmed'
            
            context = {
                'customer_name': instance.customer.get_full_name() if instance.customer else 'Customer',
                'installation_address': instance.address or 'Address not specified',
                'installation_date': installation_date,
                'installation_time': '',  # Time is usually part of preferred_datetime
                'technician_name': technician_name,
            }
            transaction.on_commit(
                lambda: queue_notifications_to_users(
                    template_name='pfungwa_installation_scheduled',
                    contact_ids=[customer_contact.id],
                    related_contact=customer_contact,
                    template_context=context
                )
            )
            logger.info(f"Queued installation scheduled notification for customer {customer_contact.id}.")


@receiver(post_save, sender=Order)
def create_warranties_on_paid_order(sender, instance: Order, created, **kwargs):
    """
    When an Order's payment_status is updated to 'paid', automatically create
    Warranty records for eligible products in the order.
    """
    # We only care about updates, not creation, and only when status is 'paid'.
    if not created and instance.payment_status == Order.PaymentStatus.PAID:
        log_prefix = f"[Order Signal for ID: {instance.id}]"
        logger.info(f"{log_prefix} Order marked as paid. Checking for items to create warranties for.")

        # Corrected Filter: Find hardware products that have a manufacturer.
        order_items = instance.items.select_related('product').filter(
            product__product_type='hardware', 
            product__manufacturer__isnull=False
        )

        for item in order_items:
            # For simplicity, we assume one serial number per quantity.
            # A more complex system might need a way to input multiple serials.
            for i in range(item.quantity):
                # The flawed `exists()` check is removed. We will create a warranty for each unit.
                # The generated serial number ensures uniqueness for each item.
                start_date = timezone.now().date()
                # Corrected: Use a default 12-month warranty as the duration is not stored on the product model.
                end_date = start_date + relativedelta(months=12)

                # This is a placeholder. In a real system, you'd need a mechanism
                # to get and assign unique serial numbers for each unit.
                serial_number = f"GEN-{instance.order_number}-{item.product.sku}-{i+1}"

                Warranty.objects.create(
                    product=item.product,
                    customer=instance.customer,
                    associated_order=instance,
                    product_serial_number=serial_number,
                    start_date=start_date,
                    end_date=end_date,
                    status=Warranty.WarrantyStatus.ACTIVE
                )
                logger.info(f"{log_prefix} Created Warranty for {item.product.name} (SN: {serial_number}).")