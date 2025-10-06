import os
import logging
import re
from google.api_core import exceptions as core_exceptions
import json
from datetime import datetime
from celery import shared_task, chain

from django.utils import timezone
import google.generativeai as genai
from .models import EmailAttachment, ParsedInvoice
import pytesseract
from pdfminer.high_level import extract_text as extract_pdf_text
from pdf2image import convert_from_path
from PIL import Image
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
            genai.configure(api_key=active_provider.api_key)
        except (AIProvider.DoesNotExist, AIProvider.MultipleObjectsReturned) as e:
            raise ValueError(f"Gemini API key configuration error: {e}")

        # 2. Upload the local file to the Gemini API
        file_path = attachment.file.path
        logger.info(f"{log_prefix} Uploading file to Gemini: {file_path}")
        uploaded_file = genai.upload_file(path=file_path)
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
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            [prompt, uploaded_file],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )

        # 5. Parse the extracted JSON data
        extracted_data = json.loads(response.text)

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
                genai.delete_file(name=uploaded_file.name)
            except Exception as e:
                logger.error(f"{log_prefix} Failed to delete uploaded Gemini file {uploaded_file.name}: {e}")


def _save_parsed_invoice_from_gemini_data(attachment: EmailAttachment, data: dict, log_prefix: str):
    """Helper function to save extracted invoice data to the ParsedInvoice model."""
    invoice_date_obj = None
    if data.get("invoice_date"):
        try:
            invoice_date_obj = datetime.strptime(data["invoice_date"], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"{log_prefix} Gemini returned date '{data.get('invoice_date')}' which could not be parsed.")

    total_amount_decimal = None
    if data.get("total_amount") is not None:
        try:
            total_amount_decimal = Decimal(str(data["total_amount"]))
        except (InvalidOperation, TypeError):
            logger.warning(f"{log_prefix} Gemini returned total amount '{data.get('total_amount')}' which could not be converted to Decimal.")

    ParsedInvoice.objects.update_or_create(
        attachment=attachment,
        defaults={
            'invoice_number': data.get("invoice_number"),
            'invoice_date': invoice_date_obj,
            'total_amount': total_amount_decimal,
        }
    )
    logger.info(f"{log_prefix} Saved/Updated ParsedInvoice record from Gemini data for attachment {attachment.id}.")

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
        # Clean up the response to ensure it's valid JSON
        cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        extracted_data = json.loads(cleaned_response_text)
        
        logger.info(f"{log_prefix} Successfully received and parsed Gemini response for attachment {attachment_id}.")

        # Save the structured data back to the ocr_text field as a JSON string
        attachment.ocr_text = json.dumps(extracted_data, indent=2)
        attachment.save(update_fields=['ocr_text', 'updated_at'])

        # Now that processing is complete, mark as processed and send confirmation.
        attachment.processed = True
        attachment.save(update_fields=['processed'])
        send_receipt_confirmation_email.delay(attachment_id)

        # (Optional but Recommended) Save to the structured ParsedInvoice model
        if extracted_data.get("document_type") == "invoice":
            _save_parsed_invoice_from_gemini_data(attachment, extracted_data, log_prefix)

        return f"Successfully processed attachment {attachment_id} with Gemini."

    except core_exceptions.ResourceExhausted as e:
        logger.warning(f"{log_prefix} Gemini API rate limit exceeded for attachment {attachment_id}: {e}. The task will be retried automatically by Celery.")
        # Re-raise to let Celery handle the retry with its backoff strategy.
        # You can configure `autoretry_for` on the @shared_task decorator for more control.
        raise

    except Exception as e:
        logger.error(f"{log_prefix} An error occurred during Gemini processing for attachment {attachment_id}: {e}", exc_info=True)
        # Re-raise the exception to mark the Celery task as failed for potential retry.
        raise

@shared_task(bind=True)
def parse_ocr_text(self, attachment_id):
    """
    Parses the ocr_text of an EmailAttachment to extract structured data.
    """
    log_prefix = f"[Parse Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Starting text parsing for EmailAttachment ID: {attachment_id}")
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        if not attachment.ocr_text:
            logger.warning(f"{log_prefix} No OCR text found for attachment {attachment_id}. Skipping parsing.")
            return f"Skipped: No OCR text for attachment {attachment_id}."

        text = attachment.ocr_text
        extracted_structured_data = {"document_type": "unknown", "raw_text_length": len(text)}
        
        text_lower = text.lower()
        if 'fiscal tax invoice' in text_lower and 'customer reference no' in text_lower:
            extracted_structured_data = _parse_sales_invoice(text, attachment, log_prefix)
            
            invoice_date_obj = None
            if extracted_structured_data.get("invoice_date"):
                try:
                    invoice_date_obj = datetime.strptime(extracted_structured_data["invoice_date"], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    logger.warning(f"{log_prefix} Could not parse date '{extracted_structured_data.get('invoice_date')}' for ParsedInvoice model.")

            parsed_invoice, created = ParsedInvoice.objects.update_or_create(
                attachment=attachment,
                defaults={
                    'invoice_number': extracted_structured_data.get("invoice_number"),
                    'invoice_date': invoice_date_obj,
                    'total_amount': Decimal(str(extracted_structured_data.get("total_amount", 0))) if extracted_structured_data.get("total_amount") is not None else None,
                }
            )
            if created:
                logger.info(f"{log_prefix} Created new ParsedInvoice record for attachment {attachment.id}.")
            else:
                logger.info(f"{log_prefix} Updated existing ParsedInvoice record for attachment {attachment.id}.")

        elif 'customer care job card' in text_lower and 'description of fault' in text_lower:
            extracted_structured_data = _parse_job_card(text, attachment, log_prefix)
        else:
            logger.warning(f"{log_prefix} Could not classify document type for attachment {attachment_id}. Skipping detailed parsing.")
            extracted_structured_data["document_type"] = "unclassified"

        attachment.ocr_text = json.dumps(extracted_structured_data, indent=2)
        attachment.save(update_fields=['ocr_text', 'updated_at'])

        return f"Successfully parsed data for attachment {attachment_id}."
    except ObjectDoesNotExist:
        logger.error(f"{log_prefix} Could not find EmailAttachment with ID {attachment_id}.")
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred during parsing: {e}", exc_info=True)
        raise

def _save_parsed_invoice_from_gemini_data(attachment: EmailAttachment, data: dict, log_prefix: str):
    """Helper function to save extracted invoice data to the ParsedInvoice model."""
    invoice_date_obj = None
    if data.get("invoice_date"):
        try:
            invoice_date_obj = datetime.strptime(data["invoice_date"], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            logger.warning(f"{log_prefix} Gemini returned date '{data.get('invoice_date')}' which could not be parsed.")

    total_amount_decimal = None
    if data.get("total_amount") is not None:
        try:
            total_amount_decimal = Decimal(str(data["total_amount"]))
        except (InvalidOperation, TypeError):
            logger.warning(f"{log_prefix} Gemini returned total amount '{data.get('total_amount')}' which could not be converted to Decimal.")

    ParsedInvoice.objects.update_or_create(
        attachment=attachment,
        defaults={
            'invoice_number': data.get("invoice_number"),
            'invoice_date': invoice_date_obj,
            'total_amount': total_amount_decimal,
        }
    )
    logger.info(f"{log_prefix} Saved/Updated ParsedInvoice record from Gemini data for attachment {attachment.id}.")

def _update_provider_rate_limit(provider: AIProvider, response_headers: dict, log_prefix: str):
    """
    Helper function to parse rate limit headers and update the AIProvider instance.
    """
    try:
        limit = response_headers.get('x-ratelimit-limit')
        remaining = response_headers.get('x-ratelimit-remaining')
        reset_seconds = response_headers.get('x-ratelimit-reset')

        update_fields = []
        if limit is not None:
            provider.rate_limit_limit = int(limit)
            update_fields.append('rate_limit_limit')
        if remaining is not None:
            provider.rate_limit_remaining = int(remaining)
            update_fields.append('rate_limit_remaining')
        if reset_seconds is not None:
            provider.rate_limit_reset_time = timezone.now() + timezone.timedelta(seconds=int(reset_seconds))
            update_fields.append('rate_limit_reset_time')
        
        if update_fields:
            provider.save(update_fields=update_fields)
            logger.info(f"{log_prefix} Updated rate limit info for {provider.provider}: {remaining}/{limit}")
    except (ValueError, TypeError) as e:
        logger.warning(f"{log_prefix} Could not parse rate limit headers: {e}")

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