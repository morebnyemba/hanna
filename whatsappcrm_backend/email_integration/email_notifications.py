"""
Email notification services for the HANNA CRM system.

This module provides functions to send email notifications using templates.
It supports both HTML and plain text emails with template rendering.
"""

import logging
from typing import Optional, Dict, List, Any
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.template.loader import render_to_string
from django.conf import settings

from .smtp_utils import get_smtp_connection, get_from_email
from notifications.models import NotificationTemplate

logger = logging.getLogger(__name__)


# ============================================================================
# EMAIL TEMPLATES (HTML)
# ============================================================================

EMAIL_TEMPLATES = {
    # Order confirmation email
    'order_confirmation': {
        'subject': 'Order Confirmation - {{ order_number }}',
        'html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f7931e; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        .button { background-color: #f7931e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }
        .order-details { background-color: white; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .highlight { color: #f7931e; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>☀️ HANNA Solar</h1>
            <h2>Order Confirmation</h2>
        </div>
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            <p>Thank you for your order! We're excited to help you go solar. 🌟</p>
            
            <div class="order-details">
                <h3>Order Details</h3>
                <p><strong>Order Number:</strong> <span class="highlight">{{ order_number }}</span></p>
                <p><strong>Amount:</strong> ${{ order_amount }}</p>
                <p><strong>Payment Status:</strong> {{ payment_status }}</p>
            </div>
            
            <h3>What's Next?</h3>
            <ol>
                <li>Our team will review your order</li>
                <li>We'll contact you to schedule installation</li>
                <li>Site assessment (if required)</li>
                <li>Installation & commissioning</li>
                <li>Warranty registration</li>
            </ol>
            
            <p style="text-align: center; margin-top: 30px;">
                <a href="https://hanna.co.zw/client" class="button">View Your Order</a>
            </p>
        </div>
        <div class="footer">
            <p>HANNA Solar Solutions<br>
            📧 support@hanna.co.zw | 📞 +263 123 456 789</p>
            <p>© 2024 HANNA. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
''',
        'plain': '''
HANNA Solar - Order Confirmation

Hi {{ customer_name }},

Thank you for your order! We're excited to help you go solar.

ORDER DETAILS
-------------
Order Number: {{ order_number }}
Amount: ${{ order_amount }}
Payment Status: {{ payment_status }}

WHAT'S NEXT?
1. Our team will review your order
2. We'll contact you to schedule installation
3. Site assessment (if required)
4. Installation & commissioning
5. Warranty registration

View your order: https://hanna.co.zw/client

HANNA Solar Solutions
support@hanna.co.zw | +263 123 456 789
'''
    },
    
    # Installation scheduled email
    'installation_scheduled': {
        'subject': 'Installation Scheduled - {{ installation_date }}',
        'html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        .details-box { background-color: white; padding: 15px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #28a745; }
        .checklist { background-color: #fff3cd; padding: 15px; border-radius: 4px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Installation Scheduled</h1>
        </div>
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            <p>Great news! Your solar installation has been scheduled.</p>
            
            <div class="details-box">
                <h3>📍 Installation Details</h3>
                <p><strong>Date:</strong> {{ installation_date }}</p>
                <p><strong>Time:</strong> {{ installation_time }}</p>
                <p><strong>Address:</strong> {{ installation_address }}</p>
                <p><strong>Technician:</strong> {{ technician_name }}</p>
            </div>
            
            <div class="checklist">
                <h3>✅ Please Ensure:</h3>
                <ul>
                    <li>Someone is home on the installation day</li>
                    <li>Roof/installation area is accessible</li>
                    <li>Electrical panel is accessible</li>
                    <li>Pets are secured if necessary</li>
                </ul>
            </div>
            
            <p>Need to reschedule? Contact us at least 24 hours before the scheduled date.</p>
        </div>
        <div class="footer">
            <p>HANNA Solar Solutions<br>
            📧 support@hanna.co.zw | 📞 +263 123 456 789</p>
        </div>
    </div>
</body>
</html>
''',
        'plain': '''
HANNA Solar - Installation Scheduled

Hi {{ customer_name }},

Great news! Your solar installation has been scheduled.

INSTALLATION DETAILS
--------------------
Date: {{ installation_date }}
Time: {{ installation_time }}
Address: {{ installation_address }}
Technician: {{ technician_name }}

PLEASE ENSURE:
- Someone is home on the installation day
- Roof/installation area is accessible
- Electrical panel is accessible
- Pets are secured if necessary

Need to reschedule? Contact us at least 24 hours before.

HANNA Solar Solutions
support@hanna.co.zw | +263 123 456 789
'''
    },
    
    # Installation complete email
    'installation_complete': {
        'subject': 'Installation Complete - Welcome to Solar! ☀️',
        'html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        .button { background-color: #f7931e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }
        .system-info { background-color: white; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .warranty-box { background-color: #d4edda; padding: 15px; border-radius: 4px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Congratulations!</h1>
            <h2>Your Solar System is Live!</h2>
        </div>
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            <p>Your solar system has been successfully installed and commissioned! Welcome to clean energy! ☀️</p>
            
            <div class="system-info">
                <h3>🔋 System Details</h3>
                <p><strong>Type:</strong> {{ installation_type }}</p>
                <p><strong>Size:</strong> {{ system_size }}kW</p>
                <p><strong>Installation Record:</strong> {{ isr_id }}</p>
            </div>
            
            <div class="warranty-box">
                <h3>🛡️ Warranty Coverage</h3>
                <p>{{ warranty_summary }}</p>
            </div>
            
            <h3>Your Client Portal</h3>
            <p>Access your portal to:</p>
            <ul>
                <li>Monitor your system performance</li>
                <li>View warranty certificates</li>
                <li>Request service</li>
                <li>Download reports</li>
            </ul>
            
            <p style="text-align: center; margin-top: 30px;">
                <a href="https://hanna.co.zw/client" class="button">Access Your Portal</a>
            </p>
        </div>
        <div class="footer">
            <p>Thank you for choosing HANNA Solar! 🌟<br>
            📧 support@hanna.co.zw | 📞 +263 123 456 789</p>
        </div>
    </div>
</body>
</html>
''',
        'plain': '''
HANNA Solar - Installation Complete!

Congratulations {{ customer_name }}!

Your solar system has been successfully installed and commissioned!

SYSTEM DETAILS
--------------
Type: {{ installation_type }}
Size: {{ system_size }}kW
Installation Record: {{ isr_id }}

WARRANTY COVERAGE
-----------------
{{ warranty_summary }}

ACCESS YOUR PORTAL
------------------
https://hanna.co.zw/client

- Monitor your system performance
- View warranty certificates
- Request service
- Download reports

Thank you for choosing HANNA Solar!
support@hanna.co.zw | +263 123 456 789
'''
    },
    
    # Warranty registered email
    'warranty_registered': {
        'subject': 'Warranty Registered - {{ product_name }}',
        'html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #17a2b8; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        .warranty-card { background-color: white; padding: 20px; border-radius: 8px; margin: 15px 0; border: 2px solid #17a2b8; }
        .button { background-color: #17a2b8; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Warranty Registered</h1>
        </div>
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            <p>Your product warranty has been successfully registered.</p>
            
            <div class="warranty-card">
                <h3>Warranty Details</h3>
                <p><strong>Product:</strong> {{ product_name }}</p>
                <p><strong>Serial Number:</strong> {{ serial_number }}</p>
                <p><strong>Manufacturer:</strong> {{ manufacturer_name }}</p>
                <p><strong>Valid From:</strong> {{ warranty_start_date }}</p>
                <p><strong>Valid Until:</strong> {{ warranty_end_date }}</p>
            </div>
            
            <p>Keep your serial number safe - you'll need it for any warranty claims.</p>
            
            <p style="text-align: center; margin-top: 30px;">
                <a href="https://hanna.co.zw/client/warranties" class="button">Download Certificate</a>
            </p>
        </div>
        <div class="footer">
            <p>HANNA Solar Solutions<br>
            📧 support@hanna.co.zw | 📞 +263 123 456 789</p>
        </div>
    </div>
</body>
</html>
''',
        'plain': '''
HANNA Solar - Warranty Registered

Hi {{ customer_name }},

Your product warranty has been successfully registered.

WARRANTY DETAILS
----------------
Product: {{ product_name }}
Serial Number: {{ serial_number }}
Manufacturer: {{ manufacturer_name }}
Valid From: {{ warranty_start_date }}
Valid Until: {{ warranty_end_date }}

Keep your serial number safe - you'll need it for any warranty claims.

Download Certificate: https://hanna.co.zw/client/warranties

HANNA Solar Solutions
support@hanna.co.zw | +263 123 456 789
'''
    },
    
    # Portal access email
    'portal_access': {
        'subject': 'Your HANNA Portal Access',
        'html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6c757d; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        .credentials { background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 15px 0; border: 2px dashed #856404; }
        .button { background-color: #f7931e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }
        .warning { background-color: #f8d7da; padding: 10px; border-radius: 4px; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Portal Access</h1>
        </div>
        <div class="content">
            <p>Hi <strong>{{ customer_name }}</strong>,</p>
            <p>Your HANNA client portal access has been set up!</p>
            
            <div class="credentials">
                <h3>🔑 Your Login Credentials</h3>
                <p><strong>Portal URL:</strong> https://hanna.co.zw/client</p>
                <p><strong>Username:</strong> {{ username }}</p>
                <p><strong>Temporary Password:</strong> {{ temp_password }}</p>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important:</strong> Please change your password immediately after your first login.
            </div>
            
            <h3>What You Can Do:</h3>
            <ul>
                <li>📊 Monitor your system performance</li>
                <li>🛡️ View and download warranty certificates</li>
                <li>🔧 Request service and support</li>
                <li>📄 Download installation reports</li>
            </ul>
            
            <p style="text-align: center; margin-top: 30px;">
                <a href="https://hanna.co.zw/client/login" class="button">Login Now</a>
            </p>
        </div>
        <div class="footer">
            <p>HANNA Solar Solutions<br>
            📧 support@hanna.co.zw | 📞 +263 123 456 789</p>
        </div>
    </div>
</body>
</html>
''',
        'plain': '''
HANNA Solar - Portal Access

Hi {{ customer_name }},

Your HANNA client portal access has been set up!

LOGIN CREDENTIALS
-----------------
Portal URL: https://hanna.co.zw/client
Username: {{ username }}
Temporary Password: {{ temp_password }}

⚠️ IMPORTANT: Please change your password immediately after your first login.

WHAT YOU CAN DO:
- Monitor your system performance
- View and download warranty certificates
- Request service and support
- Download installation reports

Login now: https://hanna.co.zw/client/login

HANNA Solar Solutions
support@hanna.co.zw | +263 123 456 789
'''
    },
    
    # Payout notification for technicians
    'technician_payout': {
        'subject': 'Payout {{ payout_status }}: {{ payout_id }}',
        'html': '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        .payout-card { background-color: white; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #28a745; }
        .amount { font-size: 32px; color: #28a745; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Payout {{ payout_status }}</h1>
        </div>
        <div class="content">
            <p>Hi <strong>{{ technician_name }}</strong>,</p>
            <p>{{ payout_message }}</p>
            
            <div class="payout-card">
                <p class="amount">${{ payout_amount }}</p>
                <p><strong>Payout ID:</strong> {{ payout_id }}</p>
                <p><strong>Installations:</strong> {{ installation_count }}</p>
                {% if payment_reference %}
                <p><strong>Payment Reference:</strong> {{ payment_reference }}</p>
                {% endif %}
            </div>
            
            <p>Thank you for your excellent work! 🙏</p>
        </div>
        <div class="footer">
            <p>HANNA Solar Solutions<br>
            📧 support@hanna.co.zw</p>
        </div>
    </div>
</body>
</html>
''',
        'plain': '''
HANNA Solar - Payout {{ payout_status }}

Hi {{ technician_name }},

{{ payout_message }}

PAYOUT DETAILS
--------------
Amount: ${{ payout_amount }}
Payout ID: {{ payout_id }}
Installations: {{ installation_count }}
{% if payment_reference %}Payment Reference: {{ payment_reference }}{% endif %}

Thank you for your excellent work!

HANNA Solar Solutions
support@hanna.co.zw
'''
    },
}


def render_email_template(template_name: str, context: Dict[str, Any]) -> tuple:
    """
    Render an email template with the given context.
    
    Args:
        template_name: Name of the template from EMAIL_TEMPLATES
        context: Dictionary of context variables
        
    Returns:
        Tuple of (subject, html_body, plain_body)
    """
    if template_name not in EMAIL_TEMPLATES:
        raise ValueError(f"Email template '{template_name}' not found")
    
    template_data = EMAIL_TEMPLATES[template_name]
    
    # Render subject
    subject_template = Template(template_data['subject'])
    subject = subject_template.render(Context(context))
    
    # Render HTML body
    html_template = Template(template_data['html'])
    html_body = html_template.render(Context(context))
    
    # Render plain text body
    plain_template = Template(template_data['plain'])
    plain_body = plain_template.render(Context(context))
    
    return subject, html_body, plain_body


def send_email_notification(
    template_name: str,
    recipient_email: str,
    context: Dict[str, Any],
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
) -> bool:
    """
    Send an email notification using a template.
    
    Args:
        template_name: Name of the email template
        recipient_email: Email address of the recipient
        context: Dictionary of context variables for the template
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        subject, html_body, plain_body = render_email_template(template_name, context)
        
        from_email = get_from_email()
        connection = get_smtp_connection()
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=from_email,
            to=[recipient_email],
            cc=cc or [],
            bcc=bcc or [],
            connection=connection,
        )
        email.attach_alternative(html_body, "text/html")
        email.send()
        
        logger.info(f"Sent email notification '{template_name}' to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email notification '{template_name}' to {recipient_email}: {e}")
        return False


def send_bulk_email_notification(
    template_name: str,
    recipients: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Send email notifications to multiple recipients.
    
    Args:
        template_name: Name of the email template
        recipients: List of dicts with 'email' and 'context' keys
        
    Returns:
        dict: Summary of sent/failed emails
    """
    sent_count = 0
    failed_count = 0
    failed_emails = []
    
    for recipient in recipients:
        email = recipient.get('email')
        context = recipient.get('context', {})
        
        if not email:
            continue
        
        success = send_email_notification(template_name, email, context)
        if success:
            sent_count += 1
        else:
            failed_count += 1
            failed_emails.append(email)
    
    return {
        'sent_count': sent_count,
        'failed_count': failed_count,
        'failed_emails': failed_emails,
    }
