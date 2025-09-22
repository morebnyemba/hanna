# whatsappcrm_backend/flows/tasks.py
import logging
from celery import shared_task
from django.db import transaction

from conversations.models import Message, Contact
from meta_integration.models import MetaAppConfig
from meta_integration.tasks import send_whatsapp_message_task
from .services import process_message_for_flow

logger = logging.getLogger(__name__)

@shared_task(queue='celery') # Use your main I/O queue
def process_flow_for_message_task(message_id: int):
    """
    This task asynchronously runs the entire flow engine for an incoming message.
    """
    try:
        # Use a transaction to ensure atomicity of reading state and taking action
        with transaction.atomic():
            incoming_message = Message.objects.select_related('contact', 'app_config').get(pk=message_id)
            contact = incoming_message.contact
            message_data = incoming_message.content_payload or {}

            # Run the main flow engine
            actions_to_perform = process_message_for_flow(contact, message_data, incoming_message)

            if not actions_to_perform:
                logger.info(f"Flow processing for message {message_id} resulted in no actions.")
                return

            # Use the config from the incoming message to ensure replies are sent from the correct number.
            # Fallback to the globally active config if the message isn't linked to one.
            config_to_use = incoming_message.app_config
            if not config_to_use:
                logger.warning(f"Message {message_id} has no associated app_config. Falling back to active config.")
                config_to_use = MetaAppConfig.objects.get_active_config()

            # Process the actions returned by the flow engine
            dispatch_countdown = 0
            for action in actions_to_perform:
                if action.get('type') == 'send_whatsapp_message':
                    recipient_wa_id = action.get('recipient_wa_id', contact.whatsapp_id)
                    
                    if recipient_wa_id == contact.whatsapp_id:
                        recipient_contact = contact
                    else:
                        recipient_contact, _ = Contact.objects.get_or_create(whatsapp_id=recipient_wa_id)

                    outgoing_msg = Message.objects.create(
                        contact=recipient_contact, app_config=config_to_use, direction='out',
                        message_type=action.get('message_type'), content_payload=action.get('data'),
                        status='pending_dispatch', related_incoming_message=incoming_message
                    )
                    send_whatsapp_message_task.apply_async(args=[outgoing_msg.id, config_to_use.id], countdown=dispatch_countdown)
                    dispatch_countdown += 2 # Stagger subsequent messages by 2 seconds

    except Message.DoesNotExist:
        logger.error(f"process_flow_for_message_task: Message with ID {message_id} not found.")
    except Exception as e:
        logger.error(f"Critical error in process_flow_for_message_task for message {message_id}: {e}", exc_info=True)