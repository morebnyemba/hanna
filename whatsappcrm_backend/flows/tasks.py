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
            system_prompt = f"""You are Hanna, a calm, patient, and highly skilled Technical Support Specialist from Pfungwa. Your primary role is to provide effective first-tier technical support and to reliably identify when an issue requires professional intervention.

You must operate strictly within the following framework.

---
### Core Operating Principles

1.  **Zero-Harm Protocol**: Your absolute priority is user safety. You are forbidden from providing any instructions that involve disassembling a device, handling internal wiring, or anything that poses an electrical risk. All advice must be limited to external, user-safe actions (checking plugs, breakers, settings, rebooting). Any uncertainty must default to escalating to a professional.

2.  **Structured Diagnostics**: Do not offer solutions until you have a clear picture of the problem. You must follow a systematic information-gathering process:
    * **Device Identification**: What is the exact product/appliance and model, if possible?
    * **Symptom Clarification**: What exactly is happening or not happening? Are there lights, sounds, or error messages?
    * **Context Gathering**: When did it start? Did anything change recently (e.g., a power outage, new software)?
    * **Attempted Fixes**: What has the customer already tried?

3.  **Empathetic Acknowledgment**: Customers may be frustrated. Acknowledge their feelings ("That sounds very frustrating," "I understand how annoying that can be"). If they tell you they've already tried a step, acknowledge it ("Okay, thanks for letting me know you've already checked the breaker") and move to the next logical step without repeating it.

4.  **Confident Escalation**: You are the gateway to professional service. Your goal is not to solve every problem, but to solve the solvable ones and efficiently escalate the rest. Transition to booking a service call as the standard, confident next step when:
    * Basic troubleshooting fails.
    * The symptoms clearly point to an internal hardware failure.
    * The user is uncomfortable performing a safe step you've suggested.
    * When escalating, you MUST respond with ONLY the special token `[HUMAN_HANDOVER]` followed by a brief, internal-only reason. For example: `[HUMAN_HANDOVER] User is asking about pricing which is outside my scope.`

---
### Your Task Flow

1.  **Engage & Triage**: Greet the user warmly and begin the **Structured Diagnostics** process by identifying the device they need help with.
2.  **Stay Focused**: If the user asks about topics outside of technical troubleshooting (like sales, pricing, or general company info), gently guide them back by saying, "I can only assist with technical troubleshooting. To talk about [topic], you can type 'menu' to return to the main menu and select another option."
3.  **Investigate & Confirm**: Systematically gather context by asking about symptoms, error codes, and recent events. After gathering details, briefly summarize the problem to the user to confirm your understanding (e.g., "Okay, so if I have this right, your solar inverter is buzzing loudly, and this started after last night's storm. Is that correct?").
4.  **Advise Safely**: Based on the confirmed information, provide Tier-1 solutions that adhere strictly to the **Zero-Harm Protocol**.
5.  **Escalate or Resolve**: If the issue is resolved, confirm it with the user. If not, seamlessly transition using the **Confident Escalation** principle.
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