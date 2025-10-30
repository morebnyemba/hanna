# customer_data/signals.py
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order, OrderItem

# --- NEW IMPORTS ---
from .models import Order
from warranty.models import Warranty
from notifications.services import queue_notifications_to_users
from dateutil.relativedelta import relativedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
# --- END NEW IMPORTS ---

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_amount(sender, instance, **kwargs):
    pass


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

        # Eagerly load related product and warranty info
        order_items = instance.items.select_related('product').filter(product__warranty_duration_months__gt=0)

        for item in order_items:
            # For simplicity, we assume one serial number per quantity.
            # A more complex system might need a way to input multiple serials.
            for i in range(item.quantity):
                # Check if a warranty for this order item already exists to prevent duplicates
                # This simple check uses the order and product. A real-world scenario might need serial numbers.
                if not Warranty.objects.filter(associated_order=instance, product=item.product).exists():
                    start_date = timezone.now().date()
                    end_date = start_date + relativedelta(months=item.product.warranty_duration_months)

                    # This is a placeholder. In a real system, you'd need a mechanism
                    # to get and assign unique serial numbers for each unit.
                    serial_number = f"GEN-{instance.order_number}-{item.product.sku}-{i+1}"

                    warranty = Warranty.objects.create(
                        product=item.product,
                        customer=instance.customer,
                        associated_order=instance,
                        product_serial_number=serial_number,
                        start_date=start_date,
                        end_date=end_date,
                        status=Warranty.WarrantyStatus.ACTIVE
                    )
                    logger.info(f"{log_prefix} Created Warranty for {item.product.name} (SN: {serial_number}).")