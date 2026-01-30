#!/usr/bin/env python
"""
Create a technician user for testing the technician checklist functionality.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
django.setup()

from users.models import User

# Create technician user
username = "technician_test"
email = "technician@hanna.co.zw"
password = "Tech123!@#"

try:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': 'technician',
            'is_active': True,
            'first_name': 'Test',
            'last_name': 'Technician',
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Created technician user:")
    else:
        # Update existing user to be a technician
        user.role = 'technician'
        user.is_active = True
        user.set_password(password)
        user.save()
        print(f"✅ Updated existing user to technician:")
    
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   Role: {user.role}")
    print(f"\n🔐 Log in with these credentials to test technician checklists")
    
except Exception as e:
    print(f"❌ Error: {e}")
