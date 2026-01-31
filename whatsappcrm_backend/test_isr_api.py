#!/usr/bin/env python
"""Test ISR API endpoint to see what customer_details is being returned"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
# Set environment variable to skip REDIS check for testing
os.environ['REDIS_PASSWORD'] = 'test'
django.setup()

from installation_systems.models import InstallationSystemRecord
from installation_systems.serializers import InstallationSystemRecordDetailSerializer
import json

print("="*80)
print("Testing ISR API - Customer Details")
print("="*80)

# Get first ISR record
isr = InstallationSystemRecord.objects.first()

if not isr:
    print("❌ No ISR records found in database")
    exit(1)

print(f"\n✓ Found ISR: {isr.short_id}")
print(f"  Customer: {isr.customer}")

# Test direct access (like list serializer does)
print("\n" + "="*80)
print("Testing Direct Access (List Serializer Pattern):")
print("="*80)
try:
    print(f"  customer.contact_id: {isr.customer.contact_id}")
    print(f"  customer.get_full_name(): {isr.customer.get_full_name()}")
    print(f"  customer.email: {isr.customer.email}")
    print(f"  customer.contact.whatsapp_id: {isr.customer.contact.whatsapp_id}")
    print(f"  customer.company: {isr.customer.company}")
    print("✓ Direct access works!")
except Exception as e:
    print(f"❌ Error with direct access: {e}")
    import traceback
    traceback.print_exc()

# Test serializer
print("\n" + "="*80)
print("Testing Detail Serializer:")
print("="*80)
try:
    serializer = InstallationSystemRecordDetailSerializer(isr)
    data = serializer.data
    
    print(f"\n✓ Serialization successful!")
    print(f"\nCustomer Details from Serializer:")
    print(json.dumps(data.get('customer_details'), indent=2))
    
    print(f"\nFull record keys: {list(data.keys())}")
    
except Exception as e:
    print(f"❌ Serialization failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
