import os
import logging
import re
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

    # Send a confirmation email to the sender as the first step.
    send_receipt_confirmation_email.delay(attachment_id)

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

    # --- Define more specific Regex Patterns for Invoices ---
    # Invoice Number: Looks for "Customer Reference No" or "Invoice No". Prioritizes the reference number.
    invoice_num_pattern = re.compile(r'(?:Customer\s*Reference\s*No|Invoice\s*No)[:\s]*([A-Z0-9/]+)', re.IGNORECASE)
    
    # Date: Looks for a date following a "Date:" label.
    date_pattern = re.compile(r'Date[:\s]*(\d{2}[-]\d{2}[-]\d{4})', re.IGNORECASE)
    
    # Total Amount: Looks for "Invoice Total (USD)" or similar.
    total_pattern = re.compile(r'(?:Invoice\s*Total|Total)\s*\(USD\)[:\s$]*([\d,]+\.\d{2})', re.IGNORECASE)

    # Customer Name: Looks for a name following a "Name:" label in the customer section.
    # Using a negative lookbehind to avoid capturing the vendor name.
    customer_name_pattern = re.compile(r'(?<!Vendor Information:\n)Name[:\s]*(.*)', re.IGNORECASE)

    # --- Extract Data ---
    invoice_number = None
    invoice_date = None
    total_amount = None
    customer_name = None # New field to extract

    match = invoice_num_pattern.search(text)
    if match:
        invoice_number = match.group(1).strip()
        logger.info(f"{log_prefix} Found Invoice Number: {invoice_number}")

    match = date_pattern.search(text)
    if match:
        try:
            date_str = match.group(1)
            # The format is DD-MM-YYYY
            invoice_date = datetime.strptime(date_str, '%d-%m-%Y').date()
            logger.info(f"{log_prefix} Found Invoice Date: {invoice_date}")
        except ValueError:
            logger.warning(f"{log_prefix} Found a date-like string '{date_str}' but could not parse it.")

    match = total_pattern.search(text)
    if match:
        try:
            amount_str = match.group(1).replace(',', '') # Remove commas
            total_amount = Decimal(amount_str)
            logger.info(f"{log_prefix} Found Total Amount: {total_amount}")
        except InvalidOperation:
            logger.warning(f"{log_prefix} Found a total-like string '{match.group(1)}' but could not convert to Decimal.")

    match = customer_name_pattern.search(text)
    if match:
        customer_name = match.group(1).strip()
        logger.info(f"{log_prefix} Found Customer Name: {customer_name}")

    # --- Save the Extracted Data ---
    # We can also link this to an Order model if the invoice number matches.
    parsed_invoice, created = ParsedInvoice.objects.update_or_create(
        attachment=attachment,
        defaults={
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'total_amount': total_amount,
            # We can add customer_name to the model if we want to store it.
        }
    )
    
    if created:
        logger.info(f"{log_prefix} Created new ParsedInvoice record for attachment {attachment.id}.")
    else:
        logger.info(f"{log_prefix} Updated existing ParsedInvoice record for attachment {attachment.id}.")

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
        
        # --- Document Classification and Dispatch ---
        text_lower = text.lower()
        if 'fiscal tax invoice' in text_lower and 'customer reference no' in text_lower:
            _parse_sales_invoice(text, attachment, log_prefix)
        elif 'customer care job card' in text_lower and 'description of fault' in text_lower:
            _parse_job_card(text, attachment, log_prefix)
        else:
            logger.warning(f"{log_prefix} Could not classify document type for attachment {attachment_id}. Skipping detailed parsing.")
            return f"Skipped: Could not classify document {attachment_id}."

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