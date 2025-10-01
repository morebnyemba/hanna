import os
from celery import shared_task
from django.conf import settings
from .email_attachment import EmailAttachment
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

@shared_task
def process_attachment_ocr(attachment_id):
    try:
        attachment = EmailAttachment.objects.get(id=attachment_id)
        file_path = attachment.file.path if hasattr(attachment.file, 'path') else os.path.join(settings.MEDIA_ROOT, attachment.file.name)
        ocr_text = ''
        if file_path.lower().endswith('.pdf'):
            images = convert_from_path(file_path)
            for image in images:
                ocr_text += pytesseract.image_to_string(image)
        else:
            image = Image.open(file_path)
            ocr_text = pytesseract.image_to_string(image)
        attachment.ocr_text = ocr_text
        attachment.processed = True
        attachment.save()
        return True
    except Exception as e:
        return str(e)