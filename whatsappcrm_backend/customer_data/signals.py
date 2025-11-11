# customer_data/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
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
                'id': instance.id,
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
            template_name='hanna_new_order_created',
            group_names=["System Admins", "Sales Team"],
            related_contact=instance.customer.contact if instance.customer else None,
            template_context=context
        )


@receiver([post_save, post_delete], sender=OrderItem)
def update_order_amount(sender, instance, **kwargs):
    """
    When an OrderItem is created, updated, or deleted,
    recalculate the total amount of the parent Order.
    """
    order = instance.order
    order.update_total_amount()
    order.save(update_fields=['amount'])


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