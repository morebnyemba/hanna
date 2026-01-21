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
        "name": "hanna_new_order_created",
        "description": "Sent to admin when a new order is created",
        "message_body": """🛒 *New Order Created*

Order: {{ order_number }}
Customer: {{ customer_name }}
Amount: ${{ order_amount }}

Please review and process the order.""",
        "body_parameters": {
            "1": "order_number",
            "2": "customer_name",
            "3": "order_amount"
        }
    },
    {
        "name": "hanna_order_confirmation",
        "description": "Sent to customer when their order is confirmed",
        "message_body": """✅ *Order Confirmed*

Hi {{ customer_name }},

Your order *{{ order_number }}* has been confirmed!

Order Details:
- Amount: ${{ order_amount }}
{{ cart_items_list }}

We'll notify you when it's ready for dispatch.

Thank you for choosing HANNA! 🌟""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "hanna_payment_received",
        "description": "Sent to customer when payment is received",
        "message_body": """💰 *Payment Received*

Hi {{ customer_name }},

We've received your payment for order *{{ order_number }}*.

Amount: ${{ order_amount }}
Payment Method: {{ payment_method }}

Your order is now being processed. We'll update you on the next steps.

Thank you! 🙏""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "hanna_payment_reminder",
        "description": "Reminder sent to customer for pending payment",
        "message_body": """⏰ *Payment Reminder*

Hi {{ customer_name }},

Your order *{{ order_number }}* is awaiting payment.

Amount Due: ${{ order_amount }}

Please complete your payment to proceed with your order.

Need help? Reply to this message.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "hanna_order_dispatched",
        "description": "Sent to customer when order is dispatched",
        "message_body": """📦 *Order Dispatched*

Hi {{ customer_name }},

Great news! Your order *{{ order_number }}* has been dispatched.

Estimated delivery: {{ delivery_date }}
{{ tracking_info }}

Track your order or contact us if you have questions.""",
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
        "name": "hanna_solar_package_purchased",
        "description": "Sent to customer when they purchase a solar package",
        "message_body": """☀️ *Solar Package Purchased!*

Hi {{ customer_name }},

Congratulations on your new solar system! 🎉

Package: {{ package_name }}
System Size: {{ system_size }}kW
Order: {{ order_number }}

*What's Next?*
1. Our team will contact you to schedule installation
2. Site assessment (if required)
3. Installation & commissioning
4. Warranty registration

Your Installation Record: {{ isr_id }}

Questions? Reply to this message anytime.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "package_name",
            "3": "system_size",
            "4": "order_number"
        }
    },
    {
        "name": "hanna_installation_scheduled",
        "description": "Sent to customer when installation is scheduled",
        "message_body": """📅 *Installation Scheduled*

Hi {{ customer_name }},

Your installation has been scheduled!

📍 *Location:* {{ installation_address }}
📆 *Date:* {{ installation_date }}
⏰ *Time:* {{ installation_time }}

*Assigned Technician:* {{ technician_name }}

Please ensure:
- Someone is home on the day
- Roof/installation area is accessible
- Electrical panel is accessible

Need to reschedule? Reply to this message.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "installation_date",
            "3": "technician_name"
        }
    },
    {
        "name": "hanna_installation_complete",
        "description": "Sent to customer when installation is completed",
        "message_body": """✅ *Installation Complete!*

Hi {{ customer_name }},

Your solar system has been successfully installed and commissioned! 🎊

*System Details:*
- Type: {{ installation_type }}
- Size: {{ system_size }}kW
- Installation Record: {{ isr_id }}

*Warranties Registered:*
{{ warranty_summary }}

*Your Client Portal:*
Access your portal at https://hanna.co.zw/client to:
- Monitor your system
- View warranties
- Request service

Thank you for choosing HANNA! ☀️""",
        "body_parameters": {
            "1": "customer_name",
            "2": "installation_type",
            "3": "system_size"
        }
    },
    {
        "name": "hanna_installation_request_new",
        "description": "Sent to admin when new installation request is created",
        "message_body": """📋 *New Installation Request*

Customer: {{ customer_name }}
Phone: {{ customer_phone }}
Type: {{ installation_type }}
Address: {{ installation_address }}

Request ID: {{ installation_request_id }}

Please review and schedule.""",
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
        "name": "hanna_technician_job_assigned",
        "description": "Sent to technician when a new job is assigned",
        "message_body": """🔧 *New Job Assigned*

Hi {{ technician_name }},

You have a new installation assignment:

*Customer:* {{ customer_name }}
*Address:* {{ installation_address }}
*Date:* {{ installation_date }}
*System:* {{ system_size }}kW {{ installation_type }}

Installation ID: {{ isr_id }}

Please confirm your availability.""",
        "body_parameters": {
            "1": "technician_name",
            "2": "customer_name",
            "3": "installation_date"
        }
    },
    {
        "name": "hanna_technician_job_reminder",
        "description": "Reminder sent to technician before scheduled job",
        "message_body": """⏰ *Job Reminder*

Hi {{ technician_name }},

Reminder: You have an installation scheduled for tomorrow.

*Customer:* {{ customer_name }}
*Address:* {{ installation_address }}
*Time:* {{ installation_time }}

Please ensure you have all required equipment and documentation.""",
        "body_parameters": {
            "1": "technician_name",
            "2": "customer_name",
            "3": "installation_time"
        }
    },
    {
        "name": "hanna_payout_approved",
        "description": "Sent to technician when payout is approved",
        "message_body": """💵 *Payout Approved*

Hi {{ technician_name }},

Your payout request *{{ payout_id }}* has been approved!

Amount: ${{ payout_amount }}
Installations: {{ installation_count }}

Payment will be processed shortly.""",
        "body_parameters": {
            "1": "technician_name",
            "2": "payout_id",
            "3": "payout_amount"
        }
    },
    {
        "name": "hanna_payout_paid",
        "description": "Sent to technician when payout is completed",
        "message_body": """✅ *Payment Completed*

Hi {{ technician_name }},

Your payment has been processed!

Payout ID: {{ payout_id }}
Amount: ${{ payout_amount }}
Reference: {{ payment_reference }}

Thank you for your excellent work! 🙏""",
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
        "name": "hanna_warranty_registered",
        "description": "Sent to customer when warranty is registered",
        "message_body": """🛡️ *Warranty Registered*

Hi {{ customer_name }},

Your warranty has been registered:

*Product:* {{ product_name }}
*Serial Number:* {{ serial_number }}
*Valid Until:* {{ warranty_end_date }}

Download your warranty certificate from your client portal.

Need to claim warranty? Contact us anytime.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "product_name",
            "3": "warranty_end_date"
        }
    },
    {
        "name": "hanna_warranty_expiring",
        "description": "Reminder sent when warranty is about to expire",
        "message_body": """⚠️ *Warranty Expiring Soon*

Hi {{ customer_name }},

Your warranty for *{{ product_name }}* will expire on {{ warranty_end_date }}.

Serial Number: {{ serial_number }}

Consider:
- Extended warranty options
- Service check before expiry
- Upgrading your system

Reply to learn about your options.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "product_name",
            "3": "warranty_end_date"
        }
    },
    {
        "name": "hanna_warranty_claim_submitted",
        "description": "Sent to customer when warranty claim is submitted",
        "message_body": """📝 *Warranty Claim Submitted*

Hi {{ customer_name }},

Your warranty claim has been received.

Claim Number: {{ claim_number }}
Product: {{ product_name }}
Issue: {{ reported_issue }}

Our team will review and respond within 2 business days.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "claim_number",
            "3": "product_name"
        }
    },
    {
        "name": "hanna_warranty_claim_approved",
        "description": "Sent to customer when warranty claim is approved",
        "message_body": """✅ *Warranty Claim Approved*

Hi {{ customer_name }},

Your warranty claim *{{ claim_number }}* has been approved!

*Resolution:* {{ resolution_type }}
{{ resolution_notes_section }}

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
        "name": "hanna_service_request_received",
        "description": "Sent to customer when service request is received",
        "message_body": """🔧 *Service Request Received*

Hi {{ customer_name }},

We've received your service request.

Reference: {{ service_request_id }}
Issue: {{ reported_issue }}

Our team will review and contact you within 24 hours.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "service_request_id",
            "3": "reported_issue"
        }
    },
    {
        "name": "hanna_job_card_created",
        "description": "Sent to customer when job card is created",
        "message_body": """📋 *Job Card Created*

Hi {{ customer_name }},

A job card has been created for your service request.

Job Card: {{ job_card_number }}
Product: {{ product_description }}
Issue: {{ reported_fault }}

A technician will be assigned shortly.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "job_card_number",
            "3": "reported_fault"
        }
    },
    {
        "name": "hanna_job_card_completed",
        "description": "Sent to customer when job is completed",
        "message_body": """✅ *Service Completed*

Hi {{ customer_name }},

Your service request has been completed.

Job Card: {{ job_card_number }}
{{ resolution_notes_section }}

Please rate your experience by replying with 1-5 stars ⭐""",
        "body_parameters": {
            "1": "customer_name",
            "2": "job_card_number"
        }
    },

    # ============================================================================
    # ADMIN / SYSTEM TEMPLATES
    # ============================================================================
    {
        "name": "hanna_admin_24h_window_reminder",
        "description": "Reminder to admin about 24-hour messaging window",
        "message_body": """⚠️ *24-Hour Window Expiring*

Contact: {{ contact_name }}
Phone: {{ customer_whatsapp_id }}

The 24-hour messaging window is about to expire. Use a template message to continue the conversation.""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "hanna_message_send_failure",
        "description": "Sent to admin when message sending fails",
        "message_body": """❌ *Message Send Failure*

Failed to send message to {{ contact_name }}.

Please check the conversation and retry or use a template message.""",
        "body_parameters": {
            "1": "contact_name"
        }
    },
    {
        "name": "hanna_human_handover_required",
        "description": "Sent to admin when bot needs human intervention",
        "message_body": """🆘 *Human Handover Requested*

Contact: {{ contact_name }}
Phone: {{ customer_whatsapp_id }}

The customer has requested to speak with a human agent.

Last bot message: {{ last_bot_message }}

Please respond promptly.""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "hanna_low_stock_alert",
        "description": "Alert sent when product stock is low",
        "message_body": """📦 *Low Stock Alert*

Product: {{ product_name }}
SKU: {{ product_sku }}
Current Stock: {{ stock_quantity }}

Please reorder to avoid stockouts.""",
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
        "name": "hanna_branch_order_received",
        "description": "Sent to branch when order is assigned to them",
        "message_body": """📦 *New Order for Your Branch*

Order: {{ order_number }}
Customer: {{ customer_name }}
Amount: ${{ order_amount }}

Please process and dispatch.""",
        "body_parameters": {
            "1": "order_number",
            "2": "customer_name",
            "3": "order_amount"
        }
    },
    {
        "name": "hanna_retailer_commission_earned",
        "description": "Sent to retailer when commission is earned",
        "message_body": """💰 *Commission Earned*

Great news! You've earned a commission.

Order: {{ order_number }}
Sale Amount: ${{ order_amount }}
Commission: ${{ commission_amount }}

Keep up the great work! 🎯""",
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
        "name": "hanna_system_offline_alert",
        "description": "Alert when monitored system goes offline",
        "message_body": """🔴 *System Offline Alert*

Customer: {{ customer_name }}
System: {{ system_type }} - {{ system_size }}kW
Last Seen: {{ last_seen_time }}

Please investigate the issue.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "system_type",
            "3": "last_seen_time"
        }
    },
    {
        "name": "hanna_system_back_online",
        "description": "Notification when system comes back online",
        "message_body": """🟢 *System Back Online*

Customer: {{ customer_name }}
System: {{ system_type }}

The system is now online and functioning normally.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "system_type"
        }
    },

    # ============================================================================
    # PORTAL ACCESS TEMPLATES
    # ============================================================================
    {
        "name": "hanna_portal_access_granted",
        "description": "Sent to customer when portal access is granted",
        "message_body": """🔐 *Portal Access Granted*

Hi {{ customer_name }},

Your client portal access has been set up!

*Portal:* https://hanna.co.zw/client
*Username:* {{ username }}
*Temporary Password:* {{ temp_password }}

Please change your password on first login.

Features available:
- Monitor your system
- View warranties
- Request service
- Download reports""",
        "body_parameters": {
            "1": "customer_name",
            "2": "username",
            "3": "temp_password"
        }
    },
    {
        "name": "hanna_password_reset",
        "description": "Password reset notification",
        "message_body": """🔑 *Password Reset*

Hi {{ customer_name }},

Your password has been reset.

*New Temporary Password:* {{ temp_password }}

Please login and change your password immediately.""",
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
        force_update = options.get('force', False)
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for template_data in NOTIFICATION_TEMPLATES:
            name = template_data['name']
            
            existing = NotificationTemplate.objects.filter(name=name).first()
            
            if existing:
                if force_update:
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
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f'Skipped (exists): {name}')
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
