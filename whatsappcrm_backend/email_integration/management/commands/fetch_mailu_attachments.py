import os
import uuid
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
import email
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_with_gemini
from email_integration.models import EmailAttachment, EmailAccount

class Command(BaseCommand):
    help = "Fetches attachments from all active email accounts specified in the EmailAccount model."

    def handle(self, *args, **kwargs):
        accounts = EmailAccount.objects.filter(is_active=True)
        if not accounts.exists():
            self.stdout.write(self.style.WARNING("No active email accounts found in the database. Nothing to fetch."))
            return

        for account in accounts:
            self.stdout.write(f"--- Processing account: {account.name} ---")
            try:
                with IMAPClient(account.imap_host, ssl=True, timeout=60) as server:
                    server.login(account.imap_user, account.imap_password)
                    server.select_folder('INBOX')
                    messages = server.search(['UNSEEN'])
                    self.stdout.write(f"Found {len(messages)} unseen messages in '{account.name}'.")

                    if not messages:
                        continue

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
                                self.stderr.write(self.style.ERROR(f"Could not parse date '{date_str}' for a message in '{account.name}': {e}"))

                        for part in msg.walk():
                            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                                continue
                            
                            filename = part.get_filename()
                            if filename:
                                unique_name = f"mailu_{uuid.uuid4().hex}_{filename}"
                                media_path = os.path.join('attachments', unique_name)
                                file_content = part.get_payload(decode=True)
                                
                                # Ensure file content is not None before saving
                                if file_content is None:
                                    self.stderr.write(self.style.ERROR(f"Skipping attachment '{filename}' due to empty content."))
                                    continue

                                default_storage.save(media_path, ContentFile(file_content))
                                
                                attachment = EmailAttachment.objects.create(
                                    account=account,  # Link the attachment to the account
                                    file=media_path,
                                    filename=filename,
                                    sender=sender,
                                    subject=subject,
                                    email_date=email_date_obj
                                )
                                self.stdout.write(self.style.SUCCESS(f"Saved attachment: {filename} (DB id: {attachment.id}) from account '{account.name}'"))
                                
                                process_attachment_with_gemini.delay(attachment.id)
                                self.stdout.write(self.style.WARNING(f"Triggered Gemini processing for attachment id: {attachment.id}"))
            
            except IMAPClientError as e:
                self.stderr.write(self.style.ERROR(f"IMAP connection failed for account '{account.name}': {e}"))
                continue # Continue to the next account
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An unexpected error occurred for account '{account.name}': {e}"))
                continue # Continue to the next account
