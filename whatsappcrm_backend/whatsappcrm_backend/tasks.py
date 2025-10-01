import os
from celery import shared_task
from django.conf import settings
from .models import EmailAttachment
import pytesseract
from pdfminer.high_level import extract_text as extract_pdf_text
from pdf2image import convert_from_path
from PIL import Image

@shared_task
def process_attachment_ocr(attachment_id):
    try:
        attachment = EmailAttachment.objects.get(pk=attachment_id)
        file_path = attachment.file.path
        ocr_text = ''

        if file_path.lower().endswith('.pdf'):
            # 1. Try to extract text directly from the PDF
            try:
                text = extract_pdf_text(file_path)
                if text and text.strip():
                    ocr_text = text
            except Exception:
                # This might fail on scanned/image-only PDFs, which is expected.
                pass
            
            # 2. If no text was extracted, fall back to OCR
            if not ocr_text:
                try:
                    images = convert_from_path(file_path)
                    ocr_text_parts = [pytesseract.image_to_string(image) for image in images]
                    ocr_text = "\n\n".join(ocr_text_parts)
                except Exception as e:
                    ocr_text = f"[PDF OCR failed: {e}]"

        else:
            try:
                image = Image.open(file_path)
                ocr_text = pytesseract.image_to_string(image)
            except Exception as e:
                ocr_text = f"[Image OCR failed: {e}]"

        attachment.ocr_text = ocr_text
        attachment.processed = True
        attachment.save()
        return True
    except Exception as e:
        return str(e)