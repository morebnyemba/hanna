import logging
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from django.db import transaction
from django.db.models import Q
from django.conf import settings

from .models import Notification, NotificationTemplate
from .tasks import dispatch_notification_task
from conversations.models import Contact, Message
from flows.models import Flow
from .utils import render_template_string, get_versioned_template_name
from meta_integration.tasks import send_whatsapp_message_task
from meta_integration.models import MetaAppConfig

logger = logging.getLogger(__name__)
User = get_user_model()

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

            # Flatten nested variables for Meta-compatible templates
            # Contact name
            if related_contact:
                render_context['contact'] = str(related_contact) # Convert model to string
                # Add contact_name for templates that need it
                render_context['contact_name'] = related_contact.name or related_contact.whatsapp_id
                # Add related_contact_name for templates that need it
                render_context['related_contact_name'] = related_contact.name or related_contact.whatsapp_id
                if hasattr(related_contact, 'customer_profile'):
                    # Assuming customer_profile might be needed. Convert it as well.
                    render_context['customer_profile'] = str(related_contact.customer_profile)
            
            # Flatten common nested patterns
            # Handle created_order_details
            if 'created_order_details' in render_context:
                order_details = render_context['created_order_details']
                if isinstance(order_details, dict):
                    render_context['order_number'] = order_details.get('order_number', '')
                    render_context['order_amount'] = order_details.get('amount', '0.00')
            
            # Handle cart_items for list rendering
            if 'cart_items' in render_context:
                cart_items = render_context['cart_items']
                if isinstance(cart_items, list):
                    items_text = '\n'.join([f"- {item.get('quantity', 0)} x {item.get('name', '')}" for item in cart_items])
                    render_context['cart_items_list'] = items_text if items_text else '(No items)'
            
            # Handle order.* patterns
            if 'order' in render_context:
                order = render_context['order']
                if isinstance(order, dict):
                    render_context['order_name'] = order.get('name', '')
                    render_context['order_number'] = render_context.get('order_number') or order.get('order_number', '')
                    render_context['order_amount'] = render_context.get('order_amount') or order.get('amount', '0.00')
                    # Handle nested customer
                    if 'customer' in order and isinstance(order['customer'], dict):
                        customer = order['customer']
                        render_context['customer_name'] = (
                            customer.get('get_full_name') or 
                            customer.get('contact', {}).get('name', '') if isinstance(customer.get('contact'), dict) else ''
                        )
            
            # Handle target_contact
            if 'target_contact' in render_context:
                target = render_context['target_contact']
                if isinstance(target, list) and len(target) > 0:
                    render_context['customer_name'] = target[0].get('name', render_context.get('customer_whatsapp_id', ''))
            
            # Handle admin name
            if 'contact' in render_context and isinstance(render_context['contact'], str):
                # Contact already converted to string above, use contact_name
                render_context['admin_name'] = render_context.get('contact_name', '')
            
            # Handle recipient name
            if 'recipient' in render_context:
                recipient = render_context['recipient']
                if isinstance(recipient, dict):
                    render_context['recipient_name'] = recipient.get('first_name') or recipient.get('username', '')
            
            # Handle or expressions and defaults
            render_context['order_number'] = render_context.get('order_number', 'N/A')
            render_context['assessment_number'] = render_context.get('assessment_number', 'N/A')
            
            # Handle install_alt_name conditional
            install_alt_name = render_context.get('install_alt_name', '')
            if install_alt_name and install_alt_name.lower() != 'n/a':
                install_alt_phone = render_context.get('install_alt_phone', '')
                render_context['install_alt_contact_line'] = f"- Alt. Contact: {install_alt_name} ({install_alt_phone})"
            else:
                render_context['install_alt_contact_line'] = ''
            
            # Handle location pin conditionals
            install_pin = render_context.get('install_location_pin')
            if install_pin and isinstance(install_pin, dict):
                lat = install_pin.get('latitude')
                lon = install_pin.get('longitude')
                if lat and lon:
                    render_context['install_location_pin_line'] = f"- Location Pin: https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                else:
                    render_context['install_location_pin_line'] = ''
            else:
                render_context['install_location_pin_line'] = ''
            
            # Handle cleaning location pin
            cleaning_pin = render_context.get('cleaning_location_pin')
            if cleaning_pin and isinstance(cleaning_pin, dict):
                lat = cleaning_pin.get('latitude')
                lon = cleaning_pin.get('longitude')
                if lat and lon:
                    render_context['cleaning_location_pin_line'] = f"- Location Pin: https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                else:
                    render_context['cleaning_location_pin_line'] = ''
            else:
                render_context['cleaning_location_pin_line'] = ''
            
            # Handle title filters
            for field in ['install_availability', 'cleaning_roof_type', 'cleaning_panel_type', 
                         'cleaning_availability', 'install_kit_type', 'new_status']:
                if field in render_context and render_context[field]:
                    render_context[field] = str(render_context[field]).title()
            
            # Handle replace filters for loan types
            if 'loan_type' in render_context:
                render_context['loan_type'] = str(render_context.get('loan_type', '')).replace('_', ' ').title()
            if 'loan_employment_status' in render_context:
                render_context['loan_employment_status'] = str(render_context.get('loan_employment_status', '')).replace('_', ' ').title()
            
            # Handle conditional lines for loan
            loan_amount = render_context.get('loan_request_amount')
            render_context['loan_amount_line'] = f"- Amount Requested: *${loan_amount}*" if loan_amount else ''
            
            loan_product = render_context.get('loan_product_interest')
            render_context['loan_product_line'] = f"- Product of Interest: *{loan_product}*" if loan_product else ''
            
            # Handle loan application ID
            if 'created_loan_application' in render_context:
                loan_app = render_context['created_loan_application']
                if isinstance(loan_app, dict):
                    render_context['loan_application_id'] = loan_app.get('id', '')
            
            # Handle warranty details
            if 'found_warranty' in render_context:
                warranty = render_context['found_warranty']
                if isinstance(warranty, list) and len(warranty) > 0:
                    render_context['warranty_product_name'] = warranty[0].get('product__name', '')
                    render_context['warranty_serial_number'] = warranty[0].get('product_serial_number', '')
            
            # Handle resolution notes conditional
            resolution_notes = render_context.get('resolution_notes', '')
            if resolution_notes:
                render_context['resolution_notes_section'] = f"*Notes from our team:*\n{resolution_notes}\n"
            else:
                render_context['resolution_notes_section'] = ''
            
            # Handle job card details
            if 'job_card' in render_context:
                job_card = render_context['job_card']
                if isinstance(job_card, dict):
                    render_context['job_card_number'] = job_card.get('job_card_number', '')
                    render_context['product_description'] = job_card.get('product_description', '')
                    render_context['product_serial_number'] = job_card.get('product_serial_number', '')
                    render_context['reported_fault'] = job_card.get('reported_fault', '')
            
            # Handle customer details for job card
            if 'customer' in render_context:
                customer = render_context['customer']
                if isinstance(customer, dict):
                    first_name = customer.get('first_name', '')
                    last_name = customer.get('last_name', '')
                    render_context['customer_name'] = f"{first_name} {last_name}".strip() or render_context.get('customer_name', '')
            
            # Handle template_context nested patterns
            if 'template_context' in render_context:
                tpl_ctx = render_context['template_context']
                if isinstance(tpl_ctx, dict):
                    render_context['last_bot_message'] = tpl_ctx.get('last_bot_message', 'User requested help or an error occurred.')
            else:
                render_context['last_bot_message'] = render_context.get('last_bot_message', 'User requested help or an error occurred.')
            
            if related_flow:
                render_context['flow'] = str(related_flow)
            
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
            if (hasattr(template, 'body_parameters') and template.body_parameters) or \
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

 
                # Append version suffix to template name when sending to Meta
                template_name_with_version = get_versioned_template_name(template_name)
                
                content_payload = {
                    "name": template_name_with_version,
                    "language": { "code": "en_US" },
                    "components": template_components
                }

            outgoing_msg = Message.objects.create(
                contact=recipient_contact, 
                app_config=active_config, 
                direction='out', 
                message_type=message_type,
                content_payload=content_payload, 
                status='pending_dispatch'
            )
            send_whatsapp_message_task.delay(outgoing_msg.id, active_config.id)
            logger.info(f"Queued direct WhatsApp notification for template '{template_name}' to contact {recipient_contact.id} ({recipient_contact.whatsapp_id}).")