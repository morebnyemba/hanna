"""
Management command to seed notification templates for the HANNA CRM system.

This command creates all the notification templates needed for:
- Order lifecycle notifications
- Installation lifecycle notifications
- Warranty notifications
- Technician notifications
- Customer notifications
- Admin/System notifications

Run with: python manage.py seed_notification_templates
"""

from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate


# ============================================================================
# NOTIFICATION TEMPLATES DEFINITIONS
# ============================================================================

# Each template has:
# - name: Unique identifier (used in code to reference the template)
# - description: Human-readable description
# - message_body: The message content (Jinja2 supported)
# - body_parameters: Mapping for Meta WhatsApp template parameters
# - buttons: Quick reply buttons (if any)

NOTIFICATION_TEMPLATES = [
    # ============================================================================
    # ORDER LIFECYCLE TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_new_order_created",
        "description": "Sent to admin when a new order is created",
        "message_body": """New Order Created

Order: {{ order_number }}
Customer: {{ customer_name }}
Amount: ${{ order_amount }}

Status: Requires review and processing""",
        "body_parameters": {
            "1": "order_number",
            "2": "customer_name",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_order_confirmation",
        "description": "Sent to customer when their order is confirmed",
        "message_body": """Order Confirmed

Customer: {{ customer_name }}
Order Number: {{ order_number }}
Amount: ${{ order_amount }}

Status: Confirmed and being processed
{{ cart_items_list }}""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_payment_received",
        "description": "Sent to customer when payment is received",
        "message_body": """Payment Received

Order Number: {{ order_number }}
Amount: ${{ order_amount }}
Payment Method: {{ payment_method }}

Status: Payment confirmed
Your order is now being processed.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_payment_reminder",
        "description": "Reminder sent to customer for pending payment",
        "message_body": """Payment Reminder

Order Number: {{ order_number }}
Amount Due: ${{ order_amount }}

Status: Awaiting payment
Please complete payment to proceed with order processing.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_order_dispatched",
        "description": "Sent to customer when order is dispatched",
        "message_body": """Order Dispatched

Order Number: {{ order_number }}
Estimated Delivery: {{ delivery_date }}
{{ tracking_info }}

Status: Dispatched""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "delivery_date"
        }
    },

    # ============================================================================
    # SOLAR PACKAGE / INSTALLATION TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_solar_package_purchased",
        "description": "Sent to customer when they purchase a solar package",
        "message_body": """Solar Package Purchased

Package: {{ package_name }}
System Size: {{ system_size }}kW
Order Number: {{ order_number }}

Installation Record: {{ isr_id }}

Next Steps:
1. Our team will contact you to schedule installation
2. Site assessment will be arranged
3. Installation and commissioning
4. Warranty registration""",
        "body_parameters": {
            "1": "customer_name",
            "2": "package_name",
            "3": "system_size"
        }
    },
    {
        "name": "pfungwa_installation_scheduled",
        "description": "Sent to customer when installation is scheduled",
        "message_body": """Installation Scheduled

Location: {{ installation_address }}
Date: {{ installation_date }}
Time: {{ installation_time }}

Assigned Technician: {{ technician_name }}

Preparation Required:
- Ensure someone is present
- Roof/installation area must be accessible
- Electrical panel must be accessible""",
        "body_parameters": {
            "1": "customer_name",
            "2": "installation_date",
            "3": "technician_name"
        }
    },
    {
        "name": "pfungwa_installation_complete",
        "description": "Sent to customer when installation is completed",
        "message_body": """Installation Completed

System: {{ installation_type }}
Size: {{ system_size }}kW
Installation Record: {{ isr_id }}

Status: Successfully installed and commissioned

Warranties Registered:
{{ warranty_summary }}

Portal Access: https://hanna.co.zw/client
- Monitor your system
- View warranties
- Request service""",
        "body_parameters": {
            "1": "customer_name",
            "2": "installation_type",
            "3": "system_size"
        }
    },
    {
        "name": "pfungwa_installation_request_new",
        "description": "Sent to admin when new installation request is created",
        "message_body": """New Installation Request

Customer: {{ customer_name }}
Phone: {{ customer_phone }}
Type: {{ installation_type }}
Address: {{ installation_address }}

Request ID: {{ installation_request_id }}

Status: Requires scheduling""",
        "body_parameters": {
            "1": "customer_name",
            "2": "installation_type",
            "3": "installation_request_id"
        }
    },

    # ============================================================================
    # TECHNICIAN TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_technician_job_assigned",
        "description": "Sent to technician when a new job is assigned",
        "message_body": """New Job Assigned

Customer: {{ customer_name }}
Address: {{ installation_address }}
Date: {{ installation_date }}
System: {{ system_size }}kW {{ installation_type }}

Installation ID: {{ isr_id }}

Status: Please confirm availability""",
        "body_parameters": {
            "1": "technician_name",
            "2": "customer_name",
            "3": "installation_date"
        }
    },
    {
        "name": "pfungwa_technician_job_reminder",
        "description": "Reminder sent to technician before scheduled job",
        "message_body": """Job Reminder

Customer: {{ customer_name }}
Address: {{ installation_address }}
Scheduled Time: {{ installation_time }}

Installation scheduled for tomorrow.

Ensure all required equipment and documentation are ready.""",
        "body_parameters": {
            "1": "technician_name",
            "2": "customer_name",
            "3": "installation_time"
        }
    },
    {
        "name": "pfungwa_payout_approved",
        "description": "Sent to technician when payout is approved",
        "message_body": """Payout Approved

Payout ID: {{ payout_id }}
Amount: ${{ payout_amount }}
Installations: {{ installation_count }}

Status: Approved
Payment will be processed shortly.""",
        "body_parameters": {
            "1": "technician_name",
            "2": "payout_id",
            "3": "payout_amount"
        }
    },
    {
        "name": "pfungwa_payout_paid",
        "description": "Sent to technician when payout is completed",
        "message_body": """Payment Completed

Payout ID: {{ payout_id }}
Amount: ${{ payout_amount }}
Reference: {{ payment_reference }}

Status: Payment processed successfully""",
        "body_parameters": {
            "1": "technician_name",
            "2": "payout_amount",
            "3": "payment_reference"
        }
    },

    # ============================================================================
    # WARRANTY TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_warranty_registered",
        "description": "Sent to customer when warranty is registered",
        "message_body": """Warranty Registered

Product: {{ product_name }}
Serial Number: {{ serial_number }}
Valid Until: {{ warranty_end_date }}

Status: Successfully registered

Warranty certificate available in your client portal.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "product_name",
            "3": "warranty_end_date"
        }
    },
    {
        "name": "pfungwa_warranty_expiring",
        "description": "Reminder sent when warranty is about to expire",
        "message_body": """Warranty Expiring

Product: {{ product_name }}
Serial Number: {{ serial_number }}
Expiration Date: {{ warranty_end_date }}

Status: Expiring soon

Consider:
- Extended warranty options
- Service check before expiry
- System upgrades""",
        "body_parameters": {
            "1": "customer_name",
            "2": "product_name",
            "3": "warranty_end_date"
        }
    },
    {
        "name": "pfungwa_warranty_claim_submitted",
        "description": "Sent to customer when warranty claim is submitted",
        "message_body": """Warranty Claim Submitted

Claim Number: {{ claim_number }}
Product: {{ product_name }}
Issue: {{ reported_issue }}

Status: Under review
Response expected within 2 business days""",
        "body_parameters": {
            "1": "customer_name",
            "2": "claim_number",
            "3": "product_name"
        }
    },
    {
        "name": "pfungwa_warranty_claim_approved",
        "description": "Sent to customer when warranty claim is approved",
        "message_body": """Warranty Claim Approved

Claim Number: {{ claim_number }}
Product: {{ product_name }}
Resolution: {{ resolution_type }}
{{ resolution_notes_section }}

Status: Approved

Next steps will be communicated shortly.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "claim_number",
            "3": "resolution_type"
        }
    },

    # ============================================================================
    # SERVICE / JOB CARD TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_service_request_received",
        "description": "Sent to customer when service request is received",
        "message_body": """Service Request Received

Reference: {{ service_request_id }}
Issue: {{ reported_issue }}

Status: Under review
Team will contact within 24 hours""",
        "body_parameters": {
            "1": "customer_name",
            "2": "service_request_id",
            "3": "reported_issue"
        }
    },
    {
        "name": "pfungwa_job_card_created",
        "description": "Sent to customer when job card is created",
        "message_body": """Job Card Created

Job Card Number: {{ job_card_number }}
Product: {{ product_description }}
Issue: {{ reported_fault }}

Status: Technician assignment in progress""",
        "body_parameters": {
            "1": "customer_name",
            "2": "job_card_number",
            "3": "reported_fault"
        }
    },
    {
        "name": "pfungwa_job_card_completed",
        "description": "Sent to customer when job is completed",
        "message_body": """Service Completed

Job Card: {{ job_card_number }}
{{ resolution_notes_section }}

Status: Completed

Your feedback is appreciated.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "job_card_number"
        }
    },

    # ============================================================================
    # ADMIN / SYSTEM TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_admin_24h_window_reminder",
        "description": "Reminder to admin about 24-hour messaging window",
        "message_body": """24-Hour Messaging Window Alert

Contact: {{ contact_name }}
Phone: {{ customer_whatsapp_id }}

Status: Messaging window expiring soon
Use template message to continue conversation""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "pfungwa_message_send_failure",
        "description": "Sent to admin when message sending fails",
        "message_body": """Message Send Failure

Contact: {{ contact_name }}
Phone: {{ customer_whatsapp_id }}

Status: Message delivery failed
Please check conversation and retry or use template""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "pfungwa_human_handover_required",
        "description": "Sent to admin when bot needs human intervention",
        "message_body": """Human Intervention Requested

Contact: {{ contact_name }}
Phone: {{ customer_whatsapp_id }}

Status: Customer requested human agent
Last Bot Message: {{ last_bot_message }}

Please respond promptly""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "pfungwa_low_stock_alert",
        "description": "Alert sent when product stock is low",
        "message_body": """Low Stock Alert

Product: {{ product_name }}
SKU: {{ product_sku }}
Current Stock: {{ stock_quantity }}

Status: Reorder required""",
        "body_parameters": {
            "1": "product_name",
            "2": "product_sku",
            "3": "stock_quantity"
        }
    },

    # ============================================================================
    # RETAILER / BRANCH TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_branch_order_received",
        "description": "Sent to branch when order is assigned to them",
        "message_body": """New Order for Branch

Order: {{ order_number }}
Customer: {{ customer_name }}
Amount: ${{ order_amount }}

Status: Requires processing and dispatch""",
        "body_parameters": {
            "1": "order_number",
            "2": "customer_name",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_retailer_commission_earned",
        "description": "Sent to retailer when commission is earned",
        "message_body": """Commission Earned

Order: {{ order_number }}
Sale Amount: ${{ order_amount }}
Commission: ${{ commission_amount }}

Status: Recorded""",
        "body_parameters": {
            "1": "order_number",
            "2": "order_amount",
            "3": "commission_amount"
        }
    },

    # ============================================================================
    # MONITORING / ALERT TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_system_offline_alert",
        "description": "Alert when monitored system goes offline",
        "message_body": """System Offline Alert

Customer: {{ customer_name }}
System: {{ system_type }} - {{ system_size }}kW
Last Seen: {{ last_seen_time }}

Status: Offline
Investigation required""",
        "body_parameters": {
            "1": "customer_name",
            "2": "system_type",
            "3": "last_seen_time"
        }
    },
    {
        "name": "pfungwa_system_back_online",
        "description": "Notification when system comes back online",
        "message_body": """System Online

Customer: {{ customer_name }}
System: {{ system_type }}

Status: System restored and functioning normally""",
        "body_parameters": {
            "1": "customer_name",
            "2": "system_type"
        }
    },

    # ============================================================================
    # PORTAL ACCESS TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_portal_access_granted",
        "description": "Sent to customer when portal access is granted",
        "message_body": """Portal Access Granted

Portal: https://hanna.co.zw/client
Username: {{ username }}
Temporary Password: {{ temp_password }}

Status: Account created
Please change password on first login

Available Features:
- System monitoring
- Warranty management
- Service requests
- Document access""",
        "body_parameters": {
            "1": "customer_name",
            "2": "username",
            "3": "temp_password"
        }
    },
    {
        "name": "pfungwa_password_reset",
        "description": "Password reset notification",
        "message_body": """Password Reset

Temporary Password: {{ temp_password }}

Status: Reset completed
Please login and change password immediately""",
        "body_parameters": {
            "1": "customer_name",
            "2": "temp_password"
        }
    },
]


class Command(BaseCommand):
    help = 'Seed notification templates for the HANNA CRM system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing templates',
        )

    def handle(self, *args, **options):
        defined_names = [template['name'] for template in NOTIFICATION_TEMPLATES]
        defined_count = len(defined_names)
        unique_defined_count = len(set(defined_names))
        existing_count = NotificationTemplate.objects.filter(name__in=defined_names).count()

        self.stdout.write(f"Template definitions: {defined_count}")
        if unique_defined_count != defined_count:
            self.stdout.write(
                self.style.WARNING(
                    f"Duplicate template names detected: {defined_count - unique_defined_count}"
                )
            )
        self.stdout.write(f"Existing templates matched: {existing_count}")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for template_data in NOTIFICATION_TEMPLATES:
            name = template_data['name']
            
            existing = NotificationTemplate.objects.filter(name=name).first()
            
            if existing:
                # Update existing template
                existing.description = template_data.get('description', '')
                existing.message_body = template_data['message_body']
                existing.body_parameters = template_data.get('body_parameters', {})
                existing.buttons = template_data.get('buttons', [])
                existing.url_parameters = template_data.get('url_parameters', {})
                existing.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {name}')
                )
            else:
                # Create new template
                NotificationTemplate.objects.create(
                    name=name,
                    description=template_data.get('description', ''),
                    message_body=template_data['message_body'],
                    body_parameters=template_data.get('body_parameters', {}),
                    buttons=template_data.get('buttons', []),
                    url_parameters=template_data.get('url_parameters', {}),
                    sync_status='pending'
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {name}')
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Summary: {created_count} created, {updated_count} updated, {skipped_count} skipped'
        ))
        self.stdout.write(
            f'Total templates: {NotificationTemplate.objects.count()}'
        )
