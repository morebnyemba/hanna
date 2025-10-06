import os
import logging
import re
from google.api_core import exceptions as core_exceptions
import json
from datetime import datetime
from celery import shared_task, chain

from google import genai
from google.genai import types as genai_types
from .models import EmailAttachment, ParsedInvoice
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.core.mail import send_mail

# Import the new model to fetch credentials
from ai_integration.models import AIProvider
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(name="email_integration.send_receipt_confirmation_email")
def send_receipt_confirmation_email(attachment_id):
    """
    Sends an email to the original sender confirming receipt of their attachment.
    """
    log_prefix = "[Email Confirmation Task]"
    logger.info(f"{log_prefix} Preparing to send receipt confirmation for attachment ID: {attachment_id}")
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        
        if not attachment.sender:
            logger.warning(f"{log_prefix} Attachment {attachment_id} has no sender email. Cannot send confirmation.")
            return "Skipped: No sender email."

        subject = f"Confirmation: We've received your document '{attachment.filename}'"
        message = (
            f"Dear Sender,\n\n"
            f"This is an automated message to confirm that we have successfully received your attachment named '{attachment.filename}'.\n\n"
            f"Our system is now processing it. You will be notified if any further action is required.\n\n"
            f"Thank you,\n"
            f"Hanna Installations"
        )
        
        from_email = os.getenv("MAILU_IMAP_USER")
        if not from_email:
            logger.warning(f"{log_prefix} MAILU_IMAP_USER environment variable not set. Falling back to default from_email.")
            from_email = settings.DEFAULT_FROM_EMAIL

        recipient_list = [attachment.sender]

        send_mail(subject, message, from_email, recipient_list)
        
        logger.info(f"{log_prefix} Successfully sent confirmation email to {attachment.sender} for attachment {attachment_id}.")
        return f"Confirmation sent to {attachment.sender}."
    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Could not find EmailAttachment with ID {attachment_id} to send confirmation.")
    except Exception as e:
        logger.error(f"{log_prefix} Failed to send confirmation email for attachment {attachment_id}: {e}", exc_info=True)

@shared_task(bind=True, name="email_integration.process_attachment_with_gemini", autoretry_for=(core_exceptions.ResourceExhausted,), retry_backoff=True, retry_kwargs={'max_retries': 3})
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
            raise ValueError(f"Gemini API key configuration error: {e}")

        # 2. Upload the local file to the Gemini API
        file_path = attachment.file.path
        logger.info(f"{log_prefix} Uploading file to Gemini: {file_path}")
        # Use the client instance to upload the file
        uploaded_file = client.files.upload(file=file_path)
        logger.info(f"{log_prefix} File uploaded successfully. URI: {uploaded_file.uri}")

        # 3. Define the Multimodal Prompt for structured JSON extraction
        prompt = """
        Analyze the provided document (likely an invoice or receipt). 
        Perform OCR to extract all key details and structure the entire content 
        into a single, valid JSON object.

        The JSON must contain the fields: 'invoice_number', 'invoice_date' (in YYYY-MM-DD format), 
        'total_amount' (numeric), 'issuer', 'recipient', and a detailed 'line_items' array.
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

        # 6. Map extracted data to the ParsedInvoice model
        invoice_number = extracted_data.get('invoice_number')
        total_amount = extracted_data.get('total_amount')
        date_str = extracted_data.get('invoice_date')

        invoice_date_obj = None
        if date_str:
            try:
                invoice_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                try:
                    invoice_date_obj = datetime.strptime(date_str, '%d-%m-%Y').date()
                except (ValueError, TypeError):
                    logger.warning(f"{log_prefix} Could not parse date string '{date_str}' for ID: {attachment_id}")

        # 7. Create or update the ParsedInvoice entry
        ParsedInvoice.objects.update_or_create(
            attachment=attachment,
            defaults={
                'invoice_number': str(invoice_number).strip() if invoice_number else None,
                'invoice_date': invoice_date_obj,
                'total_amount': total_amount,
            }
        )

        # 8. Update the EmailAttachment status
        attachment.processed = True
        attachment.extracted_data = extracted_data  # Save the JSON for review
        attachment.save(update_fields=['processed', 'extracted_data', 'updated_at'])

        logger.info(f"{log_prefix} Successfully created/updated ParsedInvoice for attachment ID: {attachment_id}")
        send_receipt_confirmation_email.delay(attachment_id)
        return f"Successfully processed attachment {attachment_id} with Gemini."

    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Attachment with ID {attachment_id} not found.")
        # Do not re-raise, as this is not a transient error.
    except (core_exceptions.ResourceExhausted, core_exceptions.DeadlineExceeded) as e:
        logger.warning(f"{log_prefix} Gemini API rate limit or timeout error for attachment {attachment_id}: {e}. Task will be retried by Celery.")
        raise # Re-raise to let Celery handle the retry
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred during Gemini processing for attachment {attachment_id}: {e}", exc_info=True)
        if attachment:
            attachment.processed = True # Mark as processed to avoid retry loops on permanent errors
            attachment.extracted_data = {"error": str(e), "status": "failed"}
            attachment.save(update_fields=['processed', 'extracted_data'])
        raise
    finally:
        # 9. Clean up: Delete the file from the Gemini service
        if uploaded_file:
            try:
                logger.info(f"{log_prefix} Deleting temporary file from Gemini service: {uploaded_file.name}")
                # Use the client instance to delete the file
                client.files.delete(name=uploaded_file.name)
            except Exception as e:
                logger.error(f"{log_prefix} Failed to delete uploaded Gemini file {uploaded_file.name}: {e}")

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