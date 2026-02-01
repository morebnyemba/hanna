# whatsappcrm_backend/notifications/management/commands/load_notification_templates.py
# (This file has been moved from the 'flows' app to the 'notifications' app for better project structure)

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

Status: Requires review in admin panel"""
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

Status: Requires follow-up for payment"""
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

Action: Schedule installation"""
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

Action: Confirm schedule"""
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

Status: Requires quote and scheduling"""
    },
    {
        "name": "pfungwa_new_custom_furniture_installation_request",
        "description": "Sent to admins when a customer submits a new custom furniture installation/delivery request.",
        "template_type": "whatsapp",
        "body": """New Custom Furniture Installation Request

Contact: {{ contact_name }}

Order Details:
- Order Number: {{ furniture_order_number }}
- Furniture Type: {{ furniture_type }}
- Specifications: {{ furniture_specifications }}

Client Details:
- Name: {{ furniture_full_name }}
- Phone: {{ furniture_contact_phone }}
{{ furniture_alt_contact_line }}

Delivery/Installation:
- Address: {{ furniture_address }}
{{ furniture_location_pin_line }}- Preferred Date: {{ furniture_preferred_date }} ({{ furniture_availability }})

Status: Requires scheduling confirmation"""
    },
    {
        "name": "pfungwa_admin_order_and_install_created",
        "description": "Sent to admins when another admin creates a new order and installation request via the admin flow.",
        "template_type": "whatsapp",
        "body": """Admin Action: Order and Installation Created

Admin: {{ admin_name }}
Customer: {{ customer_name }}
Order Number: PO-{{ order_number_ref }}
Order Name: {{ order_description }}

Status: Review in admin panel"""
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

Status: Requires scheduling"""
    },
    {
        "name": "pfungwa_job_card_created_successfully",
        "description": "Sent to admins when a job card is successfully created from an email attachment.",
        "template_type": "whatsapp",
        "body": """New Job Card Created

Job Card Number: {{ job_card_number }}
Customer: {{ customer_name }}
Product: {{ product_description }}
Serial Number: {{ product_serial_number }}
Reported Fault: {{ reported_fault }}

Status: Review and assign technician"""
    },
    {
        "name": "pfungwa_human_handover_flow",
        "description": "Sent to admins when a user is handed over to a human agent by the flow engine.",
        "template_type": "whatsapp",
        "body": """Human Intervention Required

Contact: {{ related_contact_name }}

Reason:
{{ last_bot_message }}

Status: Requires response in main inbox"""
    },
    {
        "name": "pfungwa_new_placeholder_order_created",
        "description": "Sent to admins when a placeholder order is created via the order receiver number.",
        "template_type": "whatsapp",
        "body": """New Placeholder Order Created

Contact: {{ contact_name }}
Order Number: {{ order_number_from_message }}

Status: Update order details in admin panel"""
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
Reply with any command to keep the window open"""
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
        "name": "pfungwa_new_loan_application",
        "description": "Sent to the finance team when a customer submits a new loan application.",
        "template_type": "whatsapp",
        "body": """New Loan Application Received

Contact: {{ contact_name }}
Application ID: {{ loan_application_id }}
Applicant Name: {{ loan_applicant_name }}
National ID: {{ loan_national_id }}
Loan Type: {{ loan_type }}
Employment: {{ loan_employment_status }}
Monthly Income: ${{ loan_monthly_income }}
{{ loan_amount_line }}
{{ loan_product_line }}

Status: Review in admin panel"""
    },
    {
        "name": "pfungwa_new_warranty_claim_submitted",
        "description": "Sent to admins when a customer submits a new warranty claim.",
        "template_type": "whatsapp",
        "body": """New Warranty Claim Submitted

Contact: {{ contact_name }}
Claim ID: {{ generated_claim_id }}
Product: {{ warranty_product_name }}
Serial Number: {{ warranty_serial_number }}

Fault Description:
{{ fault_description }}

Status: Review in admin panel"""
    },
    {
        "name": "pfungwa_warranty_claim_status_updated",
        "description": "Sent to a customer when an admin updates their warranty claim status.",
        "template_type": "whatsapp",
        "body": """Warranty Claim Status Updated

Claim ID: {{ claim_id }}
Product Serial: {{ serial_number }}
New Status: {{ new_status }}

{{ resolution_notes_section }}"""
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