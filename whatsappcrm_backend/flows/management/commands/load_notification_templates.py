# whatsappcrm_backend/flows/management/commands/load_notification_templates.py

from django.core.management.base import BaseCommand
from django.db import transaction
from notifications.models import NotificationTemplate


# A list of all notification templates used throughout the application.
# This makes them easy to manage and deploy.
NOTIFICATION_TEMPLATES = [
    {
        "name": "pfungwa_new_order_created",
        "description": "Sent to admins when a new order is created via a signal.",
        "template_type": "whatsapp",
        "body": """New Order Created

Customer: {{ customer_name }}
Order Name: {{ order_name }}
Order Number: {{ order_number }}
Amount: ${{ order_amount }}

Status: Requires review in admin panel""",
        "buttons": [
            {"type": "URL", "text": "View Order", "url": "https://backend.hanna.co.zw/admin/customer_data/order/{{ order_id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_new_online_order_placed",
        "description": "Sent to admins when a customer places a new order through the 'Purchase Product' flow.",
        "template_type": "whatsapp",
        "body": """New Online Order Placed

Contact: {{ contact_name }}
Order Number: {{ order_number }}
Total Amount: ${{ order_amount }}
Payment Status: Pending

Delivery Details:
- Name: {{ delivery_name }}
- Phone: {{ delivery_phone }}
- Address: {{ delivery_address }}

Items:
{{ cart_items_list }}

Status: Requires follow-up for payment""",
        "buttons": [
            {"type": "URL", "text": "View Order", "url": "https://backend.hanna.co.zw/admin/customer_data/order/{{ order_id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_order_payment_status_updated",
        "description": "Sent to a customer when an admin updates their order's payment status.",
        "template_type": "whatsapp",
        "body": """Order Payment Status Updated

Order Name: {{ order_name }}
Order Number: {{ order_number }}
New Status: {{ new_status }}"""
    },
    {
        "name": "pfungwa_assessment_status_updated",
        "description": "Sent to a customer when an admin updates their site assessment status.",
        "template_type": "whatsapp",
        "body": """Site Assessment Status Updated

Assessment ID: {{ assessment_id }}
New Status: {{ new_status }}

Status: Team will follow up with next steps"""
    },
    {
        "name": "pfungwa_new_installation_request",
        "description": "Sent to admins when a customer submits a new solar installation request.",
        "template_type": "whatsapp",
        "body": """New Installation Request

Contact Name: {{ contact_name }}
Contact Phone: {{ install_phone }}
Type: {{ installation_type }}
Order Number: {{ order_number }}
Assessment Number: {{ assessment_number }}

Branch: {{ install_branch }}
Sales Person: {{ install_sales_person }}
Client Name: {{ install_full_name }}
Alt Contact: {{ install_alt_contact_line }}
Address: {{ install_address }}
Location Pin: {{ install_location_pin_line }}
Preferred Date: {{ install_datetime }}
Availability: {{ install_availability }}

Action: Schedule installation""",
        "buttons": [
            {"type": "URL", "text": "View Request", "url": "https://backend.hanna.co.zw/admin/customer_data/installationrequest/{{ installation_request_id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_new_starlink_installation_request",
        "description": "Sent to admins when a customer submits a new Starlink installation request.",
        "template_type": "whatsapp",
        "body": """New Starlink Installation Request

Contact Name: {{ contact_name }}
Contact Phone: {{ install_phone }}
Client Name: {{ install_full_name }}
Address: {{ install_address }}
Location Pin: {{ install_location_pin_line }}

Preferred Date: {{ install_datetime }}
Availability: {{ install_availability }}

Kit Type: {{ install_kit_type }}
Mount Location: {{ install_mount_location }}

Action: Confirm schedule""",
        "buttons": [
            {"type": "URL", "text": "View Request", "url": "https://backend.hanna.co.zw/admin/customer_data/installationrequest/{{ installation_request_id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_new_solar_cleaning_request",
        "description": "Sent to admins when a customer submits a new solar panel cleaning request.",
        "template_type": "whatsapp",
        "body": """New Solar Cleaning Request

Contact: {{ contact_name }}
Client Name: {{ cleaning_full_name }}
Phone: {{ cleaning_phone }}

Job Details:
- Roof Type: {{ cleaning_roof_type }}
- Panels: {{ cleaning_panel_count }} x {{ cleaning_panel_type }}
- Preferred Date: {{ cleaning_date }} ({{ cleaning_availability }})
- Address: {{ cleaning_address }}
{{ cleaning_location_pin_line }}

Status: Requires quote and scheduling""",
        "buttons": [
            {"type": "URL", "text": "View Request", "url": "https://backend.hanna.co.zw/admin/customer_data/solarcleaningrequest/{{ cleaning_request_id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_admin_order_and_install_created",
        "description": "Sent to admins when another admin creates a new order and installation request via the admin flow.",
        "template_type": "whatsapp",
        "body": """Admin Action: Order and Installation Created

Admin: {{ admin_name }}
Customer: {{ customer_name }}
Order Number: {{ order_number_ref }}
Order Name: {{ order_description }}

Status: Review in admin panel""",
        "buttons": [
            {"type": "URL", "text": "View Order", "url": "https://backend.hanna.co.zw/admin/customer_data/order/{{ order_id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_new_site_assessment_request",
        "description": "Sent to admins when a customer books a new site assessment.",
        "template_type": "whatsapp",
        "body": """New Site Assessment Request

Contact: {{ contact_name }}
Name: {{ assessment_full_name }}
Company: {{ assessment_company_name }}
Address: {{ assessment_address }}
Contact Info: {{ assessment_contact_info }}
Preferred Day: {{ assessment_preferred_day }}

Status: Requires scheduling""",
        "buttons": [
            {"type": "URL", "text": "View Request", "url": "https://backend.hanna.co.zw/admin/customer_data/siteassessmentrequest/{{ assessment_request_id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_job_card_created_successfully",
        "description": "Sent to admins when a job card is successfully created from an email attachment.",
        "template_type": "whatsapp",
        "body": """New Job Card Created

Job Card Number: {{ job_card.job_card_number }}
Customer: {{ customer.first_name }} {{ customer.last_name }}
Product: {{ job_card.product_description }}
Serial Number: {{ job_card.product_serial_number }}
Reported Fault: {{ job_card.reported_fault }}

Status: Review and assign technician""",
        "buttons": [
            {"type": "URL", "text": "View Job Card", "url": "https://backend.hanna.co.zw/admin/customer_data/jobcard/{{ job_card.id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_human_handover_flow",
        "description": "Sent to admins when a user is handed over to a human agent by the flow engine.",
        "template_type": "whatsapp",
        "body": """Human Intervention Required

Contact: {{ related_contact_name }}

Reason:
{{ last_bot_message }}

Status: Requires response in main inbox""",
        "buttons": [
            {"type": "QUICK_REPLY", "text": "Acknowledge"},
            {"type": "URL", "text": "View Conversation", "url": "https://backend.hanna.co.zw/admin/conversations/contact/{{ related_contact.id }}/change/"}
        ]
    },
    {
        "name": "pfungwa_new_placeholder_order_created",
        "description": "Sent to admins when a placeholder order is created via the order receiver number.",
        "template_type": "whatsapp",
        "body": """New Placeholder Order Created

Contact: {{ contact_name }}
Order Number: {{ normalized_order_number }}

Status: Update order details in admin panel""",
        "buttons": [
            {"type": "URL", "text": "View Order", "url": "https://backend.hanna.co.zw/admin/customer_data/order/?q={{ normalized_order_number }}"}
        ]
    },
    {
        "name": "pfungwa_message_send_failure",
        "description": "Sent to admins when a WhatsApp message fails to send.",
        "template_type": "whatsapp",
        "body": """Message Send Failure

Contact: {{ related_contact_name }}
Reason: {{ error_details }}

Status: Check system logs for details"""
    },
    {
        "name": "pfungwa_admin_24h_window_reminder",
        "description": "Sent to an admin user when their 24-hour interaction window is about to close.",
        "template_type": "whatsapp",
        "body": """24-Hour Messaging Window Alert

Recipient: {{ recipient_name }}

Status: Messaging window expiring soon
Reply with any command to keep the window open""",
        "buttons": [
            {"type": "QUICK_REPLY", "text": "Reply Now"}
        ]
    },
    {
        "name": "pfungwa_invoice_processed_successfully",
        "description": "Sent to admins when an invoice from an email has been successfully processed into an order.",
        "template_type": "whatsapp",
        "body": """Invoice Processed

Sender: {{ sender }}
Filename: {{ filename }}

Order Number: {{ order_number }}
Total Amount: ${{ order_amount }}
Customer: {{ customer_name }}

Status: New order created"""
    },
    {
        "name": "pfungwa_customer_invoice_confirmation",
        "description": "Sent to a customer via WhatsApp after their emailed invoice has been successfully processed and an order created.",
        "template_type": "whatsapp",
        "body": """Invoice Processed

Customer: {{ customer_name }}
Order Number: {{ order_number }}
Invoice Date: {{ invoice_date }}
Total Amount: ${{ total_amount }}

Status: Installation provisionally scheduled
Team will confirm details"""
    },
    {
        "name": "solar_alert_notification",
        "description": "Sent to technical admin and solar monitoring teams when a solar system alert is triggered.",
        "template_type": "whatsapp",
        "body": """Solar System Alert

Title: {{ alert_title }}
Severity: {{ alert_severity }}
Type: {{ alert_type }}
Station: {{ station_name }}
Inverter: {{ inverter_serial }}

Description:
{{ description }}

Time: {{ occurred_at }}

Status: Investigation required"""
    },
    {
        "name": "sla_alert",
        "description": "Sent to relevant teams when an SLA alert is triggered for warranty requests.",
        "template_type": "email",
        "body": """SLA Alert - Warranty Request

An SLA violation has been detected for a warranty request.

*Request Details:*
- Type: {{ request_type }}
- Request ID: {{ request_id }}
- Response Status: {{ response_status }}
- Resolution Status: {{ resolution_status }}

*Deadlines:*
- Response Deadline: {{ response_deadline }}
- Resolution Deadline: {{ resolution_deadline }}

Please take immediate action to address this SLA violation."""
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