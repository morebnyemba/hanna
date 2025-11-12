import logging
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.db import transaction
from django.db.models import Q

from .models import Notification, NotificationTemplate
from .tasks import dispatch_notification_task
from conversations.models import Contact, Message
from flows.models import Flow
from .utils import render_template_string # Import the new render utility
from meta_integration.tasks import send_whatsapp_message_task
from meta_integration.models import MetaAppConfig

logger = logging.getLogger(__name__)
User = get_user_model()

def serialize_contact_for_template(contact: Contact) -> dict:
    """
    Serializes a Contact model instance into a dictionary for use in template rendering.
    Includes nested customer_profile data if available.
    """
    contact_data = {
        'id': contact.id,
        'whatsapp_id': contact.whatsapp_id,
        'name': contact.name or '',
    }
    
    # Add customer profile data if available
    if hasattr(contact, 'customer_profile') and contact.customer_profile:
        profile = contact.customer_profile
        contact_data['customer_profile'] = {
            'first_name': profile.first_name or '',
            'last_name': profile.last_name or '',
            'email': profile.email or '',
            'company': profile.company or '',
            'lead_status': profile.lead_status or '',
        }
        # Helper method to get full name
        contact_data['customer_profile']['get_full_name'] = f"{profile.first_name or ''} {profile.last_name or ''}".strip()
    
    return contact_data

def serialize_flow_for_template(flow: Flow) -> dict:
    """
    Serializes a Flow model instance into a dictionary for use in template rendering.
    """
    return {
        'id': flow.id,
        'name': flow.name,
        'trigger': flow.trigger if hasattr(flow, 'trigger') else '',
    }

def queue_notifications_to_users(
    template_name: str,
    template_context: Optional[dict] = None,
    user_ids: Optional[List[int]] = None,
    group_names: Optional[List[str]] = None,
    contact_ids: Optional[List[int]] = None,
    related_contact: Optional[Contact] = None,
    related_flow: Optional[Flow] = None,
):
    """
    Queues notifications for internal users and/or external contacts.
    - For internal users (by user_ids or group_names), it creates a Notification record
      and dispatches a task to send it.
    - For external contacts (by contact_ids), it creates a Message record and dispatches
      a task to send it via WhatsApp.
    """
    if not template_name:
        logger.error("queue_notifications_to_users called without a 'template_name'.")
        return

    if not user_ids and not group_names and not contact_ids:
        logger.warning("queue_notifications_to_users called without any target recipients (user_ids, group_names, or contact_ids).")
        return

    if template_name:
        try:
            from customer_data.models import CustomerProfile, Order # Local import to avoid circular dependency
            template = NotificationTemplate.objects.get(name=template_name)
            # Build the context for rendering. Start with a copy of the provided context.
            render_context = (template_context or {}).copy()

            # Add related objects to the context, ensuring they are serializable if they are models.
            # This is crucial because the context will be saved to a JSONField.
            if related_contact:
                render_context['contact'] = serialize_contact_for_template(related_contact)
            if related_flow:
                render_context['flow'] = serialize_flow_for_template(related_flow)
            
            final_message_body = render_template_string(template.message_body, render_context)
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template '{template_name}' not found. Cannot queue notifications.")
            return

    if not final_message_body or not final_message_body.strip():
        logger.warning(f"queue_notifications_to_users for template '{template_name}' resulted in an empty message body. Skipping.")
        return

    # --- Case 1: Notify internal staff users ---
    if user_ids or group_names:
        query = Q()
        if user_ids:
            query |= Q(id__in=user_ids)
        if group_names:
            query |= Q(groups__name__in=group_names)

        all_potential_users = User.objects.filter(query, is_active=True).distinct()

        if all_potential_users.exists():
            notifications_to_create = [
                Notification(
                    recipient=user, 
                    channel='whatsapp', 
                    status='pending', 
                    content=final_message_body, 
                    related_contact=related_contact, 
                    related_flow=related_flow,
                    template_name=template_name, template_context=render_context) # Use the cleaned render_context
                for user in all_potential_users
            ]

            created_notifications = Notification.objects.bulk_create(notifications_to_create)
            logger.info(f"Bulk created {len(created_notifications)} internal notifications for template '{template_name}'.")

            for notification in created_notifications:
                transaction.on_commit(lambda n=notification: dispatch_notification_task.delay(n.id))
                logger.info(f"Notifications: Queued Notification ID {notification.id} for user '{notification.recipient.username}'.")
        else:
            logger.info(f"No active internal users found for user_ids {user_ids} or group_names {group_names}.")

    # --- Case 2: Notify external contacts directly via WhatsApp ---
    if contact_ids:
        try:
            active_config = MetaAppConfig.objects.get_active_config()
        except MetaAppConfig.DoesNotExist:
            logger.error(f"Cannot send WhatsApp notification for template '{template_name}': No active MetaAppConfig found.")
            return
            
        recipient_contacts = Contact.objects.filter(id__in=contact_ids)
        for recipient_contact in recipient_contacts:
            message_type = 'text'
            content_payload = {'body': final_message_body}
            
            # If the template has buttons or body/url parameters, we must send a template message
            if (hasattr(template, 'buttons') and template.buttons) or \
               (hasattr(template, 'body_parameters') and template.body_parameters) or \
               (hasattr(template, 'url_parameters') and template.url_parameters):
                message_type = 'template'
                template_components = []

                # --- Handle BODY parameters ---
                if hasattr(template, 'body_parameters') and template.body_parameters:
                    body_params_list = []
                    # Sort by the integer value of the key (e.g., '1', '2')
                    sorted_body_params = sorted(template.body_parameters.items(), key=lambda item: int(item[0]))
                    
                    for index, jinja_var_path in sorted_body_params:
                        try:
                            param_value = render_template_string(f"{{{{ {jinja_var_path} }}}}", render_context)
                            body_params_list.append({"type": "text", "text": str(param_value)})
                        except Exception as e:
                            logger.error(f"Error rendering body parameter '{jinja_var_path}' for template '{template_name}': {e}")
                            body_params_list.append({"type": "text", "text": ""}) # Fallback

                    if body_params_list:
                        template_components.append({
                            "type": "BODY",
                            "parameters": body_params_list
                        })

                # --- Handle BUTTONS (including URL parameters) ---
                if hasattr(template, 'buttons') and template.buttons:
                    url_button_params_list = []
                    if hasattr(template, 'url_parameters') and template.url_parameters:
                        # Sort by the integer value of the key (e.g., '1', '2')
                        sorted_url_params = sorted(template.url_parameters.items(), key=lambda item: int(item[0]))

                        for index, jinja_var_path in sorted_url_params:
                            try:
                                param_value = render_template_string(f"{{{{ {jinja_var_path} }}}}", render_context)
                                url_button_params_list.append({"type": "text", "text": str(param_value)})
                            except Exception as e:
                                logger.error(f"Error rendering URL parameter '{jinja_var_path}' for template '{template_name}': {e}")
                                url_button_params_list.append({"type": "text", "text": ""}) # Fallback

                    if url_button_params_list:
                        url_button_index = -1
                        for i, button_def in enumerate(template.buttons):
                            if isinstance(button_def, dict) and button_def.get("type") == "URL":
                                url_button_index = i
                                break
                        
                        if url_button_index != -1:
                            template_components.append({
                                "type": "BUTTON",
                                "sub_type": "url",
                                "index": str(url_button_index),
                                "parameters": url_button_params_list
                            })
                
                content_payload = {
                    "name": template_name,
                    "language": { "code": "en_US" },
                    "components": template_components
                }

            outgoing_msg = Message.objects.create(
                contact=recipient_contact, 
                app_config=active_config, 
                direction='out', 
                message_type=message_type,
                content_payload=content_payload, 
                status='pending_dispatch', 
                related_flow=related_flow
            )
            send_whatsapp_message_task.delay(outgoing_msg.id, active_config.id)
            logger.info(f"Queued direct WhatsApp notification for template '{template_name}' to contact {recipient_contact.id} ({recipient_contact.whatsapp_id}).")