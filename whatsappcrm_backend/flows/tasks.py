# whatsappcrm_backend/flows/tasks.py
import logging
from celery import shared_task
from django.db import transaction

# --- Gemini AI Integration Imports ---
from google import genai
from google.api_core import exceptions as core_exceptions
from google.genai import errors as genai_errors
from ai_integration.models import AIProvider
# -------------------------------------

from conversations.models import Message, Contact
from meta_integration.models import MetaAppConfig
from meta_integration.tasks import send_whatsapp_message_task
from .services import process_message_for_flow, _clear_contact_flow_state

logger = logging.getLogger(__name__)

@shared_task(queue='celery') # Use your main I/O queue
def process_flow_for_message_task(message_id: int):
    """
    This task asynchronously runs the entire flow engine for an incoming message.
    """
    try:
        with transaction.atomic():
            incoming_message = Message.objects.select_related('contact', 'app_config').get(pk=message_id)
            contact = incoming_message.contact
            message_data = incoming_message.content_payload or {}

            actions_to_perform = process_message_for_flow(contact, message_data, incoming_message)

            if not actions_to_perform:
                logger.info(f"Flow processing for message {message_id} resulted in no actions.")
                return

            config_to_use = incoming_message.app_config
            if not config_to_use:
                logger.warning(f"Message {message_id} has no associated app_config. Falling back to active config.")
                config_to_use = MetaAppConfig.objects.get_active_config()

            dispatch_countdown = 0
            for action in actions_to_perform:
                if action.get('type') == 'send_whatsapp_message':
                    recipient_wa_id = action.get('recipient_wa_id', contact.whatsapp_id)
                    
                    recipient_contact, _ = Contact.objects.get_or_create(whatsapp_id=recipient_wa_id)

                    outgoing_msg = Message.objects.create(
                        contact=recipient_contact, app_config=config_to_use, direction='out',
                        message_type=action.get('message_type'), content_payload=action.get('data'),
                        status='pending_dispatch', related_incoming_message=incoming_message
                    )
                    send_whatsapp_message_task.apply_async(args=[outgoing_msg.id, config_to_use.id], countdown=dispatch_countdown)
                    dispatch_countdown += 2

    except Message.DoesNotExist:
        logger.error(f"process_flow_for_message_task: Message with ID {message_id} not found.")
    except Exception as e:
        logger.error(f"Critical error in process_flow_for_message_task for message {message_id}: {e}", exc_info=True)


@shared_task(
    name="flows.handle_ai_conversation_task",
    autoretry_for=(core_exceptions.ResourceExhausted, genai_errors.ServerError),
    retry_backoff=True, 
    retry_kwargs={'max_retries': 3}
)
def handle_ai_conversation_task(contact_id: int, message_id: int):
    """
    Manages an ongoing, multi-turn conversation with Gemini AI using the client.chats.create API.
    """
    log_prefix = f"[AI Conversation Task for Contact: {contact_id}]"
    logger.info(f"{log_prefix} Starting task for message ID: {message_id}")

    try:
        contact = Contact.objects.get(pk=contact_id)
        incoming_message = Message.objects.get(pk=message_id)
        active_provider = AIProvider.objects.get(provider='google_gemini', is_active=True)
        config_to_use = MetaAppConfig.objects.get_active_config()

        client = genai.Client(api_key=active_provider.api_key)

        system_prompt = "You are a helpful assistant."
        if contact.conversation_mode == 'ai_troubleshooting':
            system_prompt = f"""You are Hanna, an expert solar power installation and maintenance technician from Pfungwa. 
            Your goal is to have a natural conversation to help a customer solve their solar power issue. 
            Customer's Name: {contact.name or 'Valued Customer'}.
            
            Your Task:
            1. Ask clarifying questions to fully understand the problem.
            2. Provide clear, friendly, and safe step-by-step diagnostic advice.
            3. Use formatting like asterisks for bold (*word*), and numbered lists for steps.
            4. If the problem sounds complex, dangerous, or requires a professional, your primary goal is to guide the user to book a site assessment for their safety.
            5. IMPORTANT: If the user asks to stop, exit, or go back to the menu, you MUST respond with ONLY the special token [END_CONVERSATION] and nothing else."""

        history_messages = Message.objects.filter(contact=contact, timestamp__lte=incoming_message.timestamp).order_by('-timestamp')[:20]
        
        gemini_history = []
        # Inject the system prompt as the first message in the history for context
        gemini_history.append({'role': 'user', 'parts': [system_prompt]})
        gemini_history.append({'role': 'model', 'parts': ["Understood. I will act as Hanna, the solar expert. How can I help today?"]})

        for msg in reversed(history_messages):
            role = 'user' if msg.direction == 'in' else 'model'
            if msg.text_content:
                if msg.direction == 'in' and msg.text_content.lower().strip() in ['exit', 'menu', 'stop', 'quit']:
                    continue
                gemini_history.append({'role': role, 'parts': [msg.text_content]})

        chat = client.chats.create(
            model='models/gemini-1.5-flash', # Use the model identifier
            history=gemini_history
        )
        
        logger.info(f"{log_prefix} Sending message to Gemini chat model.")
        response = chat.send_message(incoming_message.text_content)

        ai_response_text = response.text.strip()

        if "[END_CONVERSATION]" in ai_response_text:
            logger.info(f"{log_prefix} AI requested to end conversation. The main service will handle resetting the mode.")
            final_reply = "I am now ending this session. Please type 'menu' to see other options."
        else:
            final_reply = ai_response_text

        outgoing_msg = Message.objects.create(
            contact=contact,
            app_config=config_to_use,
            direction='out',
            message_type='text',
            content_payload={'body': final_reply},
            status='pending_dispatch',
            related_incoming_message=incoming_message
        )
        send_whatsapp_message_task.delay(outgoing_msg.id, config_to_use.id)
        logger.info(f"{log_prefix} Successfully dispatched AI chat response to {contact.whatsapp_id}.")

    except Contact.DoesNotExist:
        logger.error(f"{log_prefix} Contact with ID {contact_id} not found.")
    except Message.DoesNotExist:
        logger.error(f"{log_prefix} Message with ID {message_id} not found.")
    except AIProvider.DoesNotExist:
        logger.error(f"{log_prefix} Active Gemini AI provider not configured.")
    except MetaAppConfig.DoesNotExist:
        logger.error(f"{log_prefix} Active Meta App Config not found. Cannot send reply.")
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred in AI conversation task: {e}", exc_info=True)
        raise