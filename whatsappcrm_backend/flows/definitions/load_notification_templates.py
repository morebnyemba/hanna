# whatsappcrm_backend/notifications/management/commands/load_notification_templates.py
# (This file has been moved from the 'flows' app to the 'notifications' app for better project structure)

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

Please see the admin panel for full details."""
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

Please follow up with the customer to arrange payment."""
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
- Client Phone: {{ install_phone }}
{{ install_alt_contact_line }}
- Address: {{ install_address }}
{{ install_location_pin_line }}
- Preferred Date: {{ install_datetime }} ({{ install_availability }})

Please review and schedule the installation."""
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
- Address: {{ install_address }}
{{ install_location_pin_line }}

*Scheduling:*
- Preferred Date: {{ install_datetime }} ({{ install_availability }})

*Job Details:*
- Kit Type: {{ install_kit_type }}
- Desired Mount: {{ install_mount_location }}

Please follow up to confirm the schedule."""
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
- Address: {{ cleaning_address }}
{{ cleaning_location_pin_line }}

Please follow up to provide a quote and schedule the service."""
    },
    {
        "name": "hanna_new_custom_furniture_installation_request",
        "description": "Sent to admins when a customer submits a new custom furniture installation/delivery request.",
        "template_type": "whatsapp",
        "body": """New Custom Furniture Installation Request 🪑

A new furniture installation request has been submitted by *{{ contact_name }}*.

*Order Details:*
- Order #: {{ furniture_order_number }}
- Furniture Type: {{ furniture_type }}
- Specifications: {{ furniture_specifications }}

*Client Details:*
- Name: {{ furniture_full_name }}
- Phone: {{ furniture_contact_phone }}{{ furniture_alt_contact_line }}

*Delivery/Installation Info:*
- Address: {{ furniture_address }}{{ furniture_location_pin_line }}
- Preferred Date: {{ furniture_preferred_date }} ({{ furniture_availability }})

Please follow up to confirm the delivery/installation schedule."""
    },
    {
        "name": "hanna_admin_order_and_install_created",
        "description": "Sent to admins when another admin creates a new order and installation request via the admin flow.",
        "template_type": "whatsapp",
        "body": """Admin Action: New Order & Install Created 📝

Admin *{{ admin_name }}* has created a new order and installation request.

*Customer:* {{ customer_name }}
*Order #:* PO-{{ order_number_ref }}
*Order Name:* {{ order_description }}

Please see the admin panel for full details."""
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

Please follow up to schedule the assessment."""
    },
    {
        "name": "hanna_job_card_created_successfully",
        "description": "Sent to admins when a job card is successfully created from an email attachment.",
        "template_type": "whatsapp",
        "body": """New Job Card Created ⚙️

A new job card has been automatically created from an email attachment.

*Job Card #*: {{ job_card_number }}
*Customer*: {{ customer_name }}
*Product*: {{ product_description }}
*Serial #*: {{ product_serial_number }}
*Reported Fault*: {{ reported_fault }}

Please review the job card in the admin panel and assign it to a technician."""
    },
    {
        "name": "hanna_human_handover_flow",
        "description": "Sent to admins when a user is handed over to a human agent by the flow engine.",
        "template_type": "whatsapp",
        "body": """Human Intervention Required ⚠️

Contact *{{ related_contact_name }}* requires assistance.

*Reason:*
{{ last_bot_message }}

Please respond to them in the main inbox."""
    },
    {
        "name": "hanna_new_placeholder_order_created",
        "description": "Sent to admins when a placeholder order is created via the order receiver number.",
        "template_type": "whatsapp",
        "body": """New Placeholder Order Created 📦

A new placeholder order has been created by *{{ contact_name }}*.

*Order #:* {{ order_number_from_message }}

Please update the order details in the admin panel as soon as possible."""
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

Please reply with "status" or any other command to keep the window open."""
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
    {
        "name": "hanna_new_loan_application",
        "description": "Sent to the finance team when a customer submits a new loan application.",
        "template_type": "whatsapp",
        "body": """New Loan Application Received 💰

A new loan application has been submitted by *{{ contact_name }}*.

*Application Details:*
- Application ID: *#{{ loan_application_id }}*
- Name: *{{ loan_applicant_name }}*
- National ID: {{ loan_national_id }}
- Loan Type: {{ loan_type }}
- Employment: {{ loan_employment_status }}
- Monthly Income: ${{ loan_monthly_income }}
{{ loan_amount_line }}
{{ loan_product_line }}

Please review the application in the admin panel and follow up with the customer."""
    },
    {
        "name": "hanna_new_warranty_claim_submitted",
        "description": "Sent to admins when a customer submits a new warranty claim.",
        "template_type": "whatsapp",
        "body": """New Warranty Claim Submitted 🛡️

A new warranty claim has been submitted by *{{ contact_name }}*.

*Claim Details:*
- Claim ID: *{{ generated_claim_id }}*
- Product: *{{ warranty_product_name }}*
- Serial Number: `{{ warranty_serial_number }}`

*Fault Description:*
{{ fault_description }}

Please review the claim in the admin panel and update its status."""
    },
    {
        "name": "hanna_warranty_claim_status_updated",
        "description": "Sent to a customer when an admin updates their warranty claim status.",
        "template_type": "whatsapp",
        "body": """Hello! 👋

The status for your Warranty Claim (#{{ claim_id }}) for product `{{ serial_number }}` has been updated to: *{{ new_status }}*.

{{ resolution_notes_section }}
Thank you for your patience!"""
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
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created new template: '{template_name}'"))
            else:
                self.stdout.write(f"  Updated existing template: '{template_name}'")

        self.stdout.write(self.style.SUCCESS("Successfully loaded all notification templates."))