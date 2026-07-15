"""
Management command to seed notification templates for the HANNA CRM system.

This command creates all the notification templates needed for:
- Order lifecycle notifications
- Installation lifecycle notifications
- Warranty notifications
- Technician notifications
- Customer notifications
- Admin/System notifications
- Invoice processing notifications

Run with: python manage.py seed_notification_templates
"""

from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate


# ============================================================================
# NOTIFICATION TEMPLATES DEFINITIONS
# ============================================================================

# Each template has:
# - name: Unique identifier (used in code to reference the template)
# - category: Template category for organization
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
        "category": "order",
        "description": "Sent to admin staff when a new customer order is created and needs review.",
        "message_body": """📦 *New Order Created*

A new order has been placed and requires your attention.

• *Order #:* {{ order_number }}
• *Customer:* {{ customer_name }}
• *Amount:* ${{ order_amount }}

📋 *Action Required:* Please review and process this order.""",
        "body_parameters": {
            "1": "order_number",
            "2": "customer_name",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_order_confirmation",
        "category": "order",
        "description": "Sent to the customer to confirm their order has been received and is being processed.",
        "message_body": """✅ *Order Confirmed*

Hi {{ customer_name }}, your order has been confirmed!

• *Order #:* {{ order_number }}
• *Total:* ${{ order_amount }}

{{ cart_items_list }}

We're processing your order now. You'll receive updates as it progresses.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_payment_received",
        "category": "order",
        "description": "Sent to the customer to confirm their payment has been received and verified.",
        "message_body": """💰 *Payment Received*

Hi {{ customer_name }}, we've received your payment!

• *Order #:* {{ order_number }}
• *Amount Paid:* ${{ order_amount }}
• *Method:* {{ payment_method }}

Your order is now being processed. Thank you!""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_payment_reminder",
        "category": "order",
        "description": "Friendly reminder sent to customer when payment for their order is still pending.",
        "message_body": """⏳ *Payment Reminder*

Hi {{ customer_name }}, this is a friendly reminder about your pending payment.

• *Order #:* {{ order_number }}
• *Amount Due:* ${{ order_amount }}

Please complete your payment so we can proceed with your order. If you've already paid, please disregard this message.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_order_dispatched",
        "category": "order",
        "description": "Sent to the customer when their order has been shipped/dispatched for delivery.",
        "message_body": """🚚 *Order Dispatched*

Hi {{ customer_name }}, your order is on its way!

• *Order #:* {{ order_number }}
• *Estimated Delivery:* {{ delivery_date }}
{{ tracking_info }}

You'll be notified when delivery is complete.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "delivery_date"
        }
    },
    {
        "name": "pfungwa_new_online_order_placed",
        "category": "order",
        "description": "Sent to admin staff when a customer places an order online through the WhatsApp flow.",
        "message_body": """🛒 *New Online Order Placed*

A customer has placed an order via WhatsApp.

• *Customer:* {{ customer_name }}
• *Order #:* {{ order_number }}
• *Amount:* ${{ order_amount }}

📋 *Action Required:* Review and confirm the order.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_new_placeholder_order_created",
        "category": "order",
        "description": "Sent to admin when a placeholder order is auto-created during a flow (e.g., inquiry).",
        "message_body": """📝 *Placeholder Order Created*

A placeholder order has been auto-generated.

• *Customer:* {{ customer_name }}
• *Order #:* {{ order_number }}
• *Notes:* {{ order_notes }}

📋 *Action Required:* Review and update order details.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_notes"
        }
    },
    {
        "name": "pfungwa_order_payment_status_updated",
        "category": "order",
        "description": "Sent to the customer when the payment status of their order is updated by admin.",
        "message_body": """💳 *Payment Status Updated*

Hi {{ customer_name }}, the payment status for your order has been updated.

• *Order #:* {{ order_number }}
• *New Status:* {{ new_status }}

If you have any questions, please reach out to us.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "new_status"
        }
    },

    # ============================================================================
    # SOLAR PACKAGE / INSTALLATION TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_solar_package_purchased",
        "category": "installation",
        "description": "Sent to the customer when they purchase a solar package, outlining next steps.",
        "message_body": """☀️ *Solar Package Purchased*

Hi {{ customer_name }}, thank you for choosing us for your solar installation!

• *Package:* {{ package_name }}
• *System Size:* {{ system_size }}kW
• *Order #:* {{ order_number }}
• *Installation Record:* {{ isr_id }}

*What happens next:*
1️⃣ Our team will contact you to schedule installation
2️⃣ A site assessment will be arranged
3️⃣ Installation and system commissioning
4️⃣ Warranty registration for all components""",
        "body_parameters": {
            "1": "customer_name",
            "2": "package_name",
            "3": "system_size"
        }
    },
    {
        "name": "pfungwa_installation_scheduled",
        "category": "installation",
        "description": "Sent to the customer to confirm their installation date, time, and assigned technician.",
        "message_body": """📅 *Installation Scheduled*

Hi {{ customer_name }}, your installation has been scheduled!

• *Location:* {{ installation_address }}
• *Date:* {{ installation_date }}
• *Time:* {{ installation_time }}
• *Technician:* {{ technician_name }}

*Please prepare:*
✅ Ensure someone is present at the property
✅ Roof/installation area must be accessible
✅ Electrical panel must be accessible""",
        "body_parameters": {
            "1": "customer_name",
            "2": "installation_date",
            "3": "technician_name"
        }
    },
    {
        "name": "pfungwa_installation_complete",
        "category": "installation",
        "description": "Sent to the customer when their installation is complete, including warranty and portal info.",
        "message_body": """🎉 *Installation Complete*

Hi {{ customer_name }}, your installation has been successfully completed!

• *System:* {{ installation_type }}
• *Size:* {{ system_size }}kW
• *Record:* {{ isr_id }}

{{ warranty_summary }}

🌐 *Access your portal:* https://hanna.co.zw/client
• Monitor your system performance
• View warranty certificates
• Request maintenance or service""",
        "body_parameters": {
            "1": "customer_name",
            "2": "installation_type",
            "3": "system_size"
        }
    },
    {
        "name": "pfungwa_installation_request_new",
        "category": "installation",
        "description": "Sent to admin staff when a new installation request is submitted by a customer.",
        "message_body": """🔧 *New Installation Request*

A customer has requested an installation.

• *Customer:* {{ customer_name }}
• *Phone:* {{ customer_phone }}
• *Type:* {{ installation_type }}
• *Address:* {{ installation_address }}
• *Request ID:* {{ installation_request_id }}

📋 *Action Required:* Schedule the installation.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "installation_type",
            "3": "installation_request_id"
        }
    },
    {
        "name": "pfungwa_new_installation_request",
        "category": "installation",
        "description": "Generic notification sent to admin for any new installation request from a WhatsApp flow.",
        "message_body": """🔧 *New Installation Request*

A new installation request has been submitted.

• *Customer:* {{ customer_name }}
• *Phone:* {{ install_phone }}
• *Type:* {{ install_kit_type }}
• *Address:* {{ install_address }}
{{ install_alt_contact_line }}
{{ install_location_pin_line }}
• *Preferred Date:* {{ install_preferred_date }}
• *Availability:* {{ install_availability }}

📋 *Action Required:* Review and schedule.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "install_phone",
            "3": "install_kit_type"
        }
    },
    {
        "name": "pfungwa_new_starlink_installation_request",
        "category": "installation",
        "description": "Sent to admin when a customer requests a Starlink installation.",
        "message_body": """📡 *New Starlink Installation Request*

A customer has requested a Starlink installation.

• *Customer:* {{ customer_name }}
• *Phone:* {{ install_phone }}
• *Address:* {{ install_address }}
{{ install_alt_contact_line }}
{{ install_location_pin_line }}
• *Preferred Date:* {{ install_preferred_date }}
• *Availability:* {{ install_availability }}

📋 *Action Required:* Review and schedule installation.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "install_phone",
            "3": "install_address"
        }
    },
    {
        "name": "pfungwa_new_hybrid_installation_request",
        "category": "installation",
        "description": "Sent to admin when a customer requests a hybrid (solar + starlink) installation.",
        "message_body": """⚡📡 *New Hybrid Installation Request*

A customer has requested a hybrid Solar + Starlink installation.

• *Customer:* {{ customer_name }}
• *Phone:* {{ install_phone }}
• *Kit Type:* {{ install_kit_type }}
• *Address:* {{ install_address }}
{{ install_alt_contact_line }}
{{ install_location_pin_line }}
• *Preferred Date:* {{ install_preferred_date }}
• *Availability:* {{ install_availability }}

📋 *Action Required:* Review and schedule.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "install_phone",
            "3": "install_kit_type"
        }
    },
    {
        "name": "pfungwa_new_custom_furniture_installation_request",
        "category": "installation",
        "description": "Sent to admin when a customer requests a custom furniture installation.",
        "message_body": """🪑 *New Custom Furniture Installation Request*

A customer has requested a custom furniture installation.

• *Customer:* {{ contact_name }}
• *Order #:* {{ furniture_order_number }}
• *Type:* {{ furniture_type }}
• *Specs:* {{ furniture_specifications }}
• *Name:* {{ furniture_full_name }}
• *Phone:* {{ furniture_contact_phone }}
{{ furniture_alt_contact_line }}
• *Address:* {{ furniture_address }}
{{ furniture_location_pin_line }}
• *Preferred Date:* {{ furniture_preferred_date }}
• *Availability:* {{ furniture_availability }}

📋 *Action Required:* Review and schedule.""",
        "body_parameters": {
            "1": "contact_name",
            "2": "furniture_type",
            "3": "furniture_full_name"
        }
    },
    {
        "name": "pfungwa_new_furniture_installation_request",
        "category": "installation",
        "description": "Sent to admin when a general furniture installation request is submitted.",
        "message_body": """🪑 *New Furniture Installation Request*

A new furniture installation request has been submitted.

• *Customer:* {{ customer_name }}
• *Phone:* {{ install_phone }}
• *Address:* {{ install_address }}
{{ install_alt_contact_line }}
{{ install_location_pin_line }}
• *Preferred Date:* {{ install_preferred_date }}

📋 *Action Required:* Review and schedule.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "install_phone",
            "3": "install_address"
        }
    },
    {
        "name": "pfungwa_admin_order_and_install_created",
        "category": "installation",
        "description": "Sent to admin when both an order and installation request are created together.",
        "message_body": """📦🔧 *Order & Installation Created*

A new order with an installation request has been created.

• *Customer:* {{ customer_name }}
• *Order #:* {{ order_number }}
• *Amount:* ${{ order_amount }}
• *Installation Type:* {{ installation_type }}

📋 *Action Required:* Review order and schedule installation.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "order_amount"
        }
    },

    # ============================================================================
    # SITE ASSESSMENT / CLEANING TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_new_site_assessment_request",
        "category": "installation",
        "description": "Sent to admin when a customer requests a site assessment before installation.",
        "message_body": """📍 *New Site Assessment Request*

A customer has requested a site assessment.

• *Customer:* {{ customer_name }}
• *Phone:* {{ assess_phone }}
• *Address:* {{ assess_address }}
• *Assessment #:* {{ assessment_number }}
{{ assess_location_pin_line }}
• *Preferred Date:* {{ assess_preferred_date }}

📋 *Action Required:* Schedule the site assessment.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "assess_phone",
            "3": "assessment_number"
        }
    },
    {
        "name": "pfungwa_assessment_status_updated",
        "category": "installation",
        "description": "Sent to the customer when the status of their site assessment is updated.",
        "message_body": """📍 *Assessment Status Updated*

Hi {{ customer_name }}, your site assessment status has been updated.

• *Assessment #:* {{ assessment_number }}
• *New Status:* {{ new_status }}

Our team will keep you informed of the next steps.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "assessment_number",
            "3": "new_status"
        }
    },
    {
        "name": "pfungwa_new_solar_cleaning_request",
        "category": "installation",
        "description": "Sent to admin when a customer requests solar panel cleaning.",
        "message_body": """🧹 *New Solar Panel Cleaning Request*

A customer has requested solar panel cleaning.

• *Customer:* {{ customer_name }}
• *Phone:* {{ cleaning_phone }}
• *Address:* {{ cleaning_address }}
• *Roof Type:* {{ cleaning_roof_type }}
• *Panel Type:* {{ cleaning_panel_type }}
{{ cleaning_location_pin_line }}
• *Preferred Date:* {{ cleaning_preferred_date }}
• *Availability:* {{ cleaning_availability }}

📋 *Action Required:* Schedule the cleaning service.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "cleaning_phone",
            "3": "cleaning_address"
        }
    },

    # ============================================================================
    # LOAN APPLICATION TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_new_loan_application",
        "category": "order",
        "description": "Sent to admin when a customer submits a loan/financing application.",
        "message_body": """🏦 *New Loan Application*

A customer has submitted a financing application.

• *Customer:* {{ customer_name }}
• *Loan Type:* {{ loan_type }}
• *Employment:* {{ loan_employment_status }}
{{ loan_amount_line }}
{{ loan_product_line }}

📋 *Action Required:* Review the application.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "loan_type",
            "3": "loan_employment_status"
        }
    },

    # ============================================================================
    # TECHNICIAN TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_technician_job_assigned",
        "category": "technician",
        "description": "Sent to a technician when a new installation job is assigned to them.",
        "message_body": """👷 *New Job Assigned to You*

Hi {{ technician_name }}, you've been assigned a new job.

• *Customer:* {{ customer_name }}
• *Address:* {{ installation_address }}
• *Date:* {{ installation_date }}
• *System:* {{ system_size }}kW {{ installation_type }}
• *Installation ID:* {{ isr_id }}

📋 *Action Required:* Please confirm your availability.""",
        "body_parameters": {
            "1": "technician_name",
            "2": "customer_name",
            "3": "installation_date"
        }
    },
    {
        "name": "pfungwa_technician_job_reminder",
        "category": "technician",
        "description": "Reminder sent to technician the day before a scheduled installation.",
        "message_body": """⏰ *Job Reminder — Tomorrow*

Hi {{ technician_name }}, you have a scheduled job tomorrow.

• *Customer:* {{ customer_name }}
• *Address:* {{ installation_address }}
• *Time:* {{ installation_time }}

✅ Please ensure all equipment and documentation are ready.""",
        "body_parameters": {
            "1": "technician_name",
            "2": "customer_name",
            "3": "installation_time"
        }
    },
    {
        "name": "pfungwa_payout_approved",
        "category": "technician",
        "description": "Sent to a technician when their installation payout has been approved.",
        "message_body": """✅ *Payout Approved*

Hi {{ technician_name }}, your payout has been approved!

• *Payout ID:* {{ payout_id }}
• *Amount:* ${{ payout_amount }}
• *Installations:* {{ installation_count }}

Payment will be processed shortly.""",
        "body_parameters": {
            "1": "technician_name",
            "2": "payout_id",
            "3": "payout_amount"
        }
    },
    {
        "name": "pfungwa_payout_paid",
        "category": "technician",
        "description": "Sent to a technician when their payout has been processed and payment completed.",
        "message_body": """💵 *Payment Completed*

Hi {{ technician_name }}, your payment has been processed!

• *Payout ID:* {{ payout_id }}
• *Amount:* ${{ payout_amount }}
• *Reference:* {{ payment_reference }}

Thank you for your work!""",
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
        "category": "warranty",
        "description": "Sent to the customer when a product warranty is successfully registered.",
        "message_body": """🛡️ *Warranty Registered*

Hi {{ customer_name }}, your warranty has been successfully registered.

• *Product:* {{ product_name }}
• *Serial #:* {{ serial_number }}
• *Valid Until:* {{ warranty_end_date }}

Your warranty certificate is available in the client portal.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "product_name",
            "3": "warranty_end_date"
        }
    },
    {
        "name": "pfungwa_warranty_expiring",
        "category": "warranty",
        "description": "Proactive reminder sent when a customer's warranty is nearing its expiry date.",
        "message_body": """⚠️ *Warranty Expiring Soon*

Hi {{ customer_name }}, your warranty is expiring soon.

• *Product:* {{ product_name }}
• *Serial #:* {{ serial_number }}
• *Expires:* {{ warranty_end_date }}

Consider the following before it expires:
• Extended warranty options
• Service check-up
• System upgrades""",
        "body_parameters": {
            "1": "customer_name",
            "2": "product_name",
            "3": "warranty_end_date"
        }
    },
    {
        "name": "pfungwa_warranty_claim_submitted",
        "category": "warranty",
        "description": "Sent to the customer confirming their warranty claim has been submitted for review.",
        "message_body": """📝 *Warranty Claim Submitted*

Hi {{ customer_name }}, we've received your warranty claim.

• *Claim #:* {{ claim_number }}
• *Product:* {{ product_name }}
• *Issue:* {{ reported_issue }}

Our team will review your claim. You can expect a response within 2 business days.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "claim_number",
            "3": "product_name"
        }
    },
    {
        "name": "pfungwa_warranty_claim_approved",
        "category": "warranty",
        "description": "Sent to the customer when their warranty claim has been approved and resolution determined.",
        "message_body": """✅ *Warranty Claim Approved*

Hi {{ customer_name }}, your warranty claim has been approved!

• *Claim #:* {{ claim_number }}
• *Product:* {{ product_name }}
• *Resolution:* {{ resolution_type }}
{{ resolution_notes_section }}

We'll be in touch with next steps.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "claim_number",
            "3": "resolution_type"
        }
    },
    {
        "name": "pfungwa_new_warranty_claim_submitted",
        "category": "warranty",
        "description": "Sent to admin staff when a customer submits a new warranty claim for review.",
        "message_body": """🛡️ *New Warranty Claim Submitted*

A customer has submitted a warranty claim.

• *Customer:* {{ customer_name }}
• *Claim #:* {{ claim_number }}
• *Product:* {{ product_name }}
• *Issue:* {{ reported_issue }}

📋 *Action Required:* Review and respond to the claim.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "claim_number",
            "3": "product_name"
        }
    },
    {
        "name": "pfungwa_warranty_claim_status_updated",
        "category": "warranty",
        "description": "Sent to the customer when the status of their warranty claim changes.",
        "message_body": """🛡️ *Warranty Claim Updated*

Hi {{ customer_name }}, the status of your warranty claim has been updated.

• *Claim #:* {{ claim_number }}
• *New Status:* {{ claim_status }}
{{ resolution_notes_section }}

We'll keep you informed of any further updates.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "claim_number",
            "3": "claim_status"
        }
    },

    # ============================================================================
    # SERVICE / JOB CARD TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_service_request_received",
        "category": "service",
        "description": "Sent to the customer to confirm a service/repair request has been received.",
        "message_body": """📩 *Service Request Received*

Hi {{ customer_name }}, we've received your service request.

• *Reference:* {{ service_request_id }}
• *Issue:* {{ reported_issue }}

Our team will contact you within 24 hours to discuss next steps.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "service_request_id",
            "3": "reported_issue"
        }
    },
    {
        "name": "pfungwa_job_card_created",
        "category": "service",
        "description": "Sent to the customer when a job card is created for their service request.",
        "message_body": """🔧 *Job Card Created*

Hi {{ customer_name }}, a job card has been created for your service request.

• *Job Card #:* {{ job_card_number }}
• *Product:* {{ product_description }}
• *Issue:* {{ reported_fault }}

A technician will be assigned shortly.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "job_card_number",
            "3": "reported_fault"
        }
    },
    {
        "name": "pfungwa_job_card_completed",
        "category": "service",
        "description": "Sent to the customer when their service/repair job has been completed.",
        "message_body": """✅ *Service Completed*

Hi {{ customer_name }}, your service job has been completed!

• *Job Card #:* {{ job_card_number }}
{{ resolution_notes_section }}

We appreciate your business. Your feedback is welcome!""",
        "body_parameters": {
            "1": "customer_name",
            "2": "job_card_number"
        }
    },
    {
        "name": "pfungwa_job_card_created_successfully",
        "category": "service",
        "description": "Sent to admin staff when a job card is auto-created from an invoice email.",
        "message_body": """🔧 *Job Card Auto-Created*

A job card was automatically created from an email invoice.

• *Job Card #:* {{ job_card_number }}
• *Product:* {{ product_description }}
• *Serial #:* {{ product_serial_number }}
• *Issue:* {{ reported_fault }}

📋 *Action Required:* Review and assign a technician.""",
        "body_parameters": {
            "1": "job_card_number",
            "2": "product_description",
            "3": "reported_fault"
        }
    },

    # ============================================================================
    # INVOICE PROCESSING TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_invoice_processed_successfully",
        "category": "invoice",
        "description": "Sent to admin staff when an email invoice has been automatically parsed and processed.",
        "message_body": """📄 *Invoice Processed Successfully*

An email invoice has been automatically processed.

• *From:* {{ sender }}
• *File:* {{ filename }}
• *Order #:* {{ order_number }}
• *Amount:* ${{ order_amount }}
• *Customer:* {{ customer_name }}

The order has been created and linked to the customer profile.""",
        "body_parameters": {
            "1": "sender",
            "2": "order_number",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_customer_invoice_confirmation",
        "category": "invoice",
        "description": "Sent to the customer confirming their invoice has been received and an order created.",
        "message_body": """📄 *Invoice Confirmation*

Hi {{ customer_name }}, we've received and processed your invoice.

• *Order #:* {{ order_number }}
• *Total:* ${{ total_amount }}
• *Date:* {{ invoice_date }}

If you have any questions about this invoice, please reach out to us.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "order_number",
            "3": "total_amount"
        }
    },

    # ============================================================================
    # ADMIN / SYSTEM TEMPLATES
    # ============================================================================
    {
        "name": "pfungwa_admin_24h_window_reminder",
        "category": "admin",
        "description": "Reminder sent to admin agents when the 24-hour WhatsApp messaging window is about to close.",
        "message_body": """⏰ *24-Hour Messaging Window Expiring*

The messaging window for a contact is about to expire.

• *Contact:* {{ contact_name }}
• *Phone:* {{ customer_whatsapp_id }}

📋 *Action Required:* Send a template message to keep the conversation active, or the window will close.""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "pfungwa_message_send_failure",
        "category": "admin",
        "description": "Alert sent to admin when a WhatsApp message fails to deliver after all retries.",
        "message_body": """❌ *Message Delivery Failed*

A WhatsApp message could not be delivered.

• *Contact:* {{ contact_name }}
• *Phone:* {{ customer_whatsapp_id }}

📋 *Action Required:* Check the conversation and retry, or send a template message.""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "pfungwa_human_handover_required",
        "category": "admin",
        "description": "Alert sent to admin when a customer requests to speak with a human agent.",
        "message_body": """🙋 *Human Agent Requested*

A customer has requested to speak with a human agent.

• *Contact:* {{ contact_name }}
• *Phone:* {{ customer_whatsapp_id }}
• *Last Bot Message:* {{ last_bot_message }}

📋 *Action Required:* Please respond promptly to this customer.""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "pfungwa_human_handover_flow",
        "category": "admin",
        "description": "Alert sent to admin team when the bot triggers a human handover due to customer need or error.",
        "message_body": """🙋 *Human Handover Triggered*

The bot has flagged a conversation for human attention.

• *Contact:* {{ contact_name }}
• *Phone:* {{ customer_whatsapp_id }}
• *Reason:* {{ last_bot_message }}

📋 *Action Required:* Take over this conversation.""",
        "body_parameters": {
            "1": "contact_name",
            "2": "customer_whatsapp_id"
        }
    },
    {
        "name": "pfungwa_low_stock_alert",
        "category": "admin",
        "description": "Alert sent to inventory managers when a product's stock falls below the reorder threshold.",
        "message_body": """📉 *Low Stock Alert*

A product is running low on stock and may need reordering.

• *Product:* {{ product_name }}
• *SKU:* {{ product_sku }}
• *Current Stock:* {{ stock_quantity }}

📋 *Action Required:* Reorder to avoid stockouts.""",
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
        "category": "retailer",
        "description": "Sent to a retailer branch when a new order is assigned to them for fulfillment.",
        "message_body": """📦 *New Order Assigned to Your Branch*

A new order has been assigned for processing.

• *Order #:* {{ order_number }}
• *Customer:* {{ customer_name }}
• *Amount:* ${{ order_amount }}

📋 *Action Required:* Process and prepare for dispatch.""",
        "body_parameters": {
            "1": "order_number",
            "2": "customer_name",
            "3": "order_amount"
        }
    },
    {
        "name": "pfungwa_retailer_commission_earned",
        "category": "retailer",
        "description": "Sent to a retailer when they earn a commission from a sale.",
        "message_body": """💰 *Commission Earned*

You've earned a commission on a sale!

• *Order #:* {{ order_number }}
• *Sale Amount:* ${{ order_amount }}
• *Your Commission:* ${{ commission_amount }}

The commission has been recorded in the system.""",
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
        "category": "monitoring",
        "description": "Alert sent when a monitored solar/energy system goes offline unexpectedly.",
        "message_body": """🔴 *System Offline*

A monitored system has gone offline.

• *Customer:* {{ customer_name }}
• *System:* {{ system_type }} — {{ system_size }}kW
• *Last Seen:* {{ last_seen_time }}

📋 *Action Required:* Investigate the cause of the outage.""",
        "body_parameters": {
            "1": "customer_name",
            "2": "system_type",
            "3": "last_seen_time"
        }
    },
    {
        "name": "pfungwa_system_back_online",
        "category": "monitoring",
        "description": "Notification sent when a previously offline system comes back online.",
        "message_body": """🟢 *System Back Online*

A previously offline system is now back online.

• *Customer:* {{ customer_name }}
• *System:* {{ system_type }}

The system has been restored and is functioning normally.""",
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
        "category": "portal",
        "description": "Sent to the customer when their client portal account is created.",
        "message_body": """🌐 *Portal Access Granted*

Hi {{ customer_name }}, your client portal account has been created!

• *Portal:* https://hanna.co.zw/client
• *Username:* {{ username }}
• *Temporary Password:* {{ temp_password }}

⚠️ Please change your password on first login.

*Available features:*
• System monitoring dashboard
• Warranty management
• Service request submission
• Document access""",
        "body_parameters": {
            "1": "customer_name",
            "2": "username",
            "3": "temp_password"
        }
    },
    {
        "name": "pfungwa_password_reset",
        "category": "portal",
        "description": "Sent to a user when their portal password is reset by an admin.",
        "message_body": """🔑 *Password Reset*

Hi {{ customer_name }}, your password has been reset.

• *Temporary Password:* {{ temp_password }}

⚠️ Please log in and change your password immediately for security.""",
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
                existing.category = template_data.get('category', 'other')
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
                    category=template_data.get('category', 'other'),
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
