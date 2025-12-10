# whatsappcrm_backend/flows/management/commands/load_notification_templates.py

from django.core.management.base import BaseCommand
from django.db import transaction
from notifications.models import NotificationTemplate


# A list of all notification templates used throughout the application.
# This makes them easy to manage and deploy.
NOTIFICATION_TEMPLATES = [
    {
        "name": "hanna_new_order_created",
        "description": "Sent to admins when a new order is created via a signal.",
        "template_type": "whatsapp",
        "body": """New Order Created! 📦

A new order has been created for customer *{{ customer_name }}*.

- Order Name: *{{ order_name }}*
- Order #: *{{ order_number }}*
- Amount: *${{ order_amount }}*

Please see the admin panel for full details.""",
        "buttons": [
            {"type": "URL", "text": "View Order", "url": "https://backend.hanna.co.zw/admin/customer_data/order/{{ order_id }}/change/"}
        ]
    },
    {
        "name": "hanna_new_online_order_placed",
        "description": "Sent to admins when a customer places a new order through the 'Purchase Product' flow.",
        "template_type": "whatsapp",
        "body": """New Online Order Placed! 🛍️

A new order has been placed via WhatsApp by *{{ contact_name }}*.

*Order Details:*
- Order #: *{{ order_number }}*
- Total Amount: *${{ order_amount }}*
- Payment Status: Pending

*Customer & Delivery:*
- Name: {{ delivery_name }}
- Phone: {{ delivery_phone }}
- Address: {{ delivery_address }}

*Items Ordered:*
{{ cart_items_list }}

Please follow up with the customer to arrange payment.""",
        "buttons": [
            {"type": "URL", "text": "View Order", "url": "https://backend.hanna.co.zw/admin/customer_data/order/{{ order_id }}/change/"}
        ]
    },
    {
        "name": "hanna_order_payment_status_updated",
        "description": "Sent to a customer when an admin updates their order's payment status.",
        "template_type": "whatsapp",
        "body": """Hello! 👋

The status for your order '{{ order_name }}' (#{{ order_number }}) has been updated to: *{{ new_status }}*.

Thank you for choosing us!"""
    },
    {
        "name": "hanna_assessment_status_updated",
        "description": "Sent to a customer when an admin updates their site assessment status.",
        "template_type": "whatsapp",
        "body": """Hello! 👋

The status for your Site Assessment Request (#{{ assessment_id }}) has been updated to: *{{ new_status }}*.

Our team will be in touch with the next steps. Thank you!"""
    },
    {
        "name": "hanna_new_installation_request",
        "description": "Sent to admins when a customer submits a new solar installation request.",
        "template_type": "whatsapp",
        "body": """New Installation Request 🛠️

A new installation request has been submitted by *{{ contact_name }}*.

*Request Details:*
- Type: {{ installation_type }}
- Order #: {{ order_number }}
- Assessment #: {{ assessment_number }}

*Installation Info:*
- Branch: {{ install_branch }}
- Sales Person: {{ install_sales_person }}
- Client Name: {{ install_full_name }}
- Client Phone: {{ install_phone }}{{ install_alt_contact_line }}
- Address: {{ install_address }}{{ install_location_pin_line }}
- Preferred Date: {{ install_datetime }} ({{ install_availability }})

Please review and schedule the installation.""",
        "buttons": [
            {"type": "URL", "text": "View Request", "url": "https://backend.hanna.co.zw/admin/customer_data/installationrequest/{{ installation_request_id }}/change/"}
        ]
    },
    {
        "name": "hanna_new_starlink_installation_request",
        "description": "Sent to admins when a customer submits a new Starlink installation request.",
        "template_type": "whatsapp",
        "body": """New Starlink Installation Request 🛰️

A new Starlink installation request has been submitted by *{{ contact_name }}*.

*Client & Location:*
- Name: {{ install_full_name }}
- Phone: {{ install_phone }}
- Address: {{ install_address }}{{ install_location_pin_line }}

*Scheduling:*
- Preferred Date: {{ install_datetime }} ({{ install_availability }})

*Job Details:*
- Kit Type: {{ install_kit_type }}
- Desired Mount: {{ install_mount_location }}

Please follow up to confirm the schedule.""",
        "buttons": [
            {"type": "URL", "text": "View Request", "url": "https://backend.hanna.co.zw/admin/customer_data/installationrequest/{{ installation_request_id }}/change/"}
        ]
    },
    {
        "name": "hanna_new_solar_cleaning_request",
        "description": "Sent to admins when a customer submits a new solar panel cleaning request.",
        "template_type": "whatsapp",
        "body": """New Solar Cleaning Request 💧

A new cleaning request has been submitted by *{{ contact_name }}*.

*Client Details:*
- Name: {{ cleaning_full_name }}
- Phone: {{ cleaning_phone }}

*Job Details:*
- Roof Type: {{ cleaning_roof_type }}
- Panels: {{ cleaning_panel_count }} x {{ cleaning_panel_type }}
- Preferred Date: {{ cleaning_date }} ({{ cleaning_availability }})
- Address: {{ cleaning_address }}{{ cleaning_location_pin_line }}

Please follow up to provide a quote and schedule the service.""",
        "buttons": [
            {"type": "URL", "text": "View Request", "url": "https://backend.hanna.co.zw/admin/customer_data/solarcleaningrequest/{{ cleaning_request_id }}/change/"}
        ]
    },
    {
        "name": "hanna_admin_order_and_install_created",
        "description": "Sent to admins when another admin creates a new order and installation request via the admin flow.",
        "template_type": "whatsapp",
        "body": """Admin Action: New Order & Install Created 📝

Admin *{{ admin_name }}* has created a new order and installation request.
*Customer:* {{ customer_name }}
*Order #:* {{ order_number_ref }}
*Order Name:* {{ order_description }}

Please see the admin panel for full details.""",
        "buttons": [
            {"type": "URL", "text": "View Order", "url": "https://backend.hanna.co.zw/admin/customer_data/order/{{ order_id }}/change/"}
        ]
    },
    {
        "name": "hanna_new_site_assessment_request",
        "description": "Sent to admins when a customer books a new site assessment.",
        "template_type": "whatsapp",
        "body": """New Site Assessment Request 📋

A new site assessment has been requested by *{{ contact_name }}*.

*Request Details:*
- Name: {{ assessment_full_name }}
- Company: {{ assessment_company_name }}
- Address: {{ assessment_address }}
- Contact: {{ assessment_contact_info }}
- Preferred Day: {{ assessment_preferred_day }}

Please follow up to schedule the assessment.""",
        "buttons": [
            {"type": "URL", "text": "View Request", "url": "https://backend.hanna.co.zw/admin/customer_data/siteassessmentrequest/{{ assessment_request_id }}/change/"}
        ]
    },
    {
        "name": "hanna_job_card_created_successfully",
        "description": "Sent to admins when a job card is successfully created from an email attachment.",
        "template_type": "whatsapp",
        "body": """New Job Card Created ⚙️

A new job card has been automatically created from an email attachment.

*Job Card #*: {{ job_card.job_card_number }}
*Customer*: {{ customer.first_name }} {{ customer.last_name }}
*Product*: {{ job_card.product_description }}
*Serial #*: {{ job_card.product_serial_number }}
*Reported Fault*: {{ job_card.reported_fault }}

Please review the job card in the admin panel and assign it to a technician.""",
        "buttons": [
            {"type": "URL", "text": "View Job Card", "url": "https://backend.hanna.co.zw/admin/customer_data/jobcard/{{ job_card.id }}/change/"}
        ]
    },
    {
        "name": "hanna_human_handover_flow",
        "description": "Sent to admins when a user is handed over to a human agent by the flow engine.",
        "template_type": "whatsapp",
        "body": """Human Intervention Required ⚠️

Contact *{{ related_contact_name }}* requires assistance.

*Reason:*
{{ last_bot_message }}

Please respond to them in the main inbox.""",
        "buttons": [
            {"type": "QUICK_REPLY", "text": "Acknowledge"},
            {"type": "URL", "text": "View Conversation", "url": "https://backend.hanna.co.zw/admin/conversations/contact/{{ related_contact.id }}/change/"}
        ]
    },
    {
        "name": "hanna_new_placeholder_order_created",
        "description": "Sent to admins when a placeholder order is created via the order receiver number.",
        "template_type": "whatsapp",
        "body": """New Placeholder Order Created 📦

A new placeholder order has been created by *{{ contact_name }}*.

*Order #:* {{ normalized_order_number }}

Please update the order details in the admin panel as soon as possible.""",
        "buttons": [
            {"type": "URL", "text": "View Order", "url": "https://backend.hanna.co.zw/admin/customer_data/order/?q={{ normalized_order_number }}"}
        ]
    },
    {
        "name": "hanna_message_send_failure",
        "description": "Sent to admins when a WhatsApp message fails to send.",
        "template_type": "whatsapp",
        "body": """Message Send Failure ⚠️

Failed to send a message to *{{ related_contact_name }}*.

*Reason:* {{ error_details }}

Please check the system logs for more details."""
    },
    {
        "name": "hanna_admin_24h_window_reminder",
        "description": "Sent to an admin user when their 24-hour interaction window is about to close.",
        "template_type": "whatsapp",
        "body": """Hi {{ recipient_name }},

This is an automated reminder. Your 24-hour interaction window for receiving system notifications on WhatsApp is closing soon.

Please reply with "status" or any other command to keep the window open.""",
        "buttons": [
            {"type": "QUICK_REPLY", "text": "Reply Now"}
        ]
    },
    {
        "name": "hanna_invoice_processed_successfully",
        "description": "Sent to admins when an invoice from an email has been successfully processed into an order.",
        "template_type": "whatsapp",
        "body": """Invoice Processed Successfully ✅

An invoice from *{{ sender }}* (Filename: *{{ filename }}*) has been processed.

*Order Details:*
- Order #: *{{ order_number }}*
- Total Amount: *${{ order_amount }}*
- Customer: *{{ customer_name }}*

The new order has been created in the system."""
    },
    {
        "name": "hanna_customer_invoice_confirmation",
        "description": "Sent to a customer via WhatsApp after their emailed invoice has been successfully processed and an order created.",
        "template_type": "whatsapp",
        "body": """Hello {{ customer_name }}! 👋

This is a confirmation that your invoice has been successfully processed.

*Order Details:*
- Order #: *{{ order_number }}*
- Invoice Date: {{ invoice_date }}
- Total Amount: *${{ total_amount }}*

An installation has been provisionally scheduled and our team will be in touch shortly to confirm the details.

Thank you for choosing Hanna Installations!"""
    },
]


class Command(BaseCommand):
    help = 'Loads or updates predefined notification templates from a definition list.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to load notification templates...")
        
        for template_def in NOTIFICATION_TEMPLATES:
            template_name = template_def['name']
            
            template, created = NotificationTemplate.objects.update_or_create(
                name=template_name,
                defaults={
                    'description': template_def.get('description', ''),
                    'message_body': template_def.get('body', ''),
                    'buttons': template_def.get('buttons', []),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created new template: '{template_name}'"))
            else:
                self.stdout.write(f"  Updated existing template: '{template_name}'")

        self.stdout.write(self.style.SUCCESS("Successfully loaded all notification templates."))