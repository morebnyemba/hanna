# Complete Notification System Setup & Troubleshooting Guide

## Quick Answer to Your Questions

### Q: Is my notification logic set to work?
**A: YES! ✅** Your notification system is fully implemented. However, based on the error logs you provided, there are **SMTP configuration issues** that need to be resolved.

### Q: Which groups do I need to create?
**A: 6 Groups** are required:
1. **Technical Admin** - For technical issues and failures
2. **System Admins** - For all important events
3. **Sales Team** - For customer orders and inquiries
4. **Pastoral Team** - For 24h reminder system
5. **Pfungwa Staff** - For installation services
6. **Finance Team** - For loan applications

---

## Understanding Your Current Issue

Based on your error logs, you're experiencing:

### 🔴 SMTP Authentication Failure
```
SMTPAuthenticationError: (535, b'5.7.8 Error: authentication failed: (reason unavailable)')
```

**What this means:**
- Your Django app is trying to send emails (receipts, notifications)
- The SMTP server is rejecting your login credentials
- This prevents:
  - Receipt confirmation emails to customers
  - Duplicate invoice notifications
  - Admin error notification emails

### 🔴 Network Unreachable Error
```
OSError: [Errno 101] Network is unreachable
```

**What this means:**
- After the authentication failure, the system tried to reconnect
- The SMTP server became unreachable (likely temporary network issue or firewall blocking)

---

## Part 1: Fix SMTP Configuration (CRITICAL)

### Step 1: Verify Your Email Settings

Check your `.env` file (or `docker-compose.yml` environment section):

```bash
# View current settings
docker exec -it whatsappcrm_backend_app python manage.py shell -c "
from django.conf import settings
print('EMAIL_HOST:', settings.EMAIL_HOST)
print('EMAIL_PORT:', settings.EMAIL_PORT)
print('EMAIL_HOST_USER:', settings.EMAIL_HOST_USER)
print('EMAIL_USE_TLS:', settings.EMAIL_USE_TLS)
print('DEFAULT_FROM_EMAIL:', settings.DEFAULT_FROM_EMAIL)
"
```

### Step 2: Update Your SMTP Configuration

Based on your logs, you're using `mail.hanna.co.zw`. Update your `.env` file:

```bash
# Email Configuration
EMAIL_HOST=mail.hanna.co.zw
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=installations@hanna.co.zw
EMAIL_HOST_PASSWORD=your_actual_password_here  # ⚠️ UPDATE THIS!
DEFAULT_FROM_EMAIL=installations@hanna.co.zw
```

### Step 3: Common SMTP Issues & Solutions

#### Issue 1: Wrong Password
**Solution:** 
- Verify the password is correct
- Some email servers require app-specific passwords (not your regular password)
- Contact your email administrator

#### Issue 2: TLS/SSL Configuration
**Solution:**
- Try changing `EMAIL_USE_TLS=True` to `EMAIL_USE_TLS=False`
- Or try port 465 with SSL: `EMAIL_PORT=465` and `EMAIL_USE_SSL=True`

#### Issue 3: Firewall/Network Blocking
**Solution:**
- Ensure your Docker container can reach `mail.hanna.co.zw`
- Test from inside container:
```bash
docker exec -it whatsappcrm_backend_app ping mail.hanna.co.zw
docker exec -it whatsappcrm_backend_app telnet mail.hanna.co.zw 587
```

### Step 4: Test SMTP Connection

After updating your configuration, test it:

```bash
# Restart the container to pick up new environment variables
docker-compose restart whatsappcrm_backend_app

# Test the connection
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

---

## Part 2: Set Up Admin Email Recipients

Admin email recipients receive error notifications when critical tasks fail.

### Add Recipients via Django Admin

1. Go to: `http://your-domain/admin/email_integration/adminemailrecipient/`
2. Click "Add Admin Email Recipient"
3. Add each administrator's email:
   - **Name**: Tech Admin
   - **Email**: admin@hanna.co.zw
   - **Is Active**: ✓ Checked
4. Save

### Or Create Programmatically

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from email_integration.models import AdminEmailRecipient

# Add admin recipients
AdminEmailRecipient.objects.create(
    name='Tech Admin',
    email='admin@hanna.co.zw',
    is_active=True
)

AdminEmailRecipient.objects.create(
    name='System Admin',
    email='sysadmin@hanna.co.zw',
    is_active=True
)

# Verify
for recipient in AdminEmailRecipient.objects.filter(is_active=True):
    print(f"{recipient.name}: {recipient.email}")
```

---

## Part 3: Set Up Notification Groups

### Quick Setup (Automatic)

```bash
# Create all required groups
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups

# Verify groups were created
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose
```

### Manual Setup (Django Admin)

1. Go to: `http://your-domain/admin/auth/group/`
2. Create each of these groups:
   - Technical Admin
   - System Admins
   - Sales Team
   - Pastoral Team
   - Pfungwa Staff
   - Finance Team

---

## Part 4: Link Users to WhatsApp Contacts

For staff to receive WhatsApp notifications, they must be linked to a WhatsApp Contact.

### Step 1: Create/Link Contacts

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from conversations.models import Contact

User = get_user_model()

# Example: Link user to WhatsApp contact
user = User.objects.get(username='admin')  # Change username
contact, created = Contact.objects.get_or_create(
    whatsapp_id='263771234567',  # User's WhatsApp number
    defaults={'name': user.get_full_name() or user.username}
)

# Link user to contact
user.whatsapp_contact = contact
user.save()

print(f"✓ Linked {user.username} to WhatsApp {contact.whatsapp_id}")
```

### Step 2: Assign Users to Groups

Via Django Admin:
1. Go to: `http://your-domain/admin/auth/user/`
2. Click on a user
3. Under "Groups", select appropriate groups (e.g., "System Admins")
4. Save

Or programmatically:
```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Add user to group
user = User.objects.get(username='admin')
group = Group.objects.get(name='System Admins')
user.groups.add(group)
user.save()

print(f"✓ Added {user.username} to {group.name}")
```

---

## Part 5: Load Notification Templates

```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

This loads all the pre-defined notification templates including:
- `hanna_invoice_processed_successfully`
- `hanna_new_order_created`
- `hanna_human_handover_flow`
- And more...

---

## Part 6: Complete System Validation

Run the comprehensive validation command:

```bash
# Basic validation
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup

# With SMTP test
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email

# Auto-fix common issues
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --fix
```

This command checks:
1. ✅ Email/SMTP Configuration
2. ✅ Admin Email Recipients
3. ✅ Required Groups
4. ✅ User-Contact Linkage
5. ✅ Notification Templates
6. ✅ Meta API Configuration
7. ✅ Environment Variables
8. ✅ Celery Status (informational)

---

## Part 7: Environment Variables Reference

### Required Variables

Add these to your `.env` file or `docker-compose.yml`:

```bash
# SMTP Configuration (for sending emails)
EMAIL_HOST=mail.hanna.co.zw
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=installations@hanna.co.zw
EMAIL_HOST_PASSWORD=your_password_here
DEFAULT_FROM_EMAIL=installations@hanna.co.zw

# Notification Groups (comma-separated)
INVOICE_PROCESSED_NOTIFICATION_GROUPS=System Admins,Sales Team

# Admin Notification Template
ADMIN_NOTIFICATION_FALLBACK_TEMPLATE_NAME=admin_notification_alert
```

### Optional Variables

```bash
# Additional email settings
EMAIL_TIMEOUT=30
EMAIL_USE_SSL=False  # Use if port is 465
```

---

## Part 8: Testing the Complete System

### Test 1: SMTP Email Sending

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test email from Django.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@example.com'],
    fail_silently=False,
)
print("✓ Test email sent successfully!")
```

### Test 2: WhatsApp Notification to Group

```python
from notifications.services import queue_notifications_to_users
from conversations.models import Contact

# Get a test contact
contact = Contact.objects.first()

queue_notifications_to_users(
    template_name='hanna_new_order_created',
    group_names=['System Admins'],
    related_contact=contact,
    template_context={
        'order_number': 'TEST-001',
        'customer_name': 'Test Customer',
        'order_amount': '100.00'
    }
)
print("✓ Notification queued!")
```

### Test 3: Check Celery Processing

```bash
# View Celery logs
docker logs whatsappcrm_celery_io_worker --tail 100

# Check for notification processing
docker exec -it whatsappcrm_backend_app python manage.py shell -c "
from notifications.models import Notification
recent = Notification.objects.all()[:10]
for n in recent:
    print(f'{n.id}: {n.recipient.username} - {n.status}')
"
```

---

## Part 9: Troubleshooting Common Issues

### Issue: "No active AdminEmailRecipient configured"

**Symptoms:** Error notifications not being sent to admins

**Solution:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --fix
```

Or manually add via Django Admin.

### Issue: "Group 'System Admins' not found"

**Symptoms:** Notifications not being created for certain events

**Solution:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

### Issue: Staff user not receiving WhatsApp notifications

**Symptoms:** Notification created but not sent via WhatsApp

**Checklist:**
1. ✓ Is user in the correct group?
2. ✓ Is user linked to a WhatsApp Contact?
3. ✓ Is the contact's WhatsApp ID correct?
4. ✓ Is Celery running?
5. ✓ Is Meta API configured?

**Verify:**
```python
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(username='your_username')
print(f"Groups: {list(user.groups.values_list('name', flat=True))}")
print(f"WhatsApp Contact: {user.whatsapp_contact}")
if user.whatsapp_contact:
    print(f"WhatsApp ID: {user.whatsapp_contact.whatsapp_id}")
```

### Issue: SMTP "Network unreachable"

**Symptoms:** Email tasks failing with network errors

**Solutions:**
1. **Check DNS:** Can the container resolve the SMTP host?
   ```bash
   docker exec -it whatsappcrm_backend_app nslookup mail.hanna.co.zw
   ```

2. **Check Connectivity:** Can the container reach the SMTP server?
   ```bash
   docker exec -it whatsappcrm_backend_app ping mail.hanna.co.zw
   ```

3. **Check Firewall:** Is port 587 open?
   ```bash
   docker exec -it whatsappcrm_backend_app nc -zv mail.hanna.co.zw 587
   ```

4. **Check Docker Network:** Ensure container has internet access
   ```bash
   docker exec -it whatsappcrm_backend_app ping 8.8.8.8
   ```

### Issue: Celery not processing tasks

**Symptoms:** Notifications stuck in "pending" status

**Solution:**
```bash
# Check if Celery is running
docker ps | grep celery

# Restart Celery workers
docker-compose restart whatsappcrm_celery_io_worker whatsappcrm_celery_cpu_worker

# View Celery logs
docker logs whatsappcrm_celery_io_worker --tail 100 -f
```

---

## Part 10: Complete Setup Checklist

Use this checklist to ensure everything is configured:

### ✅ SMTP Configuration
- [ ] EMAIL_HOST set in .env
- [ ] EMAIL_PORT set correctly (587 for TLS, 465 for SSL)
- [ ] EMAIL_HOST_USER configured
- [ ] EMAIL_HOST_PASSWORD configured (correct password!)
- [ ] DEFAULT_FROM_EMAIL set
- [ ] Test email sent successfully

### ✅ Admin Email Recipients
- [ ] At least one AdminEmailRecipient created
- [ ] Recipients are marked as active
- [ ] Email addresses are valid

### ✅ Notification Groups
- [ ] All 6 required groups created
- [ ] Users assigned to appropriate groups
- [ ] Each group has at least one member

### ✅ User-Contact Linkage
- [ ] Staff users have WhatsApp contacts created
- [ ] User.whatsapp_contact is set for each staff member
- [ ] WhatsApp IDs are correct (263XXXXXXXXX format)

### ✅ Templates & API
- [ ] Notification templates loaded
- [ ] Meta API configuration is active
- [ ] Meta credentials are valid

### ✅ Celery & Workers
- [ ] Celery workers running
- [ ] Redis is accessible
- [ ] Tasks are being processed

### ✅ Testing
- [ ] SMTP test successful
- [ ] Test notification sent
- [ ] Notification delivered via WhatsApp

---

## Part 11: Quick Commands Reference

```bash
# Validate entire setup
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup

# Test SMTP connection
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email

# Auto-fix common issues
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --fix

# Create groups
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups

# Check system status
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose

# Load templates
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates

# View recent notifications
docker exec -it whatsappcrm_backend_app python manage.py shell -c "
from notifications.models import Notification
for n in Notification.objects.all()[:10]:
    print(f'{n.id}: {n.recipient.username} - {n.status} - {n.content[:50]}')
"

# Check Celery logs
docker logs whatsappcrm_celery_io_worker --tail 100

# Restart services
docker-compose restart whatsappcrm_backend_app whatsappcrm_celery_io_worker
```

---

## Summary

### Your notification system is fully implemented! ✅

**What works:**
- ✅ Notification models and database
- ✅ Service functions for queuing notifications
- ✅ Celery task processing
- ✅ WhatsApp API integration
- ✅ Signal handlers for auto-triggering
- ✅ Template system

**What needs setup:**
1. 🔴 **Fix SMTP credentials** (CRITICAL - causing your errors)
2. 🟡 **Add admin email recipients**
3. 🟡 **Create notification groups**
4. 🟡 **Link staff users to WhatsApp contacts**
5. 🟢 **Load notification templates**

### Next Steps

1. **Fix SMTP immediately** - Update EMAIL_HOST_PASSWORD in .env
2. **Run validation** - `python manage.py validate_notification_setup --test-email`
3. **Create groups** - `python manage.py create_notification_groups`
4. **Add admin recipients** - Via Django Admin or shell
5. **Link users to contacts** - Via Django Admin or shell
6. **Test the system** - Send a test notification

---

**Need Help?** Check the logs:
- Celery: `docker logs whatsappcrm_celery_io_worker`
- Django: `docker logs whatsappcrm_backend_app`
- Email task errors: Search for "email_integration" in logs

**Last Updated:** December 2024
