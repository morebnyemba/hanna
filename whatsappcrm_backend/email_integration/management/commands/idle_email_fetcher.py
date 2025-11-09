import os
import uuid
import email
import time
import logging
import imaplib
import socket # Import socket for address resolution
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_with_gemini
from email_integration.models import EmailAttachment, EmailAccount # Import EmailAccount

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs a persistent IMAP IDLE worker to listen for new emails across all active email accounts and triggers processing."

    def handle(self, *args, **kwargs):
        logger.info("Starting IMAP IDLE worker for all active accounts...")
        self.stdout.write(self.style.SUCCESS("IMAP IDLE worker started."))

        while True: # Main loop to keep the command running and re-check accounts
            accounts = EmailAccount.objects.filter(is_active=True)
            if not accounts.exists():
                self.stdout.write(self.style.WARNING("No active email accounts found in the database. Sleeping for 60 seconds."))
                time.sleep(60)
                continue

            for account in accounts:
                self.stdout.write(f"--- Processing account: {account.name} ({account.imap_user}) ---")
                logger.info(f"Attempting to connect to IMAP server for account: {account.name}")

                try:
                    # --- NEW: Force IPv4 resolution to bypass potential IPv6 issues ---
                    try:
                        ipv4_address = socket.getaddrinfo(account.imap_host, None, socket.AF_INET)[0][4][0]
                        host_to_connect = ipv4_address
                        self.stdout.write(self.style.SUCCESS(f"Resolved '{account.imap_host}' to IPv4: {host_to_connect}"))
                    except socket.gaierror:
                        self.stderr.write(self.style.ERROR(f"Could not resolve IPv4 address for '{account.imap_host}'. Using original hostname."))
                        host_to_connect = account.imap_host
                    # --- END NEW ---

                    # Inner loop for each account to handle reconnects
                    while True:
                        try:
                            # --- NEW: Use STARTTLS for more compatibility ---
                            # Connect on the standard port, then upgrade to TLS.
                            server = IMAPClient(host_to_connect, ssl=False, timeout=300)
                            server.starttls()
                            # --- END NEW ---
                            server.login(account.imap_user, account.imap_password)
                            server.select_folder('INBOX')
                            logger.info(f"Successfully connected and selected INBOX for '{account.name}'.")
                            self.stdout.write(self.style.SUCCESS(f"Account '{account.name}' connected. Listening for new emails via IDLE..."))

                            while True: # IDLE loop for the current account
                                try:
                                    server.idle()
                                    responses = server.idle_check(timeout=29 * 60) 
                                    server.idle_done()

                                    if responses:
                                        logger.info(f"New email activity detected for '{account.name}'.")
                                        self.stdout.write(self.style.SUCCESS(f"New email activity detected for '{account.name}'. Fetching unseen messages..."))
                                        messages = server.search(['UNSEEN'])
                                        for uid, message_data in server.fetch(messages, 'RFC822').items():
                                            self.process_message(account, message_data) # Pass the account object
                                except (IMAPClientError, OSError, imaplib.IMAP4.error) as idle_error:
                                    logger.error(f"Error during IDLE for '{account.name}': {idle_error}. Reconnecting...")
                                    break # Exit inner IDLE loop to reconnect
                                except Exception as e:
                                    logger.exception(f"Unexpected error in IDLE loop for '{account.name}': {e}")
                                    break # Exit inner IDLE loop to reconnect

                            server.close_folder()
                            server.logout()
                            logger.info(f"Disconnected from IMAP server for '{account.name}'.")
                            break # Exit inner reconnect loop if graceful disconnect
                        except (IMAPClientError, OSError, imaplib.IMAP4.error) as e:
                            self.stderr.write(self.style.ERROR(f"IMAP connection error for '{account.name}': {e}. Reconnecting in 30 seconds..."))
                            logger.exception(f"Connection error for '{account.name}' occurred:")
                            time.sleep(30) # Wait before attempting to reconnect
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"An unexpected error occurred for '{account.name}': {e}. Skipping account for now."))
                            logger.exception(f"Unexpected error for '{account.name}':")
                            break # Break from inner reconnect loop to try next account or main loop
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING("IMAP worker stopped by user."))
                    return # Exit the main loop on Ctrl+C
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Unhandled error processing account '{account.name}': {e}"))
                    logger.exception(f"Unhandled error for account '{account.name}':")
            
            # Small sleep between full account checks to prevent busy-waiting if all accounts fail
            time.sleep(5) 

    def process_message(self, account, message_data): # Accept account object
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
                    account=account, # Link the attachment to the account
                    file=ContentFile(file_content, name="attachments/"+unique_name),
                    filename=filename, 
                    sender=sender, 
                    subject=subject, 
                    email_date=email_date_obj
                )
                self.stdout.write(self.style.SUCCESS(f"Saved attachment: {filename} (DB id: {attachment.id}) from account '{account.name}'"))
                
                process_attachment_with_gemini.delay(attachment.id)
                self.stdout.write(self.style.WARNING(f"Triggered Gemini processing for attachment id: {attachment.id}"))
