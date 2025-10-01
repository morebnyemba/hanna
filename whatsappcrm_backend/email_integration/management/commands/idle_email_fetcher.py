import os
import uuid
import email
import time
import logging
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_ocr
from email_integration.models import EmailAttachment

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs a persistent IMAP IDLE worker to listen for new emails and trigger processing."

    def handle(self, *args, **kwargs):
        host = os.getenv("MAILU_IMAP_HOST")
        user = os.getenv("MAILU_IMAP_USER")
        password = os.getenv("MAILU_IMAP_PASS")

        self.stdout.write(self.style.SUCCESS(f"Preparing to connect to IMAP server..."))
        self.stdout.write(f"  Host: {host}")
        self.stdout.write(f"  User: {user}")

        # Mask the password for security before logging
        masked_password = f"{password[:2]}...{password[-2:]}" if password and len(password) > 4 else "(password is short or not set)"
        self.stdout.write(f"  Password: {masked_password}")
        self.stdout.write(f"Connecting...")

        while True: # Main loop to handle reconnects
            try:
                with IMAPClient(host, ssl=False, timeout=300) as server: # Try connecting without SSL
                    server.login(user, password)
                    server.select_folder('INBOX')
                    self.stdout.write(self.style.SUCCESS("Connection successful. Listening for new emails via IDLE..."))

                    while True: # IDLE loop
                        server.idle()
                        responses = server.idle_check(timeout=290) # Check for activity or timeout
                        server.idle_done()

                        if responses:
                            self.stdout.write(self.style.SUCCESS("New email activity detected. Fetching unseen messages..."))
                            messages = server.search(['UNSEEN'])
                            for uid, message_data in server.fetch(messages, 'RFC822').items():
                                self.process_message(message_data)

            except (IMAPClientError, OSError) as e:
                self.stderr.write(self.style.ERROR(f"IMAP connection error: {e}. Reconnecting in 30 seconds..."))
                time.sleep(30)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("IDLE worker stopped by user."))
                break

    def process_message(self, message_data):
        msg = email.message_from_bytes(message_data[b'RFC822'])
        sender = msg.get('From', '')
        subject = msg.get('Subject', '')
        date_str = msg.get('Date', '')
        email_date_obj = parsedate_to_datetime(date_str) if date_str else None

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if filename:
                unique_name = f"mailu_{uuid.uuid4().hex}_{filename}"
                media_path = os.path.join('attachments', unique_name)
                file_content = part.get_payload(decode=True)
                
                attachment = EmailAttachment.objects.create(
                    file=ContentFile(file_content, name=unique_name),
                    filename=filename, sender=sender, subject=subject, email_date=email_date_obj
                )
                self.stdout.write(self.style.SUCCESS(f"Saved attachment: {filename} (DB id: {attachment.id})"))
                
                process_attachment_ocr.delay(attachment.id)
                self.stdout.write(self.style.WARNING(f"Triggered OCR processing for attachment id: {attachment.id}"))