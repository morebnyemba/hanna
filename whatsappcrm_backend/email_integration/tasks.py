import os
import logging
import re
import json
from datetime import datetime
from celery import shared_task, chain
from .models import EmailAttachment, ParsedInvoice
import pytesseract
from pdfminer.high_level import extract_text as extract_pdf_text
from pdf2image import convert_from_path
from PIL import Image
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.core.mail import send_mail
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
        
        # Use the email address of the monitored inbox as the sender.
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
        # We don't re-raise here because failing to send a confirmation should not stop the main OCR process.

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

        # Send a confirmation email to the sender now that we've confirmed the attachment exists.
        # This ensures the sender gets a prompt notification.
        send_receipt_confirmation_email.delay(attachment_id)

        attachment.ocr_text = extracted_text
        attachment.processed = True
        attachment.save(update_fields=['ocr_text', 'processed', 'updated_at'])
        logger.info(f"{log_prefix} Successfully processed and saved text for attachment {attachment_id}.")
        
        # Chain the parsing task to run immediately after this one succeeds
        parse_ocr_text.delay(attachment_id)
        
        return f"Successfully processed attachment {attachment_id}. Chaining parsing task."
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred: {e}", exc_info=True)
        raise  # Re-raise the exception to mark the task as FAILED in Celery

def _parse_sales_invoice(text: str, attachment: EmailAttachment, log_prefix: str):
    """
    A dedicated parser for sales invoices based on the provided examples.
    """
    logger.info(f"{log_prefix} Identified document as Sales Invoice. Parsing...")

    # --- Define more robust Regex Patterns for Invoices ---
    # Invoice Number: More flexible keywords and allows hyphens.
    invoice_num_pattern = re.compile(r'(?:Invoice\s*No|Invoice\s*#|Customer\s*Reference\s*No|Ref\s*No)[:\s#]*([A-Z0-9/ -]+)', re.IGNORECASE)
    
    # Date: Flexible date patterns (DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY, etc.)
    date_pattern = re.compile(r'(?:Date|Invoice\s*Date)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', re.IGNORECASE)
    
    # Total Amount: More robust labels and optional currency symbols.
    total_pattern = re.compile(r'(?:Total\s*Amount|Invoice\s*Total|Amount\s*Due|Balance\s*Due|Grand\s*Total)[:\s$]*[A-Z]{0,3}\s*([\d,]+\.\d{2})', re.IGNORECASE)

    # Customer Name: More flexible, looking for common labels like "Bill To" and capturing the line below it.
    customer_name_pattern = re.compile(r'(?:Bill\s*To|Customer\s*Name|Client\s*Name)[:\s]*\n?([^\n]+)', re.IGNORECASE)

    # --- Extract Data ---
    extracted_data = {
        "document_type": "invoice",
        "invoice_number": None,
        "invoice_date": None,
        "total_amount": None,
        "customer_name": None,
        "line_items": [],
    }

    match = invoice_num_pattern.search(text)
    if match:
        extracted_data["invoice_number"] = match.group(1).strip()
        logger.info(f"{log_prefix} Found Invoice Number: {extracted_data['invoice_number']}")

    match = date_pattern.search(text)
    if match:
        try:
            date_str = match.group(1)
            # Attempt to parse common date formats
            for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%y', '%d/%m/%y'):
                try:
                    extracted_data["invoice_date"] = datetime.strptime(date_str, fmt).date().isoformat() # Store as ISO string
                    logger.info(f"{log_prefix} Found and parsed Invoice Date: {extracted_data['invoice_date']}")
                    break
                except ValueError:
                    continue
            if not extracted_data["invoice_date"]:
                logger.warning(f"{log_prefix} Found a date-like string '{date_str}' but could not parse it into a known format.")
        except Exception as e:
            logger.error(f"{log_prefix} Error processing date string '{match.group(1)}': {e}")

    match = total_pattern.search(text)
    if match:
        try:
            amount_str = match.group(1).replace(',', '')  # Remove commas
            extracted_data["total_amount"] = float(Decimal(amount_str)) # Store as float for JSON
            logger.info(f"{log_prefix} Found Total Amount: {extracted_data['total_amount']}")
        except InvalidOperation:
            logger.warning(f"{log_prefix} Found a total-like string '{match.group(1)}' but could not convert to Decimal.")

    match = customer_name_pattern.search(text)
    if match:
        # Clean up potential leading/trailing junk characters
        extracted_data["customer_name"] = re.sub(r'[^a-zA-Z0-9\s]', '', match.group(1)).strip()
        logger.info(f"{log_prefix} Found Customer Name: {extracted_data['customer_name']}")

    # --- Extract Line Items ---
    # This is more complex and requires identifying the table-like structure.
    # We'll look for a block of text between a header and a subtotal/total line.
    try:
        # Find the start of the line items section (e.g., after a header like "Description")
        # and the end (e.g., before "Subtotal").
        line_items_header_pattern = re.compile(r'(?:Description|Item|Product|Details)', re.IGNORECASE)
        line_items_footer_pattern = re.compile(r'(?:Subtotal|Sub-total|Total|Amount\s*Due)', re.IGNORECASE)
        
        header_match = line_items_header_pattern.search(text)
        footer_match = line_items_footer_pattern.search(text, pos=header_match.end() if header_match else 0)

        start_index = header_match.end() if header_match else 0
        end_index = footer_match.start() if footer_match else len(text)

        line_items_block = text[start_index:end_index]

        # Regex to capture a typical line item: (optional qty) (description) (unit price) (line total)
        # This pattern is flexible: it looks for a line ending in two decimal numbers.
        line_item_pattern = re.compile(
            r'^(?P<description>.+?)\s+(?P<unit_price>[\d,]+\.\d{2})\s+(?P<line_total>[\d,]+\.\d{2})\s*$',
            re.MULTILINE
        )

        for item_match in line_item_pattern.finditer(line_items_block):
            description_part = item_match.group('description').strip()
            
            # Try to extract a quantity from the beginning of the description
            qty_match = re.match(r'^(?P<quantity>\d+)\s+(?P<desc_text>.+)', description_part)
            quantity = int(qty_match.group('quantity')) if qty_match else 1
            description = qty_match.group('desc_text').strip() if qty_match else description_part

            extracted_data["line_items"].append({
                "quantity": quantity,
                "description": description,
                "unit_price": float(Decimal(item_match.group('unit_price').replace(',', ''))),
                "line_total": float(Decimal(item_match.group('line_total').replace(',', ''))),
            })
        logger.info(f"{log_prefix} Found {len(extracted_data['line_items'])} line items.")
    except Exception as e:
        logger.error(f"{log_prefix} Failed to parse line items: {e}", exc_info=True)

    return extracted_data

def _parse_job_card(text: str, attachment: EmailAttachment, log_prefix: str):
    """
    A placeholder parser for job cards.
    This can be built out with regex specific to the job card format.
    """
    logger.info(f"{log_prefix} Identified document as Job Card. Parsing...")
    # TODO: Add regex and logic to parse job card details (Document Number, Customer, Fault, etc.)
    # TODO: Create a `ParsedJobCard` model to store this data.
    pass

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
        
        # --- Document Classification and Dispatch ---
        text_lower = text.lower()
        if 'fiscal tax invoice' in text_lower and 'customer reference no' in text_lower:
            extracted_structured_data = _parse_sales_invoice(text, attachment, log_prefix)
            
            # Save to ParsedInvoice model
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
            # TODO: If you create a ParsedJobCard model, save data here.
            # For now, it will just be saved to attachment.ocr_text as JSON.
        else:
            logger.warning(f"{log_prefix} Could not classify document type for attachment {attachment_id}. Skipping detailed parsing.")
            # If unclassified, we can still save a basic JSON structure
            extracted_structured_data["document_type"] = "unclassified"

        # Save the structured data as JSON to the attachment's ocr_text field
        attachment.ocr_text = json.dumps(extracted_structured_data, indent=2)
        attachment.save(update_fields=['ocr_text', 'updated_at'])

        return f"Successfully parsed data for attachment {attachment_id}."
    except ObjectDoesNotExist:
        logger.error(f"{log_prefix} Could not find EmailAttachment with ID {attachment_id}.")
        # Do not re-raise, as the task cannot be retried if the object is gone.
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred during parsing: {e}", exc_info=True)
        raise

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
        raise # Re-raise the exception to mark the task as FAILED