from whatsappcrm_backend.whatsappcrm_backend.tasks import process_attachment_ocr
from whatsappcrm_backend.whatsappcrm_backend.models import EmailAttachment
import os
import uuid
from imapclient import IMAPClient
import email
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from dotenv import load_dotenv

load_dotenv()  # Loads .env file

class Command(BaseCommand):
    help = "Fetch attachments from Mailu mailbox and save to media directory"

    def handle(self, *args, **kwargs):
        host = os.getenv("MAILU_IMAP_HOST")
        user = os.getenv("MAILU_IMAP_USER")
        password = os.getenv("MAILU_IMAP_PASS")
        with IMAPClient(host) as server:
            server.login(user, password)
            server.select_folder('INBOX')
            messages = server.search(['UNSEEN'])
            for uid, message_data in server.fetch(messages, 'RFC822').items():
                msg = email.message_from_bytes(message_data[b'RFC822'])
                sender = msg.get('From', '')
                subject = msg.get('Subject', '')
                email_date = msg.get('Date', '')
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    filename = part.get_filename()
                    if filename:
                        # Ensure unique filename
                        unique_name = f"mailu_{uuid.uuid4().hex}_{filename}"
                        media_path = os.path.join('attachments', unique_name)
                        file_content = part.get_payload(decode=True)
                        saved_path = default_storage.save(media_path, ContentFile(file_content))
                        full_path = default_storage.path(saved_path)
                        # Create EmailAttachment record
                        attachment = EmailAttachment.objects.create(
                            file=media_path,
                            filename=filename,
                            sender=sender,
                            subject=subject,
                            email_date=email_date
                        )
                        self.stdout.write(self.style.SUCCESS(f"Saved attachment: {full_path} (DB id: {attachment.id}, sender: {sender}, subject: {subject}, date: {email_date})"))
                        # Trigger OCR processing asynchronously
                        process_attachment_ocr.delay(attachment.id)
                        self.stdout.write(self.style.WARNING(f"Triggered OCR processing for attachment id: {attachment.id}"))
