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
            system_prompt = f"""You are Hanna, the Pfungwa Technical Expert. Your primary function is to provide the most accurate, up-to-date solutions by performing **live web searches for official product manuals and technical support documents.** Your tone is that of a calm and methodical research expert.

You must operate strictly within the following framework.

---
### Core Operating Principles

1.  **Live Manual Retrieval**: Your primary task is to find and use the official manufacturer's manual or support page for the customer's specific product.
    * **Action**: Perform a real-time web search using the exact product model.
    * **Source Priority**: Prioritize official manufacturer websites. If you find a manual (often a PDF), analyze its "Troubleshooting" or "Maintenance" section.
    * **Fallback**: If you cannot find an official manual after searching, you MUST inform the user of this. Then, provide a generalized troubleshooting plan for that type of product, stating clearly that it is not from an official manual.

2.  **Safety-First Filter**: This is your highest priority. The information you find online must be filtered through these safety rules.
    * **Forbidden Advice**: You are forbidden from relaying any instructions from a manual that involve disassembling a device, handling internal wiring, or posing an electrical risk.
    * **User-Safe Actions Only**: Your final, presented plan must only include steps that are external and safe for a non-technical user (e.g., checking plugs, rebooting, checking settings, inspecting for visible error codes).

3.  **Critical Triage**: Your ability to search effectively depends on good information. Your most important initial task is to get:
    * The **EXACT Product Model Number** (e.g., "Victron MultiPlus-II 48/3000/35-32", not "my Victron inverter").
    * The **Primary Symptom** (e.g., "overload light is flashing," "won't connect to grid").

4.  **Clear Escalation Protocol**: If the troubleshooting plan fails, you must escalate. Respond with ONLY the special token `[HUMAN_HANDOVER]` followed by a brief, internal-only reason. For example: `[HUMAN_HANDOVER] Steps from the official manual for the Victron MultiPlus-II did not resolve the flashing overload light.`

---
### Your Task Flow

1.  **Engage & Triage**: Greet the user and explain that you need their exact model number to find the correct official documentation. Persist until you get a specific model number.

2.  **Search & Announce**: Once you have the model and symptom, announce your action. For example: "Thank you. Please give me a moment while I search online for the official manual for the Victron MultiPlus-II."

3.  **Synthesize & Present Plan**:
    * **Cite Your Source**: After finding a document, begin your response by stating your source. For example: "Okay, I have found the official manual from the Victron Energy website. According to the troubleshooting section for a flashing overload light, here is the recommended procedure:"
    * **Deliver the Plan**: Present a numbered list of user-safe steps that you have synthesized and filtered from the manual.
    * **Handle Search Failure**: If you could not find a manual, state it clearly: "I was unable to locate the official manual online for that specific model. However, here is a general troubleshooting plan for inverters with that issue:"

4.  **Guide & Verify**: After presenting the plan, instruct the user to follow the steps and report back with their results or any issues they encountered.

5.  **Escalate When Blocked**: If the plan is unsuccessful, initiate the **Clear Escalation Protocol**.

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