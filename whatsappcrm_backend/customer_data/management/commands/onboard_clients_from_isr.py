"""
Management command to onboard clients from Installation System Records.

This command creates CustomerProfile and User accounts for customers from ISR records.

Usage:
  python manage.py onboard_clients_from_isr                # Process all ISR records
  python manage.py onboard_clients_from_isr --dry-run      # Preview changes without saving
  python manage.py onboard_clients_from_isr --force         # Force update existing profiles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from installation_systems.models import InstallationSystemRecord
from customer_data.models import CustomerProfile
from conversations.models import Contact
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Onboard clients from Installation System Records to client portal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing customer profiles'
        )
        parser.add_argument(
            '--status',
            type=str,
            default='commissioned,active',
            help='Filter by installation status (comma-separated). Default: commissioned,active'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        statuses = [s.strip() for s in options['status'].split(',')]

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write("CLIENT ONBOARDING FROM ISR RECORDS")
        self.stdout.write(f"{'='*70}\n")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be saved\n"))

        # Get ISR records to process
        isrs = InstallationSystemRecord.objects.filter(
            installation_status__in=statuses,
            customer__isnull=False
        ).select_related('customer', 'customer__contact', 'order').distinct('customer')

        total = isrs.count()
        created_users = 0
        created_profiles = 0
        updated_profiles = 0
        errors = 0

        self.stdout.write(f"Processing {total} unique customers from {total} ISR records...\n")

        for idx, isr in enumerate(isrs, 1):
            try:
                result = self._onboard_customer(isr, force, dry_run)
                
                if result['user_created']:
                    created_users += 1
                if result['profile_created']:
                    created_profiles += 1
                if result['profile_updated']:
                    updated_profiles += 1

                # Print progress
                self.stdout.write(
                    f"[{idx}/{total}] {result['message']}"
                )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f"[{idx}/{total}] ERROR: {str(e)}")
                )
                logger.exception(f"Error onboarding customer from ISR {isr.id}")

        # Summary
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write("ONBOARDING SUMMARY")
        self.stdout.write(f"{'='*70}")
        self.stdout.write(f"Total Processed:      {total}")
        self.stdout.write(self.style.SUCCESS(f"Users Created:        {created_users}"))
        self.stdout.write(self.style.SUCCESS(f"Profiles Created:     {created_profiles}"))
        self.stdout.write(self.style.WARNING(f"Profiles Updated:     {updated_profiles}"))
        self.stdout.write(self.style.ERROR(f"Errors:               {errors}"))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("\nDRY RUN COMPLETE - No changes were saved. Run without --dry-run to apply.")
            )
        else:
            self.stdout.write(self.style.SUCCESS("\nOnboarding complete!"))
        
        self.stdout.write(f"{'='*70}\n")

    def _onboard_customer(self, isr, force, dry_run):
        """
        Onboard a single customer from ISR record.
        Returns a dict with onboarding result details.
        """
        customer = isr.customer
        contact = customer.contact
        
        if not contact:
            raise ValueError(f"Customer {customer.id} has no Contact record")

        result = {
            'message': '',
            'user_created': False,
            'profile_created': False,
            'profile_updated': False
        }

        # Generate username from email or WhatsApp ID
        username = self._generate_username(customer, contact)
        
        # Check if user exists
        user = User.objects.filter(username=username).first()
        
        if not user:
            # Create new user
            user_data = {
                'username': username,
                'email': customer.email or '',
                'first_name': customer.first_name or '',
                'last_name': customer.last_name or '',
            }
            
            if not dry_run:
                user = User.objects.create_user(
                    **user_data,
                    password=self._generate_password()  # Random password, user can reset
                )
                user.is_active = True
                user.save()
            
            result['user_created'] = True
            result['message'] = f"✓ Created user: {username}"

        # Check if customer profile exists
        profile = CustomerProfile.objects.filter(contact=contact).first()
        
        if not profile:
            # Create customer profile
            profile_data = {
                'contact': contact,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'email': customer.email,
                'company': customer.company,
                'user': user,
            }
            
            if not dry_run:
                profile = CustomerProfile.objects.create(**profile_data)
                profile.save()
            
            result['profile_created'] = True
            result['message'] += f" + Profile" if result['message'] else f"✓ Created profile: {contact.whatsapp_id}"
        
        elif force and user:
            # Update existing profile with new user link if force is enabled
            if profile.user != user and not dry_run:
                profile.user = user
                profile.email = customer.email or profile.email
                profile.first_name = customer.first_name or profile.first_name
                profile.last_name = customer.last_name or profile.last_name
                profile.company = customer.company or profile.company
                profile.save()
                result['profile_updated'] = True
                result['message'] = f"✓ Updated profile: {contact.whatsapp_id} → {username}"
            else:
                result['message'] = f"  Existing profile: {contact.whatsapp_id}"
        
        else:
            result['message'] = f"  Existing profile: {contact.whatsapp_id}"

        return result

    def _generate_username(self, customer, contact):
        """
        Generate a unique username from email or WhatsApp ID.
        Format: email_prefix or whatsapp_id
        """
        if customer.email:
            username = customer.email.split('@')[0].lower()
            # Remove special characters
            username = ''.join(c for c in username if c.isalnum() or c in ['.', '_', '-'])
        else:
            username = f"client_{contact.whatsapp_id}"

        # Ensure uniqueness
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    def _generate_password(self, length=12):
        """Generate a secure random password."""
        import secrets
        import string
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(chars) for _ in range(length))
