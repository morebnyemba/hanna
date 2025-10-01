import os
import uuid
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
import email
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_ocr
from email_integration.models import EmailAttachment

load_dotenv()  # Loads .env file

class Command(BaseCommand):
    help = "Fetch attachments from Mailu mailbox and save to media directory"

    def handle(self, *args, **kwargs):
        host = os.getenv("MAILU_IMAP_HOST")
        user = os.getenv("MAILU_IMAP_USER")
        password = os.getenv("MAILU_IMAP_PASS")
        try:
            with IMAPClient(host) as server:
                server.login(user, password)
                server.select_folder('INBOX')
                messages = server.search(['UNSEEN'])
                self.stdout.write(f"Found {len(messages)} unseen messages.")
                for uid, message_data in server.fetch(messages, 'RFC822').items():
                    msg = email.message_from_bytes(message_data[b'RFC822'])
                    sender = msg.get('From', '')
                    subject = msg.get('Subject', '')
                    date_str = msg.get('Date', '')
                    email_date_obj = None
                    if date_str:
                        try:
                            email_date_obj = parsedate_to_datetime(date_str)
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"Could not parse date '{date_str}': {e}"))

                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                            continue
                        
                        filename = part.get_filename()
                        if filename:
                            unique_name = f"mailu_{uuid.uuid4().hex}_{filename}"
                            media_path = os.path.join('attachments', unique_name)
                            file_content = part.get_payload(decode=True)
                            saved_path = default_storage.save(media_path, ContentFile(file_content))
                            
                            attachment = EmailAttachment.objects.create(
                                file=media_path,
                                filename=filename,
                                sender=sender,
                                subject=subject,
                                email_date=email_date_obj
                            )
                            self.stdout.write(self.style.SUCCESS(f"Saved attachment: {filename} (DB id: {attachment.id})"))
                            
                            process_attachment_ocr.delay(attachment.id)
                            self.stdout.write(self.style.WARNING(f"Triggered OCR processing for attachment id: {attachment.id}"))
        except IMAPClientError as e:
            self.stderr.write(self.style.ERROR(f"IMAP connection failed: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
