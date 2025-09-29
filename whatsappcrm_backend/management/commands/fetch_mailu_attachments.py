import os
from imapclient import IMAPClient
import email
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

load_dotenv()  # Loads .env file

class Command(BaseCommand):
    help = "Fetch attachments from Mailu mailbox"

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
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    filename = part.get_filename()
                    if filename:
                        with open(filename, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        self.stdout.write(self.style.SUCCESS(f"Saved attachment: {filename}"))
