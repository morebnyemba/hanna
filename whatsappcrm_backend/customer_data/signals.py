# customer_data/signals.py
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order, OrderItem

@receiver([post_save, post_delete], sender=OrderItem)
def update_order_amount(sender, instance, **kwargs):
    """
    Updates the total amount of an Order whenever an OrderItem
    associated with it is saved or deleted.
    """
    order = instance.order
    
    # Calculate the new total by summing the (quantity * unit_price) for all related items.
    # This is done efficiently in the database.
    new_total = order.items.aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField()))
    )['total'] or 0.00
    
    # Update the order's amount field only if it has changed.
    Order.objects.filter(pk=order.pk).update(amount=new_total)