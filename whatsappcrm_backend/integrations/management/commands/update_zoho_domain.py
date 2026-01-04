"""
Management command to update ZohoCredential API domain to the correct format.

Usage:
    python manage.py update_zoho_domain

This command updates existing ZohoCredential records from the old domain format
(e.g., https://inventory.zoho.com or https://inventory.zohoapis.com) to the
new format (e.g., https://www.zohoapis.com for US region).
"""
from django.core.management.base import BaseCommand
from integrations.models import ZohoCredential


class Command(BaseCommand):
    help = 'Update ZohoCredential API domain to the correct Zoho API format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Mapping of old domains to new domains
        # Includes common variations found in logs and manual configuration attempts
        domain_mapping = {
            'https://inventory.zoho.com': 'https://www.zohoapis.com',
            'https://inventory.zohoapis.com': 'https://www.zohoapis.com',
            'https://inventory.zoho.eu': 'https://www.zohoapis.eu',
            'https://inventory.zohoapis.eu': 'https://www.zohoapis.eu',
            'https://inventory.zoho.in': 'https://www.zohoapis.in',
            'https://inventory.zohoapis.in': 'https://www.zohoapis.in',
            'https://inventory.zoho.com.au': 'https://www.zohoapis.com.au',
            'https://inventory.zohoapis.com.au': 'https://www.zohoapis.com.au',
            'https://inventory.zoho.com.cn': 'https://www.zohoapis.com.cn',
            'https://inventory.zohoapis.com.cn': 'https://www.zohoapis.com.cn',
            # Include manual configuration attempts seen in error logs
            'https://zohoapis.com': 'https://www.zohoapis.com',
            'https://zohoapis.com/inventory': 'https://www.zohoapis.com',
        }
        
        credentials = ZohoCredential.objects.all()
        
        if not credentials.exists():
            self.stdout.write(self.style.WARNING('No ZohoCredential records found.'))
            return
        
        updated_count = 0
        # Note: ZohoCredential is a singleton model (typically only 1 record)
        # so bulk_update optimization is not necessary
        for credential in credentials:
            old_domain = credential.api_domain
            
            if old_domain in domain_mapping:
                new_domain = domain_mapping[old_domain]
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY RUN] Would update domain from '
                            f'{old_domain!r} to {new_domain!r}'
                        )
                    )
                else:
                    credential.api_domain = new_domain
                    credential.save(update_fields=['api_domain'])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Updated domain from {old_domain!r} to {new_domain!r}'
                        )
                    )
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        f'Skipping - domain already correct or unrecognized: {old_domain!r}'
                    )
                )
        
        if updated_count > 0:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n[DRY RUN] Would update {updated_count} credential(s). '
                        f'Run without --dry-run to apply changes.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Successfully updated {updated_count} credential(s).'
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✓ No credentials needed updating. All domains are already correct.'
                )
            )
