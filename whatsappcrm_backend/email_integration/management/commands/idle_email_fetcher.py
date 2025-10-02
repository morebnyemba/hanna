import os
import uuid
import email
import logging
import ssl
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_ocr
from email_integration.models import EmailAttachment

logger = logging.getLogger(__name__)
import time
class Command(BaseCommand):
    help = "Runs a persistent IMAP IDLE worker to listen for new emails and trigger processing."

    def handle(self, *args, **kwargs):
        host = os.getenv("MAILU_IMAP_HOST")
        user = os.getenv("MAILU_IMAP_USER")
        password = os.getenv("MAILU_IMAP_PASS")

        logger.info("Starting IMAP IDLE worker...")
        logger.info(f"  Host: {host}")
        logger.info(f"  User: {user}")

        # Mask the password for security before logging
        masked_password = f"{password[:2]}...{password[-2:]}" if password and len(password) > 4 else "(password is short or not set)"
        logger.info(f"  Password: {masked_password}")

        while True: # Main loop to handle reconnects
            try:
                # When connecting to an internal service name ('imap'), we use SSL but disable
                # hostname verification because the internal certificate is for 'mail.hanna.co.zw'.
                # This is secure as the connection is contained within the private Docker network.
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                with IMAPClient(host, ssl=True, ssl_context=ssl_context, timeout=300) as server:
                    server.login(user, password)
                    server.select_folder('INBOX')
                    logger.info("Connection successful. Listening for new emails via IDLE...")

                    while True: # IDLE loop
                        server.idle()
                        responses = server.idle_check(timeout=290) # Check for activity or timeout
                        server.idle_done()

                        if responses: # If there's any activity
                            logger.info("New email activity detected. Fetching unseen messages...")
                            messages = server.search(['UNSEEN'])
                            for uid, message_data in server.fetch(messages, 'RFC822').items():
                                try:
                                    self.process_message(uid, message_data)
                                except Exception as e:
                                    logger.error(f"Failed to process message UID {uid}: {e}", exc_info=True)

            except (IMAPClientError, OSError) as e:
                logger.error(f"IMAP connection error: {e}. Reconnecting in 30 seconds...")
                time.sleep(30)
            except KeyboardInterrupt:
                logger.warning("IDLE worker stopped by user.")
                break
            except Exception as e:
                logger.critical(f"An unexpected critical error occurred in the main loop: {e}. Reconnecting in 60 seconds...", exc_info=True)
                time.sleep(60)

    def process_message(self, uid, message_data):
        """
        Parses a single email message, extracts attachments, saves them,
        and triggers the OCR processing task.
        """
        msg = email.message_from_bytes(message_data[b'RFC822'])
        sender = msg.get('From', '')
        subject = msg.get('Subject', '')
        date_str = msg.get('Date', '')
        email_date_obj = parsedate_to_datetime(date_str) if date_str else None

        attachment_count = 0
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if filename:
                attachment_count += 1
                unique_name = f"mailu_{uuid.uuid4().hex}_{filename}"
                file_content = part.get_payload(decode=True)
                
                attachment = EmailAttachment.objects.create(
                    filename=filename, sender=sender, subject=subject, email_date=email_date_obj
                )
                # Correctly save the file content to the ImageField/FileField
                attachment.file.save(unique_name, ContentFile(file_content), save=True)
                
                logger.info(f"Saved attachment: '{filename}' to '{attachment.file.name}' (DB ID: {attachment.id})")
                
                process_attachment_ocr.delay(attachment.id)
                logger.info(f"Triggered OCR processing for attachment ID: {attachment.id}")
        
        if attachment_count == 0:
            logger.info(f"Processed email from '{sender}' with subject '{subject}', but found no attachments.")