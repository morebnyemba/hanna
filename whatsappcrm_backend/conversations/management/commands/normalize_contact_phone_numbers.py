# conversations/management/commands/normalize_contact_phone_numbers.py
from django.core.management.base import BaseCommand
from conversations.models import Contact
from conversations.utils import normalize_phone_number
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Normalizes contact phone numbers to E.164 format for WhatsApp compatibility'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to database',
        )
        parser.add_argument(
            '--country-code',
            type=str,
            default='263',
            help='Default country code to use (default: 263 for Zimbabwe)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        country_code = options['country_code']
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Contact Phone Number Normalization Tool'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN MODE] - No changes will be saved\n'))
        
        # Get all contacts
        contacts = Contact.objects.all()
        total_contacts = contacts.count()
        
        self.stdout.write(f'\nFound {total_contacts} contacts to process...\n')
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for contact in contacts:
            original_id = contact.whatsapp_id
            
            # Skip if it looks like an email or placeholder (not a phone number)
            if '@' in original_id or not any(char.isdigit() for char in original_id):
                skipped_count += 1
                continue
            
            # Skip if already in correct format (starts with country code and has no leading 0)
            if original_id.startswith(country_code) and len(original_id) >= 10:
                skipped_count += 1
                continue
            
            try:
                # Normalize the phone number
                normalized_id = normalize_phone_number(original_id, default_country_code=country_code)
                
                if normalized_id and normalized_id != original_id:
                    self.stdout.write(
                        f'  {contact.name or "Unknown"}: '
                        f'{self.style.WARNING(original_id)} → {self.style.SUCCESS(normalized_id)}'
                    )
                    
                    if not dry_run:
                        # Check if the normalized ID already exists
                        if Contact.objects.filter(whatsapp_id=normalized_id).exclude(id=contact.id).exists():
                            self.stdout.write(
                                self.style.ERROR(
                                    f'    ⚠ Skipped: Contact with whatsapp_id "{normalized_id}" already exists'
                                )
                            )
                            error_count += 1
                            continue
                        
                        contact.whatsapp_id = normalized_id
                        contact.save(update_fields=['whatsapp_id'])
                    
                    updated_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  Error processing contact {contact.id} ({original_id}): {str(e)}'
                    )
                )
                error_count += 1
        
        # Print summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  Total contacts: {total_contacts}')
        self.stdout.write(f'  {self.style.SUCCESS(f"Updated: {updated_count}")}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        if error_count > 0:
            self.stdout.write(f'  {self.style.ERROR(f"Errors: {error_count}")}')
        self.stdout.write('=' * 70)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] Run without --dry-run to apply changes\n'))
        elif updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully normalized {updated_count} contact phone numbers!\n'))
        else:
            self.stdout.write('\nNo contacts needed normalization.\n')
