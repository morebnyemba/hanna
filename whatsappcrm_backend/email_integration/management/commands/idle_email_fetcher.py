import os
import uuid
import email
import time
import logging
import imaplib
import socket
import ssl # Import the ssl module
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_with_gemini
from email_integration.models import EmailAttachment, EmailAccount

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs a persistent IMAP IDLE worker to listen for new emails across all active email accounts and triggers processing."

    def handle(self, *args, **kwargs):
        logger.info("Starting IMAP IDLE worker for all accounts...")
        self.stdout.write(self.style.SUCCESS("IMAP IDLE worker started."))

        while True:
            accounts = EmailAccount.objects.filter(is_active=True)
            if not accounts.exists():
                self.stdout.write(self.style.WARNING("No active email accounts found in the database. Sleeping for 60 seconds."))
                time.sleep(60)
                continue

            for account in accounts:
                self.stdout.write(f"--- Processing account: {account.name} ({account.imap_user}) ---")
                logger.info(f"Attempting to connect to IMAP server for account: {account.name}")

                try:
                    while True:
                        try:
                            # Using the hostname directly as requested by the user.
                            server = IMAPClient(account.imap_host, ssl=True, timeout=300)
                            server.login(account.imap_user, account.imap_password)
                            server.select_folder('INBOX')
                            logger.info(f"Successfully connected and selected INBOX for '{account.name}'.")
                            self.stdout.write(self.style.SUCCESS(f"Account '{account.name}' connected. Listening for new emails via IDLE..."))

                            while True:
                                try:
                                    server.idle()
                                    responses = server.idle_check(timeout=29 * 60) 
                                    server.idle_done()

                                    if responses:
                                        logger.info(f"New email activity detected for '{account.name}'.")
                                        self.stdout.write(self.style.SUCCESS(f"New email activity detected for '{account.name}'. Fetching unseen messages..."))
                                        messages = server.search(['UNSEEN'])
                                        for uid, message_data in server.fetch(messages, 'RFC822').items():
                                            self.process_message(account, message_data)
                                except (IMAPClientError, OSError, imaplib.IMAP4.error) as idle_error:
                                    logger.error(f"Error during IDLE for '{account.name}': {idle_error}. Reconnecting...")
                                    break
                                except Exception as e:
                                    logger.exception(f"Unexpected error in IDLE loop for '{account.name}': {e}")
                                    break

                            server.close_folder()
                            server.logout()
                            logger.info(f"Disconnected from IMAP server for '{account.name}'.")
                            break
                        except (IMAPClientError, OSError, imaplib.IMAP4.error) as e:
                            self.stderr.write(self.style.ERROR(f"IMAP connection error for '{account.name}': {e}. Reconnecting in 30 seconds..."))
                            logger.exception(f"Connection error for '{account.name}' occurred:")
                            time.sleep(30)
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"An unexpected error occurred for '{account.name}': {e}. Skipping account for now."))
                            logger.exception(f"Unexpected error for '{account.name}':")
                            break
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING("IMAP worker stopped by user."))
                    return
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Unhandled error processing account '{account.name}': {e}"))
                    logger.exception(f"Unhandled error for account '{account.name}':")
            
            time.sleep(5) 

    def process_message(self, account, message_data):
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
                
                file_content = part.get_payload(decode=True)
                
                if file_content is None:
                    logger.warning(f"Skipping attachment '{filename}' from '{account.name}' due to empty content.")
                    continue

                attachment = EmailAttachment.objects.create(
                    account=account,
                    file=ContentFile(file_content, name="attachments/"+unique_name),
                    filename=filename, 
                    sender=sender, 
                    subject=subject, 
                    email_date=email_date_obj
                )
                self.stdout.write(self.style.SUCCESS(f"Saved attachment: {filename} (DB id: {attachment.id}) from account '{account.name}'"))
                
                process_attachment_with_gemini.delay(attachment.id)
                self.stdout.write(self.style.WARNING(f"Triggered Gemini processing for attachment id: {attachment.id}"))
