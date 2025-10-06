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

@shared_task(bind=True)
def process_attachment_ocr(self, attachment_id):
    """
    Processes an email attachment to extract text using direct extraction for PDFs
    and OCR as a fallback or for images.
    """
    log_prefix = f"[OCR Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Starting OCR processing for EmailAttachment ID: {attachment_id}")
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        file_path = attachment.file.path
        extracted_text = ''

        if file_path.lower().endswith('.pdf'):
            try:
                text = extract_pdf_text(file_path)
                if text and text.strip():
                    extracted_text = text
                    logger.info(f"{log_prefix} Successfully extracted text directly from PDF.")
            except Exception as e:
                logger.warning(f"{log_prefix} Direct text extraction from PDF failed, will fall back to OCR. Error: {e}")

            if not extracted_text:
                logger.info(f"{log_prefix} Falling back to OCR for PDF.")
                images = convert_from_path(file_path)
                ocr_text_parts = [pytesseract.image_to_string(image) for image in images]
                extracted_text = "\n\n".join(ocr_text_parts)
                logger.info(f"{log_prefix} Successfully performed OCR on PDF.")
        else:
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image)
            logger.info(f"{log_prefix} Successfully performed OCR on image.")

        send_receipt_confirmation_email.delay(attachment_id)

        attachment.ocr_text = extracted_text
        attachment.processed = True
        attachment.save(update_fields=['ocr_text', 'processed', 'updated_at'])
        logger.info(f"{log_prefix} Successfully processed and saved text for attachment {attachment_id}.")
        
        # Chain the new Gemini processing task instead of the old regex parser
        process_document_with_gemini.delay(attachment_id)
        
        return f"Successfully processed attachment {attachment_id}. Chaining parsing task."
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred: {e}", exc_info=True)
        raise

def _parse_sales_invoice(text: str, attachment: 'EmailAttachment', log_prefix: str):
    """
    A dedicated parser for sales invoices, updated to handle the specific format
    of the provided TV Sales & Home invoice.
    """
    logger.info(f"{log_prefix} Identified document as Sales Invoice. Parsing...")

    # --- Regex Patterns (Refined for the sample invoice) ---
    invoice_num_pattern = re.compile(r'Customer\s*Reference\s*No[:\s]*([A-Z0-9/ -]+)', re.IGNORECASE)
    date_pattern = re.compile(r'Date[:\s]*(\d{2}-\d{2}-\d{4})', re.IGNORECASE)
    total_pattern = re.compile(r'Invoice\s*Total,\s*USD.*?([\d,]+\.\d{2})', re.IGNORECASE)
    customer_name_pattern = re.compile(r'^\s*([A-Z]+\s+[A-Z]+\s+[A-Z]+(?:\s+[A-Z]+)?)\s*$', re.MULTILINE)

    # --- Extract Header Data ---
    extracted_data = {
        "document_type": "invoice",
        "invoice_number": None,
        "invoice_date": None,
        "total_amount": None,
        "customer_name": None,
        "line_items": [],
    }

    # Find Invoice Number
    match = invoice_num_pattern.search(text)
    if match:
        extracted_data["invoice_number"] = match.group(1).strip()
        logger.info(f"{log_prefix} Found Invoice Number: {extracted_data['invoice_number']}")

    # Find Invoice Date
    match = date_pattern.search(text)
    if match:
        try:
            date_str = match.group(1)
            extracted_data["invoice_date"] = datetime.strptime(date_str, '%d-%m-%Y').date().isoformat()
            logger.info(f"{log_prefix} Found and parsed Invoice Date: {extracted_data['invoice_date']}")
        except ValueError:
            logger.warning(f"{log_prefix} Found date string '{date_str}' but could not parse it.")

    # Find Total Amount
    match = total_pattern.search(text)
    if match:
        try:
            amount_str = match.group(1).replace(',', '')
            extracted_data["total_amount"] = float(Decimal(amount_str))
            logger.info(f"{log_prefix} Found Total Amount: {extracted_data['total_amount']}")
        except InvalidOperation:
            logger.warning(f"{log_prefix} Could not convert total amount '{match.group(1)}' to Decimal.")

    # Find Customer Name
    match = customer_name_pattern.search(text)
    if match:
        potential_name = match.group(1).strip()
        if "BORROWDALE" not in potential_name:
             extracted_data["customer_name"] = potential_name
             logger.info(f"{log_prefix} Found Customer Name: {extracted_data['customer_name']}")

    # --- Extract Line Items (New Robust Logic) ---
    try:
        # Make the header regex more flexible to handle OCR variations and different layouts.
        # This pattern looks for the key columns, allowing other text or newlines between them.
        header = r'Description\s+Qty\s+Price.*?Total\s+Amount'
        footer = 'Total 15% VAT'
        
        start_match = re.search(header, text, re.IGNORECASE)
        end_match = re.search(footer, text, re.IGNORECASE)
        
        if not start_match:
            logger.error(f"{log_prefix} COULD NOT FIND LINE ITEM HEADER. Parsing of line items will fail.")
            return extracted_data

        start_index = start_match.end()
        end_index = end_match.start() if end_match else len(text)

        line_items_block = text[start_index:end_index].strip()
        
        line_item_pattern = re.compile(
            r'^(?P<description>.+?)\s+'
            r'(?P<quantity>\d+)\s+'
            r'(?P<price>[\d,.]+\.\d{3})\s+'
            r'(?P<vat>[\d,.]+\.\d{2})\s+'
            r'(?P<total>[\d,.]+\.\d{2})$'
        )

        processed_lines = []
        for line in line_items_block.splitlines():
            line = line.strip()
            if not line:
                continue
            if processed_lines and not re.search(r'\d+\s+[\d,.]+\s+[\d,.]+\s+[\d,.]+$', line):
                processed_lines[-1] = f"{processed_lines[-1]} {line}"
            else:
                processed_lines.append(line)
        
        for line in processed_lines:
            cleaned_line = re.sub(r'^[A-Z]{2}-\s+', '', line).strip()
            item_match = line_item_pattern.search(cleaned_line)
            
            if item_match:
                extracted_data["line_items"].append({
                    "quantity": int(item_match.group('quantity')),
                    "description": item_match.group('description').strip(),
                    "unit_price": float(Decimal(item_match.group('price').replace(',', ''))),
                    "vat_amount": float(Decimal(item_match.group('vat').replace(',', ''))),
                    "line_total": float(Decimal(item_match.group('total').replace(',', ''))),
                })

        logger.info(f"{log_prefix} Found {len(extracted_data['line_items'])} line items.")
    except Exception as e:
        logger.error(f"{log_prefix} Failed to parse line items: {e}", exc_info=True)

    return extracted_data

def _parse_job_card(text: str, attachment: 'EmailAttachment', log_prefix: str):
    """
    A placeholder parser for job cards.
    """
    logger.info(f"{log_prefix} Identified document as Job Card. Parsing...")
    pass

@shared_task(bind=True, name="email_integration.process_document_with_gemini")
def process_document_with_gemini(self, attachment_id):
    """
    Uses Google's Gemini Pro model to extract structured data from document text.
    """
    log_prefix = f"[Gemini Task ID: {self.request.id}]"
    logger.info(f"{log_prefix} Starting Gemini processing for EmailAttachment ID: {attachment_id}")

    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)
    except EmailAttachment.DoesNotExist:
        logger.error(f"{log_prefix} Could not find EmailAttachment with ID {attachment_id}.")
        return f"Error: Attachment {attachment_id} not found."

    if not attachment.ocr_text:
        logger.warning(f"{log_prefix} No OCR text found for attachment {attachment_id}. Skipping Gemini processing.")
        return f"Skipped: No OCR text for attachment {attachment_id}."

    try:
        # Fetch the API key from the new AIProvider model
        # We fetch the full object now to update it later.
        active_provider = AIProvider.objects.get(provider='google_gemini', is_active=True)
    except (AIProvider.DoesNotExist, AIProvider.MultipleObjectsReturned) as e:
        logger.error(f"{log_prefix} Could not retrieve Gemini API key from database: {e}")
        # Re-raise to fail the task so it can be retried once the DB is configured correctly.
        raise ValueError(f"Gemini API key configuration error: {e}")

    # NOTE on library: The correct package to install is `google-genai` from PyPI.
    # The `google-generativeai` package is deprecated.
    # However, the import statement remains `import google.generativeai`.
    # We configure it here with the key fetched from the database.
    genai.configure(api_key=active_provider.api_key)
    model = genai.GenerativeModel('gemini-pro')

    # This prompt is crucial. It instructs the model on what to extract and the exact JSON format to return.
    # It remains unchanged.
    # You can customize the `json_schema` to fit any other document types you need to process.
    prompt = """
    Analyze the following text extracted from a business document (likely an invoice or job card).
    Based on the content, identify the document type and extract key information into a structured JSON object.

    The desired JSON schema is:
    {{
      "document_type": "invoice" | "job_card" | "quote" | "unclassified",
      "invoice_number": "string" | null,
      "invoice_date": "YYYY-MM-DD" | null,
      "customer_name": "string" | null,
      "total_amount": number | null,
      "line_items": [
        {{
          "description": "string",
          "quantity": number,
          "unit_price": number,
          "line_total": number
        }}
      ] | null
    }}

    - If a field is not found, its value should be null.
    - The `invoice_date` must be in 'YYYY-MM-DD' format.
    - `total_amount`, `quantity`, `unit_price`, and `line_total` must be numbers (float or integer), not strings.
    - If the document does not seem to be an invoice, job card, or quote, classify it as "unclassified" and leave other fields null.
    - Return ONLY the JSON object, with no other text or markdown formatting.

    Here is the document text:
    ---
    {text}
    ---
    """.format(text=attachment.ocr_text)

    try:
        logger.info(f"{log_prefix} Sending request to Gemini API for attachment {attachment_id}.")
        
        # The Gemini library doesn't directly expose headers. We access the underlying
        # transport to get the raw response and headers.
        raw_response, response_body = model._client._client.request(
            method='POST',
            url=model._client._api_endpoint + "/v1/models/gemini-pro:generateContent",
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'contents': [{'parts': [{'text': prompt}]}]})
        )
        
        # Update rate limit info on the provider model
        _update_provider_rate_limit(active_provider, raw_response, log_prefix)

        # Check for non-200 status codes which indicate an error
        if raw_response.status != 200:
            error_message = f"Gemini API returned status {raw_response.status}: {response_body.decode('utf-8')}"
            logger.error(f"{log_prefix} {error_message}")
            # Raise a specific exception for rate limiting
            if raw_response.status == 429:
                raise core_exceptions.ResourceExhausted(error_message)
            raise Exception(error_message)

        response = genai.types.GenerateContentResponse.from_dict(json.loads(response_body))
        
        # Clean up the response to ensure it's valid JSON
        cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        extracted_data = json.loads(cleaned_response_text)
        
        logger.info(f"{log_prefix} Successfully received and parsed Gemini response for attachment {attachment_id}.")

        # Save the structured data back to the ocr_text field as a JSON string
        attachment.ocr_text = json.dumps(extracted_data, indent=2)
        attachment.save(update_fields=['ocr_text', 'updated_at'])

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