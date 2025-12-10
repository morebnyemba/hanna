#!/usr/bin/env python
"""
Quick Notification System Readiness Check
Run this to get a simple yes/no answer on whether your notification system is ready.

Usage:
    python check_notification_readiness.py
"""

import os
import sys
import django

# Status symbols as constants
CHECK_PASS = '✅'
CHECK_FAIL = '❌'
CHECK_WARN = '⚠️'
STATUS_OK = '✓'

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Derive settings module from directory structure
settings_module = os.getenv('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from notifications.models import NotificationTemplate
from meta_integration.models import MetaAppConfig
from email_integration.models import AdminEmailRecipient

User = get_user_model()


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check_smtp():
    """Check if SMTP is configured"""
    print("\n📧 Checking SMTP Configuration...")
    
    issues = []
    
    if not settings.EMAIL_HOST:
        issues.append(f"{CHECK_FAIL} EMAIL_HOST not set")
    else:
        print(f"   {STATUS_OK} EMAIL_HOST: {settings.EMAIL_HOST}")
    
    if not settings.EMAIL_HOST_USER:
        issues.append(f"{CHECK_FAIL} EMAIL_HOST_USER not set")
    else:
        print(f"   {STATUS_OK} EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    
    if not settings.EMAIL_HOST_PASSWORD:
        issues.append(f"{CHECK_FAIL} EMAIL_HOST_PASSWORD not set")
    else:
        print(f"   {STATUS_OK} EMAIL_HOST_PASSWORD: ***SET***")
    
    if not settings.DEFAULT_FROM_EMAIL:
        issues.append(f"{CHECK_FAIL} DEFAULT_FROM_EMAIL not set")
    else:
        print(f"   {STATUS_OK} DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    admin_recipients = AdminEmailRecipient.objects.filter(is_active=True).count()
    if admin_recipients == 0:
        issues.append(f"{CHECK_WARN} No AdminEmailRecipient configured (warnings only)")
        print(f"   {CHECK_WARN} AdminEmailRecipient: 0 (add in Django Admin)")
    else:
        print(f"   {STATUS_OK} AdminEmailRecipient: {admin_recipients}")
    
    return len([i for i in issues if i.startswith(CHECK_FAIL)]) == 0


def check_groups():
    """Check if all required groups exist"""
    print("\n👥 Checking Required Groups...")
    
    required_groups = [
        'Technical Admin',
        'System Admins',
        'Sales Team',
        'Pastoral Team',
        'Pfungwa Staff',
        'Finance Team'
    ]
    
    all_exist = True
    for group_name in required_groups:
        try:
            group = Group.objects.get(name=group_name)
            member_count = group.user_set.count()
            if member_count == 0:
                print(f"   {CHECK_WARN} {group_name}: EXISTS but NO MEMBERS")
            else:
                print(f"   {STATUS_OK} {group_name}: {member_count} member(s)")
        except Group.DoesNotExist:
            print(f"   {CHECK_FAIL} {group_name}: NOT CREATED")
            all_exist = False
    
    return all_exist


def check_user_linkage():
    """Check if staff users are linked to WhatsApp contacts"""
    print("\n🔗 Checking User-Contact Linkage...")
    
    staff_users = User.objects.filter(is_staff=True)
    linked_count = 0
    
    if staff_users.count() == 0:
        print(f"   {CHECK_WARN} No staff users found")
        return True
    
    for user in staff_users:
        if hasattr(user, 'whatsapp_contact') and user.whatsapp_contact:
            linked_count += 1
            print(f"   {STATUS_OK} {user.username} → {user.whatsapp_contact.whatsapp_id}")
        else:
            print(f"   {CHECK_FAIL} {user.username} → NOT LINKED")
    
    print(f"\n   Summary: {linked_count}/{staff_users.count()} staff users linked")
    return linked_count > 0


def check_templates():
    """Check if notification templates are loaded"""
    print("\n📋 Checking Notification Templates...")
    
    template_count = NotificationTemplate.objects.count()
    
    if template_count == 0:
        print(f"   {CHECK_FAIL} No templates loaded")
        print("   → Run: python manage.py load_notification_templates")
        return False
    else:
        print(f"   {STATUS_OK} {template_count} template(s) loaded")
        return True


def check_meta_api():
    """Check if Meta API is configured"""
    print("\n📱 Checking Meta API Configuration...")
    
    try:
        config = MetaAppConfig.objects.get_active_config()
        print(f"   {STATUS_OK} Active config found")
        print(f"      Phone Number ID: {config.business_phone_number_id}")
        return True
    except MetaAppConfig.DoesNotExist:
        print(f"   {CHECK_FAIL} No active Meta API configuration")
        return False


def main():
    print_section("🔍 NOTIFICATION SYSTEM READINESS CHECK")
    
    checks = {
        'SMTP Configuration': check_smtp(),
        'Required Groups': check_groups(),
        'User-Contact Linkage': check_user_linkage(),
        'Notification Templates': check_templates(),
        'Meta API Configuration': check_meta_api(),
    }
    
    print_section("📊 RESULTS")
    
    print("\nCheck Results:")
    all_passed = True
    for check_name, passed in checks.items():
        status = f"{CHECK_PASS} PASS" if passed else f"{CHECK_FAIL} FAIL"
        print(f"   {status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    
    if all_passed:
        print("\n🎉 SUCCESS! Your notification system is ready to use!")
        print("\nNext steps:")
        print("   1. Restart services: docker-compose restart")
        print("   2. Test with: python manage.py validate_notification_setup --test-email")
        return 0
    else:
        print("\n⚠️  ISSUES FOUND! Your notification system needs configuration.")
        print("\nQuick fixes:")
        print("   1. Fix SMTP: Update .env with correct EMAIL_HOST_PASSWORD")
        print("   2. Create groups: python manage.py create_notification_groups")
        print("   3. Link users: Use Django Admin to link users to contacts")
        print("   4. Load templates: python manage.py load_notification_templates")
        print("\nFor detailed help, see: NOTIFICATION_SYSTEM_COMPLETE_DIAGNOSIS.md")
        return 1


if __name__ == '__main__':
    sys.exit(main())
