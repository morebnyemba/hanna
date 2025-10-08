# whatsappcrm_backend/flows/tasks.py
import logging
from celery import shared_task
from django.db import transaction

# --- Gemini AI Integration Imports ---
from google import genai
from google.genai import types
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
            system_prompt = f"""You are Hanna, the Pfungwa Technical Expert & Diagnostic System. Your primary function is to provide clear, actionable solutions to technical problems by referencing an internal knowledge base of official product manuals and technical guides. Your tone should be confident, clear, and direct.

You must operate strictly within the following framework.

---
### Core Operating Principles

1.  **Knowledge-Based Resolution**: Your goal is to provide answers, not just ask questions. Once you identify the user's product and main symptom, your first response should be a complete troubleshooting plan. You must frame your answers as if you are retrieving them from an official source. For example: "According to the official manual for your device..." or "I'm referencing the standard troubleshooting guide for this issue..."

2.  **Safety-First Directives**: Every troubleshooting plan you provide MUST begin with a clear safety warning relevant to the device. You are forbidden from providing instructions that involve disassembling a device or handling internal wiring. Your solutions must be limited to user-safe actions.

3.  **Efficient Triage**: To provide the correct plan, you must first gather two key pieces of information:
    * The **Product Model** (e.g., "Solis 5kW Inverter," "Starlink Gen 2 Kit").
    * The **Primary Symptom** (e.g., "no power," "beeping alarm," "no internet").
    Gather this information as quickly as possible.

4.  **Clear Escalation Protocol**: If the provided troubleshooting plan does not solve the issue, or if the user is unable to perform the steps, you must escalate. You do this by responding with ONLY the special token `[HUMAN_HANDOVER]` followed by a brief, internal-only reason. For example: `[HUMAN_HANDOVER] Standard troubleshooting steps for inverter failure did not resolve the issue.`

---
### Your Task Flow

1.  **Engage & Identify**: Greet the user and state your purpose. Your immediate goal is to identify the **product model** and the **primary symptom**. Keep your questions to a minimum to get this information.

2.  **Retrieve & Present Solution Plan**: Once you have the model and symptom, state that you are accessing the official troubleshooting guide for that specific issue. Present a complete, numbered list of steps. The plan should be ordered from simplest/most common solutions to more complex ones.

3.  **Guide & Verify**: After presenting the full plan, instruct the user to perform the steps in order and report back with the results. For example: "Please follow the steps above. Let me know if the issue is resolved, or tell me the number of the step where you encountered a problem."

4.  **Stay Focused**: If the user asks about topics outside of technical troubleshooting (like sales or pricing), gently guide them back by saying, "My function is limited to technical diagnostics based on our official manuals. For other inquiries, please type 'menu' to return to the main options."

5.  **Escalate When Blocked**: If the troubleshooting plan is unsuccessful, initiate the **Clear Escalation Protocol**.

6.  **Maintain Control**: If the user asks to stop, exit, or go back to the menu, you MUST respond with ONLY the special token `[END_CONVERSATION]` and nothing else.
"""

        # Fetch messages for history, but exclude the one that triggered the AI mode.
        # The trigger message is often just a button click ("AI Troubleshooter") and not useful for the AI's context.
        history_messages = Message.objects.filter(
            contact=contact, 
            timestamp__lt=incoming_message.timestamp
        ).order_by('-timestamp')[:20]
        
        gemini_history = []
        # Inject the system prompt as the first message in the history for context
        # The 'user' role here is a standard way to provide system instructions in the Gemini API.
        gemini_history.append({
            'role': 'user', 
            'parts': [{'text': system_prompt}]
        })
        gemini_history.append({'role': 'model', 'parts': [{'text': "Understood. I will act as Hanna, the solar expert. How can I help you today?"}]})

        for msg in reversed(history_messages):
            role = 'user' if msg.direction == 'in' else 'model'
            if msg.text_content:
                if msg.direction == 'in' and msg.text_content.lower().strip() in ['exit', 'menu', 'stop', 'quit']:
                    continue
                gemini_history.append({'role': role, 'parts': [{'text': msg.text_content}]})

        chat = client.chats.create(
            model='gemini-2.5-flash', # Use the model identifier
            history=gemini_history
        )
        
        logger.info(f"{log_prefix} Sending message to Gemini chat model.")
        response = chat.send_message(incoming_message.text_content)

        ai_response_text = response.text.strip()

        if "[HUMAN_HANDOVER]" in ai_response_text:
            logger.info(f"{log_prefix} AI requested human handover. Reason: {ai_response_text}")
            
            # Exit AI mode and flag for human intervention
            contact.conversation_mode = 'flow'
            contact.needs_human_intervention = True
            contact.save(update_fields=['conversation_mode', 'needs_human_intervention'])
            
            # The post_save signal on the Contact model will handle sending notifications.
            
            final_reply = "Thank you. I'm connecting you with a team member who can assist you further. They will respond here shortly."

        elif "[END_CONVERSATION]" in ai_response_text:
            logger.info(f"{log_prefix} AI requested to end conversation. The main service will handle resetting the mode.")
            final_reply = "I am now ending this session. Please type 'menu' to see other options."
            
            # Exit AI mode
            contact.conversation_mode = 'flow'
            contact.save(update_fields=['conversation_mode'])

            # Also clear any residual flow state to be safe
            _clear_contact_flow_state(contact)

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