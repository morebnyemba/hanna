import os
import logging
import re
from google.api_core import exceptions as core_exceptions
import smtplib
import json
from datetime import datetime
from celery import shared_task, chain

from celery import shared_task
from google import genai
from google.genai import types as genai_types
from google.genai import errors as genai_errors
from .models import EmailAttachment, ParsedInvoice, AdminEmailRecipient
from decimal import Decimal, InvalidOperation
# --- ADD JobCard to imports ---
from customer_data.models import CustomerProfile, Order, OrderItem, JobCard, InstallationRequest
from conversations.models import Contact
from conversations.utils import normalize_phone_number
from products_and_services.models import Product, SerializedItem
from notifications.services import queue_notifications_to_users
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q

# Import the new model to fetch credentials
from ai_integration.models import AIProvider
from django.conf import settings
from .smtp_utils import get_smtp_connection, get_from_email

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="email_integration.send_receipt_confirmation_email",
    # Automatically retry for connection errors, which are common for email servers.
    autoretry_for=(ConnectionRefusedError, smtplib.SMTPException),
    retry_backbackoff=True,
    retry_kwargs={'max_retries': 3}
)
def send_receipt_confirmation_email(self, attachment_id):
    """
    Sends an email to the original sender confirming receipt of their attachment.
    Retries on common SMTP connection errors.
    """
    log_prefix = f"[Email Confirmation Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Preparing to send receipt confirmation for attachment ID: {attachment_id}")
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)

        if not attachment.sender:
            logger.warning(f"{log_prefix} Attachment {attachment_id} has no sender email. Cannot send confirmation.")
            return "Skipped: No sender email."

        subject = f"Confirmation: We've received your document '{attachment.filename}'"

        # Plain text version for email clients that don't support HTML
        text_message = (
            f"Dear Sender,\n\n"
            f"This is an automated message to confirm that we have successfully received your attachment named '{attachment.filename}'.\n\n"
            f"Our system is now processing it. You will be notified if any further action is required.\n\n"
            f"Thank you,\n"
            f"Hanna Installations"
        )

        # HTML version for a richer user experience
        html_message = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; margin: auto; }}
                    .header {{ font-size: 1.2em; font-weight: bold; color: #28a745; }}
                    strong {{ color: #000; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <p class="header">Document Receipt Confirmation</p>
                    <p>Dear Sender,</p>
                    <p>This is an automated message to confirm that we have successfully received your attachment named <strong>'{attachment.filename}'</strong>.</p>
                    <p>Our system is now processing it. You will be notified if any further action is required.</p>
                    <p>Thank you,<br><strong>Hanna Installations</strong></p>
                </div>
            </body>
        </html>
        """

        from_email = get_from_email()
        recipient_list = [attachment.sender]
        
        # Use database SMTP config if available
        connection = get_smtp_connection()
        
        send_mail(
            subject, 
            text_message, 
            from_email, 
            recipient_list, 
            html_message=html_message,
            connection=connection
        )

        logger.info(f"{log_prefix} Successfully sent confirmation email to {attachment.sender} for attachment {attachment_id}.")
        return f"Confirmation sent to {attachment.sender}."
    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Could not find EmailAttachment with ID {attachment_id} to send confirmation.")
        # No retry needed, this is a permanent failure for this task instance.
    except Exception as e:
        # The `autoretry_for` decorator handles SMTP exceptions. We just need to log other errors.
        logger.error(f"{log_prefix} An unexpected error occurred while sending confirmation for attachment {attachment_id}: {e}", exc_info=True)
        raise  # Re-raise to let Celery mark the task as failed for non-retriable errors.

@shared_task(
    bind=True,
    name="email_integration.send_duplicate_invoice_email",
    autoretry_for=(ConnectionRefusedError, smtplib.SMTPException),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3}
)
def send_duplicate_invoice_email(self, attachment_id, order_number):
    """
    Sends an email to the original sender informing them that the invoice
    they sent is a duplicate of an existing order.
    """
    log_prefix = f"[Duplicate Email Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Preparing to send duplicate invoice notification for attachment ID: {attachment_id}")
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        if not attachment.sender:
            logger.warning(f"{log_prefix} Attachment {attachment_id} has no sender email. Cannot send notification.")
            return "Skipped: No sender email."

        subject = f"Duplicate Invoice Detected: '{attachment.filename}'"
        message = (
            f"Dear Sender,\n\n"
            f"This is an automated message to inform you that the invoice '{attachment.filename}' you sent appears to be a duplicate.\n\n"
            f"An order with the same invoice number ({order_number}) already exists in our system.\n\n"
            f"No further action is needed. If you believe this is an error, please contact our support team.\n\n"
            f"Thank you,\n"
            f"Hanna Installations"
        )
        from_email = get_from_email()
        recipient_list = [attachment.sender]
        connection = get_smtp_connection()
        
        send_mail(subject, message, from_email, recipient_list, connection=connection)
        logger.info(f"{log_prefix} Successfully sent duplicate invoice email to {attachment.sender}.")
        return f"Duplicate notification sent to {attachment.sender}."
    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Could not find EmailAttachment with ID {attachment_id} to send duplicate notification.")
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred while sending duplicate notification for attachment {attachment_id}: {e}", exc_info=True)
        raise

@shared_task(name="email_integration.send_error_notification_email")
def send_error_notification_email(task_name, attachment_id, error_message, raw_response=None):
    """
    Sends a standardized email notification to the admin when a critical task fails.
    """
    subject = f"URGENT: Critical Task Failure in {task_name}"
    
    # Obfuscate part of the attachment ID if it's sensitive, though it's a UUID.
    safe_attachment_id = str(attachment_id)[:8] + "..." if attachment_id else "N/A"

    html_message = f"""
    <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f4f4; color: #333; }}
                .container {{ max-width: 700px; margin: 20px auto; padding: 25px; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
                .header {{ background-color: #d9534f; color: #ffffff; padding: 15px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 20px; }}
                .content h2 {{ color: #d9534f; font-size: 20px; border-bottom: 2px solid #eeeeee; padding-bottom: 10px; }}
                .error-details {{ background-color: #f9f2f2; border: 1px solid #e6b8b8; padding: 15px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; white-space: pre-wrap; word-wrap: break-word; }}
                .raw-response {{ background-color: #f0f0f0; border: 1px solid #ccc; padding: 15px; border-radius: 5px; margin-top: 15px; font-family: 'Courier New', Courier, monospace; white-space: pre-wrap; word-wrap: break-word; }}
                .footer {{ margin-top: 25px; text-align: center; font-size: 12px; color: #888; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Critical Task Failure</h1>
                </div>
                <div class="content">
                    <h2>Error Summary</h2>
                    <p>A critical error occurred in the background processing system. Manual intervention may be required.</p>
                    
                    <h3>Task Details:</h3>
                    <ul>
                        <li><strong>Task Name:</strong> {task_name}</li>
                        <li><strong>Attachment ID:</strong> {safe_attachment_id}</li>
                        <li><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
                    </ul>

                    <h2>Error Message</h2>
                    <div class="error-details">
                        <p>{error_message}</p>
                    </div>
"""
    if raw_response:
        html_message += f"""
                    <h2>Raw AI Response</h2>
                    <div class="raw-response">
                        <p>{raw_response}</p>
                    </div>
"""
    html_message += """
                </div>
                <div class="footer">
                    <p>This is an automated notification from the Hanna Installations CRM.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    try:
        # Get active admin email recipients from the database instead of settings
        recipient_list = list(AdminEmailRecipient.objects.filter(is_active=True).values_list('email', flat=True))
        
        if not recipient_list:
            logger.warning(
                f"No active AdminEmailRecipient configured. Cannot send error notification for task {task_name}. "
                "Please add admin email recipients in the Django admin panel."
            )
            return
        
        connection = get_smtp_connection()
        
        send_mail(
            subject=subject,
            message=f"Critical task failure in {task_name} for attachment {attachment_id}. Error: {error_message}", # Plain text fallback
            from_email=get_from_email(),
            recipient_list=recipient_list,
            html_message=html_message,
            connection=connection,
            fail_silently=False,
        )
        logger.info(f"Successfully sent error notification email for task {task_name} and attachment {attachment_id} to {len(recipient_list)} recipient(s).")
    except Exception as e:
        logger.critical(
            f"FATAL: Could not send error notification email for task {task_name}. "
            f"Original error: {error_message}. Email sending error: {e}",
            exc_info=True
        )

def _parse_gemini_json_response(raw_text: str, log_prefix: str) -> dict:
    """
    Robustly parse JSON from Gemini API response with multiple fallback strategies.
    
    Handles common issues:
    - Markdown code blocks (```json ... ```)
    - Trailing commas in arrays and objects
    - Missing closing braces
    - Extra text before/after JSON
    
    Args:
        raw_text: The raw response text from Gemini API
        log_prefix: Logging prefix for context
        
    Returns:
        Parsed JSON as a dictionary
        
    Raises:
        json.JSONDecodeError: If all parsing strategies fail
    """
    if not raw_text or not raw_text.strip():
        raise json.JSONDecodeError("Empty response from Gemini", "", 0)
    
    cleaned_text = None
    parsing_strategy = None
    
    # Strategy 1: Extract JSON from markdown code blocks (```json ... ```)
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw_text)
    if json_match:
        cleaned_text = json_match.group(1).strip()
        parsing_strategy = "markdown_extraction"
        logger.debug(f"{log_prefix} Using markdown extraction strategy")
    
    # Strategy 2: Find JSON object starting with { and ending with }
    if not cleaned_text:
        json_object_match = re.search(r'(\{[\s\S]*\})', raw_text)
        if json_object_match:
            cleaned_text = json_object_match.group(1).strip()
            parsing_strategy = "regex_extraction"
            logger.debug(f"{log_prefix} Using regex extraction strategy")
    
    # Strategy 3: Use entire text after removing markdown markers (backward compatibility)
    if not cleaned_text:
        cleaned_text = raw_text.replace('```json', '').replace('```', '').strip()
        parsing_strategy = "simple_cleanup"
        logger.debug(f"{log_prefix} Using simple cleanup strategy")
    
    if not cleaned_text:
        raise json.JSONDecodeError("Could not extract JSON content from response", "", 0)
    
    # Try parsing the cleaned text
    parse_attempts = [
        ("direct", cleaned_text),
    ]
    
    # Apply multiple fix strategies, building on previous fixes
    current_text = cleaned_text
    
    # Strategy 4: Fix trailing commas before closing braces/brackets
    fixed_text = re.sub(r',(\s*[}\]])', r'\1', current_text)
    if fixed_text != current_text:
        parse_attempts.append(("trailing_comma_fix", fixed_text))
        logger.debug(f"{log_prefix} Applied trailing comma fix")
        current_text = fixed_text
    
    # Strategy 5: Fix missing closing brace before comma (e.g., "value": 123\n      ,\n      {)
    # This handles the exact pattern from the GitHub issue where a closing brace is missing
    # Pattern: number, whitespace, newline, comma, whitespace, opening brace
    # Replace with: number, closing brace, comma, whitespace, opening brace
    fixed_text = re.sub(r'(\d+\.?\d*)(\s*\n\s*),(\s*\n\s*\{)', r'\1},\3', current_text)
    if fixed_text != current_text:
        parse_attempts.append(("missing_brace_before_comma_fix", fixed_text))
        logger.debug(f"{log_prefix} Applied missing brace before comma fix")
        current_text = fixed_text
    
    # Strategy 6: Fix trailing commas before newlines followed by object/array start
    fixed_text = re.sub(r',(\s*\n\s*[{\[])', r'\1', current_text)
    if fixed_text != current_text:
        parse_attempts.append(("newline_comma_fix", fixed_text))
        logger.debug(f"{log_prefix} Applied newline comma fix")
        current_text = fixed_text
    
    # Strategy 7: More aggressive - fix any pattern of value, newline, comma, newline, opening brace
    # Matches numbers, strings, booleans, null followed by comma on separate line
    fixed_text = re.sub(
        r'([\d\w]+|true|false|null)(\s*\n\s*),(\s*\n\s*[{\[])',
        r'\1},\3',
        current_text
    )
    if fixed_text != current_text:
        parse_attempts.append(("aggressive_missing_brace_fix", fixed_text))
        logger.debug(f"{log_prefix} Applied aggressive missing brace fix")
        current_text = fixed_text
    
    # Try each parsing attempt
    last_error = None
    for strategy_name, text_to_parse in parse_attempts:
        try:
            result = json.loads(text_to_parse)
            logger.info(f"{log_prefix} Successfully parsed JSON using strategy: {strategy_name}")
            return result
        except json.JSONDecodeError as e:
            last_error = e
            logger.debug(f"{log_prefix} Strategy '{strategy_name}' failed: {e}")
            continue
    
    # All strategies failed - provide detailed error information
    error_context = f"All parsing strategies failed. Last error: {last_error}"
    logger.error(f"{log_prefix} {error_context}")
    logger.error(f"{log_prefix} Original text length: {len(raw_text)}, Cleaned text length: {len(cleaned_text)}")
    logger.error(f"{log_prefix} First 500 chars of cleaned text: {cleaned_text[:500]}")
    
    # Re-raise the last error with additional context
    raise json.JSONDecodeError(
        f"{error_context}. {last_error.msg}",
        last_error.doc,
        last_error.pos
    )

@shared_task(
    bind=True,
    name="email_integration.process_attachment_with_gemini",
    # Automatically retry on transient API errors like rate limits or server overload.
    autoretry_for=(core_exceptions.ResourceExhausted, genai_errors.ServerError),
    retry_backoff=True, retry_kwargs={'max_retries': 5}
)
def process_attachment_with_gemini(self, attachment_id):
    """
    Fetches an attachment, asks Gemini to classify it (invoice or job_card),
    extracts structured data based on the type, and saves it to the correct model.
    On failure, it sends a notification to the admin.
    """
    log_prefix = f"[Gemini File API Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Starting Gemini processing for attachment ID: {attachment_id}")

    attachment = None
    uploaded_file = None
    client = None

    try:
        # 1. Fetch the attachment record and check processing status
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        if attachment.processed:
            logger.warning(f"{log_prefix} Attachment ID {attachment_id} already processed. Skipping.")
            return f"Skipped: Attachment {attachment_id} already processed."

        # --- Configure Gemini ---
        try:
            active_provider = AIProvider.objects.get(provider='google_gemini', is_active=True)
            client = genai.Client(api_key=active_provider.api_key)
        except (AIProvider.DoesNotExist, AIProvider.MultipleObjectsReturned) as e:
            error_message = f"Gemini API key configuration error: {e}"
            logger.error(f"{log_prefix} {error_message}")
            attachment.processed = True
            attachment.extracted_data = {"error": error_message, "status": "failed"}
            attachment.save(update_fields=['processed', 'extracted_data'])
            # Trigger admin notification for this critical configuration error
            send_error_notification_email.delay(self.name, attachment_id, error_message)
            return f"Failed: {error_message}"

        # 2. Upload the local file to the Gemini API
        file_path = attachment.file.path
        logger.info(f"{log_prefix} Uploading file to Gemini: {file_path}")
        uploaded_file = client.files.upload(file=file_path)
        logger.info(f"{log_prefix} File uploaded successfully. URI: {uploaded_file.uri}")

        # --- UPDATED: More detailed invoice schema ---
        invoice_schema_definition = """
        {
          "issuer": {
            "tin": "string | null",
            "name": "string | null",
            "email": "string | null",
            "phone": "string | null",
            "vat_no": "string | null",
            "address": "string | null"
          },
          "recipient": {
            "name": "string | null",
            "phone": "string | null",
            "address": "string | null"
          },
          "line_items": [
            {
              "product_code": "string | null",
              "description": "string",
              "quantity": "number",
              "unit_price": "number",
              "vat_amount": "number | null",
              "total_amount": "number"
            }
          ],
          "invoice_number": "string | null",
          "customer_reference_no": "string | null",
          "invoice_date": "YYYY-MM-DD | null",
          "total_amount": "number | null",
          "total_vat_amount": "number | null",
          "notes_and_terms": "string | null"
        }
        """

        job_card_schema_definition = """
        {
          "job_card_number": "string", "creation_date": "YYYY-MM-DD",
          "customer": { "name": "string", "phone": "string", "address": "string" },
          "product": { "description": "string", "serial_number": "string" },
          "reported_fault": "string", "is_under_warranty": "boolean", "status": "string"
        }
        """

        # --- NEW: Update the Prompt to Classify First, then Extract ---
        prompt = f"""
        Analyze the attached document and determine its type. The type can be 'invoice' or 'job_card'.

        Based on the identified type, extract the key details into the corresponding JSON schema.

        If the document type is 'invoice', use this schema:
        {invoice_schema_definition}

        If the document type is 'job_card', use this schema:
        {job_card_schema_definition}

        Your final output must be a single JSON object with two keys: "document_type" and "data".
        The "data" key should contain the extracted information. For dates, use YYYY-MM-DD format.
        For boolean values, use true or false.

        Example for a job card:
        {{
            "document_type": "job_card",
            "data": {{ "job_card_number": "31,699", "creation_date": "2025-09-18", ... }}
        }}
        """

        # 4. Call the Gemini API to process the document
        logger.info(f"{log_prefix} Sending request to Gemini model for analysis.")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, uploaded_file],
        )

        # 5. Parse the extracted JSON data
        try:
            raw_text = response.text.strip()
            extracted_data = _parse_gemini_json_response(raw_text, log_prefix)
        except json.JSONDecodeError as e:
            error_message = f"Failed to decode JSON from Gemini response. Error: {e}."
            logger.error(f"{log_prefix} {error_message} Raw response text: '{response.text}'")
            attachment.processed = True
            attachment.extracted_data = {"error": error_message, "status": "failed", "raw_response": response.text}
            attachment.save(update_fields=['processed', 'extracted_data'])
            # Trigger admin notification
            send_error_notification_email.delay(self.name, attachment_id, error_message, raw_response=response.text)
            return f"Failed: {error_message}"

        # --- NEW: Conditional Logic Based on Document Type ---
        document_type = extracted_data.get("document_type")
        data = extracted_data.get("data")

        if not document_type or not data:
            error_message = "AI response missing 'document_type' or 'data' key."
            raise ValueError(error_message)

        logger.info(f"{log_prefix} Gemini identified document as type: '{document_type}'")

        if document_type == 'invoice':
            _create_order_from_invoice_data(attachment, data, log_prefix)
        elif document_type == 'job_card':
            _create_job_card_from_data(attachment, data, log_prefix)
        else:
            logger.warning(f"{log_prefix} Unknown document type '{document_type}' received. Skipping database save.")

        # 8. Update the EmailAttachment status
        attachment.processed = True
        attachment.extracted_data = extracted_data
        attachment.save(update_fields=['processed', 'extracted_data', 'updated_at'])

        logger.info(f"{log_prefix} Successfully processed attachment {attachment_id}.")
        send_receipt_confirmation_email.delay(attachment_id)
        return f"Successfully processed attachment {attachment_id} with Gemini."

    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Attachment with ID {attachment_id} not found.")
        # No notification needed if the attachment doesn't exist, as it's a state issue.
    except (core_exceptions.ResourceExhausted, core_exceptions.DeadlineExceeded, genai_errors.ServerError) as e:
        logger.warning(f"{log_prefix} Gemini API rate limit or timeout error for attachment {attachment_id}: {e}. Task will be retried by Celery.")
        raise # Re-raise to let Celery handle the retry
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        logger.error(f"{log_prefix} {error_message}", exc_info=True)
        if attachment:
            attachment.processed = True
            attachment.extracted_data = {"error": str(e), "status": "failed"}
            attachment.save(update_fields=['processed', 'extracted_data'])
        # Trigger admin notification for any other unexpected error
        send_error_notification_email.delay(self.name, attachment_id, error_message)
    finally:
        # 9. Clean up: Delete the file from the Gemini service
        if uploaded_file and client:
            try:
                logger.info(f"{log_prefix} Deleting temporary file from Gemini service: {uploaded_file.name}")
                client.files.delete(name=uploaded_file.name)
            except Exception as e:
                # This failure is not critical enough to stop the process, but it should be logged.
                logger.error(f"{log_prefix} Failed to delete uploaded Gemini file {uploaded_file.name}: {e}")



def _get_or_create_customer_profile(customer_data: dict, log_prefix: str) -> CustomerProfile | None:
    """Finds or creates a customer profile based on data from a document."""
    customer_name = customer_data.get('name')
    customer_phone = customer_data.get('phone')

    if not customer_phone and customer_name:
        match = re.search(r'(07[1-9][0-9]{7})', customer_name)
        if match:
            customer_phone = match.group(0)
            customer_name = customer_name.replace(customer_phone, '').strip(' _-').strip()
            logger.info(f"{log_prefix} Extracted fallback phone '{customer_phone}' from name.")

    if not customer_phone:
        logger.warning(f"{log_prefix} No phone number found for customer '{customer_name}'. Cannot create profile.")
        return None

    # Normalize phone number to E.164 format for WhatsApp (e.g., "0772354523" -> "263772354523")
    normalized_phone = normalize_phone_number(customer_phone)
    if not normalized_phone:
        logger.warning(f"{log_prefix} Failed to normalize phone number '{customer_phone}' for customer '{customer_name}'. Cannot create profile.")
        return None
    
    contact, _ = Contact.objects.get_or_create(
        whatsapp_id=normalized_phone,
        defaults={'name': customer_name or f"Customer {normalized_phone}"}
    )

    profile, created = CustomerProfile.objects.get_or_create(
        contact=contact,
        defaults={
            'first_name': customer_name.split(' ')[0] if customer_name else '',
            'last_name': ' '.join(customer_name.split(' ')[1:]) if customer_name and ' ' in customer_name else '',
            'address_line_1': customer_data.get('address', '')
        }
    )

    if created:
        logger.info(f"{log_prefix} Created new CustomerProfile for '{customer_name}'.")
    else:
        logger.info(f"{log_prefix} Found existing CustomerProfile for '{customer_name}'.")

    return profile


@transaction.atomic
def _create_order_from_invoice_data(attachment: EmailAttachment, data: dict, log_prefix: str):
    """Creates or updates an Order and its items from extracted invoice data."""
    from django.forms.models import model_to_dict
    from django.utils import timezone
    from datetime import timedelta

    logger.info(f"{log_prefix} Starting to create Order from extracted data.")
    
    customer_profile = _get_or_create_customer_profile(data.get('recipient', {}), log_prefix)
    
    # --- FIX: More robust fallback logic for order number ---
    invoice_num_raw = data.get('invoice_number')
    cust_ref_raw = data.get('customer_reference_no')
    invoice_number = None

    # Prioritize invoice_number only if it's a meaningful, non-zero value
    if invoice_num_raw and str(invoice_num_raw).strip() and str(invoice_num_raw).strip() != '0':
        invoice_number = str(invoice_num_raw).strip()
    # Fallback to customer_reference_no if it exists and invoice_number was not valid
    elif cust_ref_raw and str(cust_ref_raw).strip():
        invoice_number = str(cust_ref_raw).strip()

    if not invoice_number:
        logger.warning(f"{log_prefix} No valid 'invoice_number' or 'customer_reference_no' found in data. Cannot create order.")
        return

    # --- NEW: Check for existing order BEFORE creating ---
    if Order.objects.filter(order_number=invoice_number).exists():
        logger.warning(f"{log_prefix} Order with number '{invoice_number}' already exists. Skipping creation and sending duplicate notification.")
        send_duplicate_invoice_email.delay(attachment.id, invoice_number)
        return # Stop processing

    invoice_date_obj = None
    if date_str := data.get('invoice_date'):
        try:
            invoice_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"{log_prefix} Could not parse date string '{date_str}' for Order.")

    # Since we checked for existence, we can now safely create it.
    order = Order.objects.create(
        order_number=invoice_number,
        customer=customer_profile,
        name=f"Invoice {invoice_number}",
        stage=Order.Stage.CLOSED_WON,
        payment_status=Order.PaymentStatus.PAID,
        source=Order.Source.EMAIL_IMPORT,
        invoice_details=data,
        expected_close_date=invoice_date_obj,
    )

    logger.info(f"{log_prefix} Created new Order with order_number '{invoice_number}'.")

    # --- NEW: Automatically create an InstallationRequest ---
    if customer_profile:
        installation_date = timezone.now() + timedelta(hours=72)
        InstallationRequest.objects.create(
            customer=customer_profile,
            associated_order=order,
            status='pending',
            installation_type='residential', # Defaulting to residential
            full_name=customer_profile.get_full_name() or "N/A",
            address=customer_profile.address_line_1 or "N/A",
            contact_phone=customer_profile.contact.whatsapp_id,
            preferred_datetime=installation_date.strftime('%Y-%m-%d %H:%M:%S'),
            notes=f"Automatically generated from processed invoice '{attachment.filename}'."
        )
        logger.info(f"{log_prefix} Automatically created InstallationRequest for order '{invoice_number}'.")


    line_items = data.get('line_items', [])
    number_of_panels = 0
    if isinstance(line_items, list):
        for item_data in line_items:
            product_code = item_data.get('product_code')
            product_description = item_data.get('description', 'Unknown Product')
            
            if 'panel' in product_description.lower():
                number_of_panels += item_data.get('quantity', 0)
            
            # More robust product lookup: Try SKU first, then name.
            product = None
            if product_code:
                product = Product.objects.filter(sku=product_code).first()
            if not product and product_description:
                product = Product.objects.filter(name=product_description).first()

            if not product:
                product = Product.objects.create(
                    sku=product_code,
                    name=product_description,
                    price=item_data.get('unit_price', 0),
                    product_type=Product.ProductType.HARDWARE,  # Default type
                    is_active=False,  # Products from email import need manual review before activation
                )
            OrderItem.objects.create(
                order=order, 
                product=product, 
                quantity=item_data.get('quantity', 1), 
                unit_price=item_data.get('unit_price', 0),
                total_amount=item_data.get('total_amount', 0) # Save the line item total
            )
        logger.info(f"{log_prefix} Created {len(line_items)} OrderItem(s) for Order '{invoice_number}'.")

        # --- NEW: Send the specific, more descriptive notification for email imports ---
        if customer_profile:
            from django.forms.models import model_to_dict
            attachment_dict = model_to_dict(attachment, fields=['sender', 'filename'])
            # --- FIX: Explicitly convert Decimal to float for JSON serialization ---
            order_dict = {
                'order_number': order.order_number, 'amount': float(order.amount) if order.amount is not None else 0.0,
                'number_of_panels': number_of_panels
            }
            customer_dict = {
                'full_name': customer_profile.get_full_name(), 
                'contact_name': getattr(customer_profile.contact, 'name', None),
                'client_number': customer_profile.contact.whatsapp_id
            }

            queue_notifications_to_users(
                template_name='hanna_invoice_processed_successfully',
                group_names=settings.INVOICE_PROCESSED_NOTIFICATION_GROUPS,
                related_contact=customer_profile.contact,
                template_context={
                    'attachment': attachment_dict, 'order': order_dict, 'customer': customer_dict,
                    # Flattened variables for simplified template
                    'sender': attachment_dict.get('sender', ''),
                    'filename': attachment_dict.get('filename', ''),
                    'order_number': order_dict.get('order_number', ''),
                    'order_amount': f"{order_dict.get('amount') or 0:.2f}",
                    'customer_name': customer_dict.get('full_name') or customer_dict.get('contact_name') or ''
                }
            )
            
            # --- NEW: Send WhatsApp notification to the customer ---
            queue_notifications_to_users(
                template_name='hanna_customer_invoice_confirmation', # New template for customers
                contact_ids=[customer_profile.contact.id],
                related_contact=customer_profile.contact,
                template_context={
                    'customer_name': customer_profile.get_full_name(),
                    'order_number': order.order_number,
                    'total_amount': f"{order.amount:.2f}" if order.amount is not None else "N/A",
                    'invoice_date': order.expected_close_date.strftime('%Y-%m-%d') if order.expected_close_date else "N/A",
                }
            )
            logger.info(f"{log_prefix} Queued WhatsApp notification for customer {customer_profile.contact.whatsapp_id} for order '{order.order_number}'.")

@transaction.atomic
def _create_job_card_from_data(attachment: EmailAttachment, data: dict, log_prefix: str):
    """Creates or updates a JobCard from extracted data."""
    logger.info(f"{log_prefix} Starting to create JobCard from extracted data.")

    customer_profile = _get_or_create_customer_profile(data.get('customer', {}), log_prefix)

    job_card_number = data.get('job_card_number')
    if not job_card_number:
        logger.warning(f"{log_prefix} No 'job_card_number' found in data. Cannot create job card.")
        return

    creation_date_obj = None
    if date_str := data.get('creation_date'):
        try:
            creation_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"{log_prefix} Could not parse date string '{date_str}' for JobCard.")

    product_info = data.get('product', {})

    # --- NEW: Find or create the SerializedItem ---
    serialized_item = None
    serial_number = product_info.get('serial_number')
    product_description = product_info.get('description')

    if serial_number:
        # Try to find an existing serialized item
        serialized_item = SerializedItem.objects.filter(serial_number=serial_number).first()
        if not serialized_item:
            # If it doesn't exist, we need to create it. First, find or create the base product.
            product = None
            if product_description:
                product = Product.objects.filter(name__icontains=product_description).first()
            
            if not product:
                # If the base product doesn't exist, create it.
                product = Product.objects.create(
                    name=product_description or f"Product with SN {serial_number}",
                    product_type=Product.ProductType.HARDWARE,  # Default type
                    is_active=False,  # Products from email import need manual review before activation
                )

            # Now create the new serialized item
            serialized_item = SerializedItem.objects.create(
                product=product,
                serial_number=serial_number,
                status=SerializedItem.Status.IN_REPAIR # Default status for a new item from a job card
            )

    job_card, created = JobCard.objects.update_or_create(
        job_card_number=job_card_number,
        defaults={
            'customer': customer_profile,
            'serialized_item': serialized_item, # Link to the serialized item
            'reported_fault': data.get('reported_fault'),
            'is_under_warranty': data.get('is_under_warranty', False),
            'creation_date': creation_date_obj,
            'status': data.get('status', 'open').lower(),
            'job_card_details': data,
        }
    )

    if created:
        logger.info(f"{log_prefix} Created new JobCard with number '{job_card_number}'.")
    else:
        logger.info(f"{log_prefix} Updated existing JobCard with number '{job_card_number}'.")

    # --- NEW: Send notification if a new job card was created ---
    if created:
        from django.forms.models import model_to_dict
        job_card_dict = model_to_dict(job_card, fields=[
            'job_card_number', 'product_description', 'product_serial_number', 'reported_fault'
        ])
        customer_dict = {}
        if customer_profile:
            customer_dict = {
                'first_name': customer_profile.first_name,
                'last_name': customer_profile.last_name
            }

        queue_notifications_to_users(
            template_name='hanna_job_card_created_successfully',
            # You might want to create a specific group setting for this
            group_names=settings.INVOICE_PROCESSED_NOTIFICATION_GROUPS,
            related_contact=customer_profile.contact if customer_profile else None,
            template_context={'job_card': job_card_dict, 'customer': customer_dict}
        )

@shared_task(name="email_integration.fetch_email_attachments_task")
def fetch_email_attachments_task():
    """
    Celery task to run the fetch_mailu_attachments management command.
    """
    log_prefix = "[Fetch Email Task]"
    logger.info(f"{log_prefix} Starting scheduled task to fetch email attachments.")
    try:
        call_command('fetch_mailu_attachments')
        logger.info(f"{log_prefix} Successfully finished fetch_mail_attachments command.")
    except Exception as e:
        logger.error(f"{log_prefix} The 'fetch_mail_attachments' command failed: {e}", exc_info=True)
        raise