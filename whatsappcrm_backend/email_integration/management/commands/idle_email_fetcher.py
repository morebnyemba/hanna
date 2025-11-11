import os
import uuid
import email
import time
import logging
import imaplib
import socket
import ssl
import threading
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_with_gemini
from email_integration.models import EmailAttachment, EmailAccount

logger = logging.getLogger(__name__)

def process_message(account, message_data):
    """Processes a single email message, extracting attachments."""
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
                file=ContentFile(file_content, name="attachments/" + unique_name),
                filename=filename,
                sender=sender,
                subject=subject,
                email_date=email_date_obj
            )
            logger.info(f"Saved attachment: {filename} (DB id: {attachment.id}) from account '{account.name}'")
            
            process_attachment_with_gemini.delay(attachment.id)
            logger.info(f"Triggered Gemini processing for attachment id: {attachment.id}")

import ssl
import certifi
import os
import uuid
import email
import time
import logging
import imaplib
import socket
import ssl
import threading
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_with_gemini
from email_integration.models import EmailAttachment, EmailAccount

logger = logging.getLogger(__name__)

def process_message(account, message_data):
    """Processes a single email message, extracting attachments."""
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
                file=ContentFile(file_content, name="attachments/" + unique_name),
                filename=filename,
                sender=sender,
                subject=subject,
                email_date=email_date_obj
            )
            logger.info(f"Saved attachment: {filename} (DB id: {attachment.id}) from account '{account.name}'")
            
            process_attachment_with_gemini.delay(attachment.id)
            logger.info(f"Triggered Gemini processing for attachment id: {attachment.id}")

def monitor_account(account):
    """
    The main worker function for a single email account.
    Connects to the IMAP server and enters a persistent IDLE loop.
    """
    logger.info(f"[{account.name}] Starting monitoring thread for host {account.imap_host} and user {account.imap_user}.")
    
    # Create a default SSL context using certifi for up-to-date CAs
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    while True:
        try:
            logger.info(f"[{account.name}] Attempting to connect to {account.imap_host} with SSL using certifi CAs.")
            server = IMAPClient(account.imap_host, ssl_context=ssl_context, timeout=300)
            logger.info(f"[{account.name}] Connection to {account.imap_host} successful. Logging in...")
            server.login(account.imap_user, account.imap_password)
            server.select_folder('INBOX')
            logger.info(f"[{account.name}] Successfully connected and selected INBOX.")

            # Main IDLE loop for the connection
            while True:
                try:
                    server.idle()
                    # Wait for up to 29 minutes for new messages
                    responses = server.idle_check(timeout=29 * 60)
                    server.idle_done()

                    if responses:
                        logger.info(f"[{account.name}] New email activity detected. Fetching unseen messages...")
                        messages = server.search(['UNSEEN'])
                        for uid, message_data in server.fetch(messages, 'RFC822').items():
                            process_message(account, message_data)
                
                except (IMAPClientError, OSError, imaplib.IMAP4.error) as idle_error:
                    logger.error(f"[{account.name}] Error during IDLE: {idle_error}. Reconnecting...")
                    # Break from the inner IDLE loop to force a reconnection
                    break 
                except Exception as e:
                    logger.exception(f"[{account.name}] Unexpected error in IDLE loop: {e}. Reconnecting...")
                    break

        except (IMAPClientError, OSError, imaplib.IMAP4.error, socket.gaierror) as e:
            logger.error(f"[{account.name}] IMAP connection error for host {account.imap_host}: {e}. Retrying in 60 seconds...")
            time.sleep(60)
        except Exception as e:
            logger.exception(f"[{account.name}] An unrecoverable error occurred for host {account.imap_host}: {e}. Thread will exit and be restarted by the main loop.")
            # The thread will die, and the main loop will restart it.
            return

class Command(BaseCommand):
    help = "Runs a persistent IMAP IDLE worker to listen for new emails across all active email accounts concurrently."

    def handle(self, *args, **kwargs):
        logger.info("Starting IMAP IDLE worker manager...")
        self.stdout.write(self.style.SUCCESS("IMAP IDLE worker manager started."))
        
        active_threads = {}

        try:
            while True:
                # Fetch all currently active accounts from the database
                active_accounts = {acc.id: acc for acc in EmailAccount.objects.filter(is_active=True)}
                
                # --- Start threads for new or inactive accounts ---
                for account_id, account in active_accounts.items():
                    if account_id not in active_threads or not active_threads[account_id].is_alive():
                        if account_id in active_threads:
                            self.stdout.write(self.style.WARNING(f"Thread for '{account.name}' was found dead. Restarting..."))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"Found new active account '{account.name}'. Starting listener thread..."))
                        
                        thread = threading.Thread(target=monitor_account, args=(account,))
                        thread.daemon = True
                        thread.start()
                        active_threads[account_id] = thread

                # --- Stop threads for accounts that are no longer active ---
                stale_thread_ids = set(active_threads.keys()) - set(active_accounts.keys())
                for account_id in stale_thread_ids:
                    # The threads are daemonized, so we don't need to explicitly stop them.
                    # We just remove them from our tracking dictionary.
                    self.stdout.write(self.style.WARNING(f"Account with ID {account_id} is no longer active. Thread will be discarded."))
                    del active_threads[account_id]

                # Sleep for a while before checking the accounts and threads again
                time.sleep(60)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("IMAP worker manager stopped by user."))
        except Exception as e:
            logger.exception("An unhandled error occurred in the main worker manager loop.")
            self.stderr.write(self.style.ERROR(f"Unhandled error in main loop: {e}"))

class Command(BaseCommand):
    help = "Runs a persistent IMAP IDLE worker to listen for new emails across all active email accounts concurrently."

    def handle(self, *args, **kwargs):
        logger.info("Starting IMAP IDLE worker manager...")
        self.stdout.write(self.style.SUCCESS("IMAP IDLE worker manager started."))
        
        active_threads = {}

        try:
            while True:
                # Fetch all currently active accounts from the database
                active_accounts = {acc.id: acc for acc in EmailAccount.objects.filter(is_active=True)}
                
                # --- Start threads for new or inactive accounts ---
                for account_id, account in active_accounts.items():
                    if account_id not in active_threads or not active_threads[account_id].is_alive():
                        if account_id in active_threads:
                            self.stdout.write(self.style.WARNING(f"Thread for '{account.name}' was found dead. Restarting..."))
                        else:
                            self.stdout.write(self.style.SUCCESS(f"Found new active account '{account.name}'. Starting listener thread..."))
                        
                        thread = threading.Thread(target=monitor_account, args=(account,))
                        thread.daemon = True
                        thread.start()
                        active_threads[account_id] = thread

                # --- Stop threads for accounts that are no longer active ---
                stale_thread_ids = set(active_threads.keys()) - set(active_accounts.keys())
                for account_id in stale_thread_ids:
                    # The threads are daemonized, so we don't need to explicitly stop them.
                    # We just remove them from our tracking dictionary.
                    self.stdout.write(self.style.WARNING(f"Account with ID {account_id} is no longer active. Thread will be discarded."))
                    del active_threads[account_id]

                # Sleep for a while before checking the accounts and threads again
                time.sleep(60)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("IMAP worker manager stopped by user."))
        except Exception as e:
            logger.exception("An unhandled error occurred in the main worker manager loop.")
            self.stderr.write(self.style.ERROR(f"Unhandled error in main loop: {e}"))

