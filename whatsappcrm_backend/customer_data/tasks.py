# whatsappcrm_backend/customer_data/tasks.py

"""
Celery tasks for customer_data app.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(queue='celery')
def send_payment_reminders():
    """
    Send payment reminder notifications for orders with pending payments.
    Sends reminders for orders that are:
    - In PENDING payment status
    - Stage is CLOSED_WON (order was won but not yet paid)
    - Created more than 3 days ago
    
    Should be run daily via Celery Beat.
    """
    from .models import Order
    from notifications.services import queue_notifications_to_users
    
    logger.info("Starting payment reminder task")
    
    try:
        # Calculate cutoff date (3 days ago)
        cutoff_date = timezone.now() - timedelta(days=3)
        
        # Find orders with pending payment older than 3 days
        pending_orders = Order.objects.filter(
            payment_status=Order.PaymentStatus.PENDING,
            stage=Order.Stage.CLOSED_WON,
            created_at__lte=cutoff_date
        ).select_related('customer').exclude(
            customer__isnull=True
        )
        
        reminders_sent = 0
        
        for order in pending_orders:
            customer_contact = order.customer.contact if hasattr(order.customer, 'contact') else None
            
            if customer_contact:
                # Calculate days overdue
                days_pending = (timezone.now() - order.created_at).days
                
                context = {
                    'customer_name': order.customer.get_full_name(),
                    'order_number': order.order_number or str(order.id),
                    'order_amount': str(order.amount) if order.amount else '0.00',
                    'days_pending': str(days_pending),
                }
                
                queue_notifications_to_users(
                    template_name='pfungwa_payment_reminder',
                    contact_ids=[customer_contact.id],
                    related_contact=customer_contact,
                    template_context=context
                )
                
                reminders_sent += 1
                logger.info(f"Queued payment reminder for order {order.id} ({days_pending} days pending).")
        
        logger.info(f"Payment reminders complete. Sent {reminders_sent} reminders.")
        
        return {
            'success': True,
            'reminders_sent': reminders_sent
        }
        
    except Exception as e:
        logger.error(f"Error in payment reminder task: {str(e)}")
        raise
