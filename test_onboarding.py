#!/usr/bin/env python
"""Test script for client onboarding command."""

import os
import sys
import django

# Setup Django
sys.path.insert(0, 'whatsappcrm_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
django.setup()

from installation_systems.models import InstallationSystemRecord
from customer_data.models import CustomerProfile
from conversations.models import Contact
from django.contrib.auth.models import User

# Check ISR records
print("=" * 70)
print("ISR RECORDS ANALYSIS")
print("=" * 70)

total_isrs = InstallationSystemRecord.objects.count()
commissioned_active = InstallationSystemRecord.objects.filter(
    installation_status__in=["commissioned", "active"]
).count()

print(f"\nTotal ISR records: {total_isrs}")
print(f"Commissioned/Active: {commissioned_active}")

# Check sample ISR with customer
if total_isrs > 0:
    isrs_with_customer = InstallationSystemRecord.objects.filter(
        customer__isnull=False
    ).select_related('customer', 'customer__contact').values(
        'id', 'customer__id', 'customer__first_name', 'customer__last_name',
        'installation_status', 'customer__contact__whatsapp_id'
    )[:5]
    
    print("\nSample ISR records with customers:")
    for isr in isrs_with_customer:
        print(f"  ISR #{isr['id']}: {isr['customer__first_name']} {isr['customer__last_name']} "
              f"({isr['installation_status']}) - Contact: {isr['customer__contact__whatsapp_id']}")

# Check existing customer profiles with users
print("\n" + "=" * 70)
print("CUSTOMER PROFILE ANALYSIS")
print("=" * 70)

total_profiles = CustomerProfile.objects.count()
profiles_with_users = CustomerProfile.objects.filter(user__isnull=False).count()

print(f"\nTotal CustomerProfiles: {total_profiles}")
print(f"Profiles with Users: {profiles_with_users}")

# Check existing users
existing_clients = User.objects.filter(
    customerprofile__isnull=False
).select_related('customerprofile__contact')[:5]

if existing_clients.exists():
    print("\nExisting client users:")
    for user in existing_clients:
        print(f"  {user.username}: {user.first_name} {user.last_name} "
              f"(Contact: {user.customerprofile.contact.whatsapp_id if user.customerprofile.contact else 'N/A'})")

print("\n" + "=" * 70)
print("ONBOARDING READINESS")
print("=" * 70)

if commissioned_active > 0:
    print(f"\n✓ Ready to onboard {commissioned_active} customers")
    print(f"  Run: python manage.py onboard_clients_from_isr --dry-run")
else:
    print("\n✗ No commissioned/active ISR records found")
    print("  Create some ISR records and set status to 'commissioned' or 'active'")

print("\n" + "=" * 70)
