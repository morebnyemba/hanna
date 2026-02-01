import logging
from django.dispatch import receiver
from django.utils import timezone
from meta_integration.signals import message_send_failed
from .services import queue_notifications_to_users

logger = logging.getLogger(__name__)

@receiver(message_send_failed)
def handle_failed_message_notification(sender, message_instance, **kwargs):
    """
    Listens for the message_send_failed signal and queues a notification
    to the admin team.
    """
    try:
        contact = message_instance.contact
        logger.info(
            f"Signal received: Message send failed for contact '{contact.name}' ({contact.whatsapp_id}). "
            f"Queuing admin notification."
        )

        queue_notifications_to_users(
            template_name='pfungwa_message_send_failure',
            group_names=["Technical Admin"],
            related_contact=contact,
            template_context={
                'message_id': message_instance.id,
                'message_body': message_instance.message_body[:100] if message_instance.message_body else 'N/A',
                'contact_name': contact.name or contact.whatsapp_id,
                'contact_whatsapp_id': contact.whatsapp_id,
                'error_details': kwargs.get('error', 'Unknown error'),
                'error_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        )
    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to queue notification for failed message {message_instance.id}. Error: {e}",
            exc_info=True
        )