#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
django.setup()

from installation_systems.models import InstallationSystemRecord
from installation_systems.serializers import InstallationSystemRecordDetailSerializer
import json

# Get first ISR record
isr = InstallationSystemRecord.objects.first()
if isr:
    print('ISR:', isr)
    print('Customer:', isr.customer)
    if isr.customer:
        print('Customer contact:', isr.customer.contact)
        print('Customer contact_id:', isr.customer.contact_id)
        print('Customer name:', isr.customer.get_full_name())
        print('Customer email:', isr.customer.email)
        print('Customer company:', isr.customer.company)
        if isr.customer.contact:
            print('Contact whatsapp_id:', isr.customer.contact.whatsapp_id)
    
    # Serialize it
    try:
        serializer = InstallationSystemRecordDetailSerializer(isr)
        print('\nSerialized customer_details:')
        print(json.dumps(serializer.data.get('customer_details'), indent=2))
    except Exception as e:
        print(f'\nError during serialization: {e}')
        import traceback
        traceback.print_exc()
else:
    print('No ISR records found')
