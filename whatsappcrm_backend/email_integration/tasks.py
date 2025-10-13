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
from .models import EmailAttachment, ParsedInvoice
from decimal import Decimal, InvalidOperation
from customer_data.models import CustomerProfile, Order, OrderItem
from conversations.models import Contact
from products_and_services.models import Product
from notifications.services import queue_notifications_to_users
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q

# Import the new model to fetch credentials
from ai_integration.models import AIProvider
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    name="email_integration.send_receipt_confirmation_email",
    # Automatically retry for connection errors, which are common for email servers.
    autoretry_for=(ConnectionRefusedError, smtplib.SMTPException),
    retry_backoff=True, 
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
        
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [attachment.sender]

        send_mail(subject, text_message, from_email, recipient_list, html_message=html_message)
        
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
    name="email_integration.process_attachment_with_gemini",
    # Automatically retry on transient API errors like rate limits or server overload.
    autoretry_for=(core_exceptions.ResourceExhausted, genai_errors.ServerError),
    retry_backoff=True, retry_kwargs={'max_retries': 5}
)
def process_attachment_with_gemini(self, attachment_id):
    """
    Fetches a saved attachment, uploads it directly to the Gemini File API,
    performs OCR and structured data extraction, and saves the result.
    """
    log_prefix = f"[Gemini File API Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Starting Gemini processing for attachment ID: {attachment_id}")

    attachment = None
    uploaded_file = None

    try:
        # 1. Fetch the attachment record and check processing status
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        if attachment.processed:
            logger.warning(f"{log_prefix} Attachment ID {attachment_id} already processed. Skipping.")
            return f"Skipped: Attachment {attachment_id} already processed."

        # --- Configure Gemini ---
        try:
            active_provider = AIProvider.objects.get(provider='google_gemini', is_active=True)
            # Using the explicit client-based approach as per the documentation
            client = genai.Client(api_key=active_provider.api_key)
        except (AIProvider.DoesNotExist, AIProvider.MultipleObjectsReturned) as e:
            error_message = f"Gemini API key configuration error: {e}"
            logger.error(f"{log_prefix} {error_message}")
            attachment.processed = True
            attachment.extracted_data = {"error": error_message, "status": "failed"}
            attachment.save(update_fields=['processed', 'extracted_data'])
            return f"Failed: {error_message}"

        # 2. Upload the local file to the Gemini API
        file_path = attachment.file.path
        logger.info(f"{log_prefix} Uploading file to Gemini: {file_path}")
        # Use the client instance to upload the file
        uploaded_file = client.files.upload(file=file_path)
        logger.info(f"{log_prefix} File uploaded successfully. URI: {uploaded_file.uri}")

        # 3. Define the Multimodal Prompt for structured JSON extraction
        # By defining the schema separately, we avoid the confusing double-bracket escaping.
        json_schema_definition = """
{
  "issuer": {
    "tin": "string" | null,
    "name": "string" | null,
    "email": "string" | null,
    "phone": "string" | null,
    "vat_no": "string" | null,
    "address": "string" | null
  },
  "recipient": {
    "name": "string" | null,
    "phone": "string" | null,
    "address": "string" | null
  },
  "line_items": [
    {
      "product_code": "string" | null,
      "description": "string",
      "quantity": "number",
      "unit_price": "number",
      "vat_amount": "number" | null,
      "total_amount": "number"
    }
  ],
  "invoice_number": "string" | null,
  "customer_reference_no": "string" | null,
  "invoice_date": "YYYY-MM-DD" | null,
  "total_amount": "number" | null,
  "total_vat_amount": "number" | null,
  "notes_and_terms": "string" | null
}
"""

        prompt = f"""
        Analyze the provided document (likely an invoice or receipt).
        Perform OCR to extract key details and structure them into a single, valid JSON object.

        The desired JSON schema is:
        {json_schema_definition}

        **Extraction Rules:**
        - For the 'invoice_number', prioritize the value associated with the "Customer Reference No" field. If that is not present, look for a standard "Invoice Number".
        - The 'invoice_date' must be in 'YYYY-MM-DD' format.
        - All monetary values must be numeric (float or integer), not strings.
        - If a field is not found, its value should be null.

        The final output MUST ONLY contain the valid, complete JSON object.
        """

        # 4. Call the Gemini API to process the document
        logger.info(f"{log_prefix} Sending request to Gemini model for analysis.")
        # Use the client instance to get the model
        # CORRECTED: Use client.models.generate_content directly, as per the documentation,
        # which is the idiomatic way when a client instance is used.
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, uploaded_file],
        )

        # 5. Parse the extracted JSON data
        try:
            # Clean up the response to remove potential markdown formatting
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            if not cleaned_text:
                raise json.JSONDecodeError("Empty response from Gemini", "", 0)
            extracted_data = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(
                f"{log_prefix} Failed to decode JSON from Gemini response for attachment {attachment_id}. "
                f"Error: {e}. Raw response text: '{response.text}'"
            )
            # Mark as failed and stop processing. This is a graceful failure.
            attachment.processed = True
            attachment.extracted_data = {"error": "Invalid JSON response from Gemini", "status": "failed", "raw_response": response.text}
            attachment.save(update_fields=['processed', 'extracted_data'])
            return f"Failed: Gemini returned non-JSON response for attachment {attachment_id}."

        # 6. Create Order and related objects from the extracted data
        _create_order_from_invoice_data(attachment, extracted_data, log_prefix)

        # 8. Update the EmailAttachment status
        attachment.processed = True
        attachment.extracted_data = extracted_data  # Save the JSON for review
        attachment.save(update_fields=['processed', 'extracted_data', 'updated_at'])

        logger.info(f"{log_prefix} Successfully processed attachment {attachment_id} and created associated order.")
        send_receipt_confirmation_email.delay(attachment_id)
        return f"Successfully processed attachment {attachment_id} with Gemini."

    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Attachment with ID {attachment_id} not found.")
        # Do not re-raise, as this is not a transient error.
    except (core_exceptions.ResourceExhausted, core_exceptions.DeadlineExceeded, genai_errors.ServerError) as e:
        logger.warning(f"{log_prefix} Gemini API rate limit or timeout error for attachment {attachment_id}: {e}. Task will be retried by Celery.")
        raise # Re-raise to let Celery handle the retry
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred during Gemini processing for attachment {attachment_id}: {e}", exc_info=True)
        if attachment:
            attachment.processed = True # Mark as processed to avoid retry loops on permanent errors
            attachment.extracted_data = {"error": str(e), "status": "failed"}
            attachment.save(update_fields=['processed', 'extracted_data'])
        # Do not re-raise; the error is logged and the attachment is marked as failed.
    finally:
        # 9. Clean up: Delete the file from the Gemini service
        if uploaded_file:
            try:
                logger.info(f"{log_prefix} Deleting temporary file from Gemini service: {uploaded_file.name}")
                # Use the client instance to delete the file
                client.files.delete(name=uploaded_file.name)
            except Exception as e:
                logger.error(f"{log_prefix} Failed to delete uploaded Gemini file {uploaded_file.name}: {e}")

@transaction.atomic
def _create_order_from_invoice_data(attachment: EmailAttachment, data: dict, log_prefix: str):
    """
    Creates or updates an Order, CustomerProfile, and OrderItems from extracted invoice data.
    """
    logger.info(f"{log_prefix} Starting to create Order from extracted data for attachment {attachment.id}.")
    from django.forms.models import model_to_dict

    invoice_number = data.get('invoice_number')
    if not invoice_number:
        logger.warning(f"{log_prefix} No 'invoice_number' found in extracted data. Cannot create order.")
        return

    # --- 1. Find or Create CustomerProfile ---
    recipient_data = data.get('recipient', {})
    recipient_name = recipient_data.get('name')
    recipient_phone = recipient_data.get('phone')
    customer_profile = None

    # A contact is required to create a customer profile. Use phone number if available.
    if recipient_phone:
        # Normalize the phone number to be just digits for the whatsapp_id
        normalized_phone = re.sub(r'\D', '', recipient_phone)

        # Find or create the base Contact record
        contact, contact_created = Contact.objects.get_or_create(
            whatsapp_id=normalized_phone,
            defaults={'name': recipient_name or f"Customer {normalized_phone}"}
        )
        if contact_created:
            logger.info(f"{log_prefix} Created new Contact for phone '{normalized_phone}'.")

        # Now, find or create the CustomerProfile linked to the Contact
        customer_profile, created = CustomerProfile.objects.get_or_create(
            contact=contact,
            defaults={
                'first_name': recipient_name.split(' ')[0] if recipient_name else '',
                'last_name': ' '.join(recipient_name.split(' ')[1:]) if recipient_name and ' ' in recipient_name else '',
                'notes': f"Profile automatically created from invoice {invoice_number}."
            }
        )
        if created:
            logger.info(f"{log_prefix} Created new CustomerProfile for '{recipient_name}'.")
        else:
            logger.info(f"{log_prefix} Found existing CustomerProfile for '{recipient_name}'.")

    # --- 2. Create or Update the Order ---
    invoice_date_obj = None
    if date_str := data.get('invoice_date'):
        try:
            invoice_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"{log_prefix} Could not parse date string '{date_str}' for Order.")

    order, order_created = Order.objects.update_or_create(
        order_number=invoice_number,
        defaults={
            'customer': customer_profile,
            'name': f"Invoice {invoice_number}",
            'stage': Order.Stage.CLOSED_WON, # Assume an invoice represents a completed sale
            'payment_status': Order.PaymentStatus.PAID, # Or 'pending' if that's more appropriate
            'amount': data.get('total_amount'),
            'source': Order.Source.EMAIL_IMPORT,
            'invoice_details': data, # Store the raw extracted data
            'expected_close_date': invoice_date_obj,
        }
    )

    if order_created:
        logger.info(f"{log_prefix} Created new Order with order_number '{invoice_number}'.")
    else:
        logger.info(f"{log_prefix} Updated existing Order with order_number '{invoice_number}'.")
        # If updating, clear old items to prevent duplicates
        order.items.all().delete()

    # --- 3. Create OrderItems ---
    line_items = data.get('line_items', [])
    if isinstance(line_items, list):
        for item_data in line_items:
            product_description = item_data.get('description', 'Unknown Product')
            product_code = item_data.get('product_code')
            
            # Efficiently find by SKU or name, creating if neither exists.
            product_query = Q()
            if product_code:
                product_query |= Q(sku=product_code)
            if product_description:
                product_query |= Q(name=product_description)

            product = Product.objects.filter(product_query).first() if product_query else None

            if not product:
                product = Product.objects.create(
                    sku=product_code,
                    name=product_description,
                    price=item_data.get('unit_price', 0),
                    product_type=Product.ProductType.HARDWARE # Default type
                )

            OrderItem.objects.create(order=order, product=product, quantity=item_data.get('quantity', 1), unit_price=item_data.get('unit_price', 0))
        logger.info(f"{log_prefix} Created {len(line_items)} OrderItem(s) for Order '{invoice_number}'.")

    # --- 4. Send a specific notification about the processed invoice ---
    # This is more specific than the generic 'new_order_created' signal.
    # FIX: The notification should be sent if the order was created OR updated,
    # as long as a customer profile exists to associate it with.
    if order and customer_profile:
        # Convert model instances to dictionaries to ensure they are JSON serializable
        customer_dict = model_to_dict(customer_profile, fields=['id', 'first_name', 'last_name'])
        # Manually add the full name and contact name for the template
        customer_dict['full_name'] = customer_profile.get_full_name()
        customer_dict['contact_name'] = getattr(getattr(customer_profile, 'contact', None), 'name', '')

        # FIX: Wrap the context in a 'template_context' key to match the template's variable access.
        # The template expects `{{ template_context.order.order_number }}`, not `{{ order.order_number }}`.
        final_context_for_template = {'template_context': {
            'attachment': model_to_dict(attachment, fields=['id', 'filename', 'sender']),
            'order': model_to_dict(order, fields=['id', 'order_number', 'name', 'amount']),
            'customer': customer_dict,
        }}
        queue_notifications_to_users(
            template_name='invoice_processed_successfully',
            group_names=settings.INVOICE_PROCESSED_NOTIFICATION_GROUPS, # Notify relevant teams
            related_contact=customer_profile.contact,
            template_context=final_context_for_template
        )
        logger.info(f"{log_prefix} Queued 'invoice_processed_successfully' notification for Order ID {order.id}.")



@shared_task(name="email_integration.fetch_email_attachments_task")
def fetch_email_attachments_task():
    """
    Celery task to run the fetch_mailu_attachments management command.
    """
    log_prefix = "[Fetch Email Task]"
    logger.info(f"{log_prefix} Starting scheduled task to fetch email attachments.")
    try:
        call_command('fetch_mailu_attachments')
        logger.info(f"{log_prefix} Successfully finished fetch_mailu_attachments command.")
    except Exception as e:
        logger.error(f"{log_prefix} The 'fetch_mailu_attachments' command failed: {e}", exc_info=True)
        raise