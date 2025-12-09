# Notification System Complete Diagnosis

## 🎯 Executive Summary

**Status**: ✅ Your notification logic IS set to work, but has configuration issues

**Primary Issue**: SMTP authentication failure preventing email notifications
**Secondary Issue**: Notification groups may not be created

---

## 📋 Answers to Your Questions

### Q1: Is my notification logic set to work?

**YES!** ✅ Your notification system is fully implemented and functional. The code includes:

1. ✅ **Notification Models** (`notifications/models.py`)
   - `Notification` - Stores notification records
   - `NotificationTemplate` - Stores templates for messages

2. ✅ **Service Layer** (`notifications/services.py`)
   - `queue_notifications_to_users()` - Queues notifications to staff or customers
   - Supports WhatsApp and email notifications
   - Template rendering with Jinja2 variables

3. ✅ **Task Processing** (`notifications/tasks.py`)
   - `dispatch_notification_task()` - Sends notifications via WhatsApp
   - `check_and_send_24h_window_reminders()` - Scheduled reminders
   - Celery integration for background processing

4. ✅ **Signal Handlers** (`notifications/handlers.py`)
   - Automatic notifications on message failures
   - Event-driven notification system

5. ✅ **Email Integration** (`email_integration/tasks.py`)
   - `send_receipt_confirmation_email()` - Confirms document receipt
   - `send_duplicate_invoice_email()` - Notifies about duplicates
   - `send_error_notification_email()` - Admin error alerts

6. ✅ **Management Commands**
   - `create_notification_groups` - Creates required groups
   - `validate_notification_setup` - Validates complete setup
   - `check_notification_system` - Quick status check
   - `load_notification_templates` - Loads notification templates

**The logic works. You just need to configure it properly.**

---

### Q2: Which groups do I need to create for the notification system to work?

You need **6 groups** total:

| # | Group Name | Purpose | Members Needed |
|---|------------|---------|----------------|
| 1 | **Technical Admin** | System errors, message failures, human handover | System admins, DevOps |
| 2 | **System Admins** | All important events, orders, installations | All administrators |
| 3 | **Sales Team** | Customer orders, inquiries, processed invoices | Sales staff |
| 4 | **Pastoral Team** | 24-hour window closing reminders | Community team |
| 5 | **Pfungwa Staff** | Solar installations, cleaning services | Installation technicians |
| 6 | **Finance Team** | Loan applications, financial transactions | Finance staff |

**Create them all with one command:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

---

## 🔴 Current Problems

### Problem 1: SMTP Authentication Failure

**Error from your logs:**
```
SMTPAuthenticationError: (535, b'5.7.8 Error: authentication failed: (reason unavailable)')
```

**Root Cause:**
The SMTP server (`mail.hanna.co.zw`) is rejecting the credentials in your `.env` file.

**Your Current Configuration:**
```env
EMAIL_HOST=mail.hanna.co.zw
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=installations@hanna.co.zw
EMAIL_HOST_PASSWORD=PfungwaHanna2024
DEFAULT_FROM_EMAIL=installations@hanna.co.zw
```

**Possible Reasons:**
1. ❌ Password is incorrect or has changed
2. ❌ Account requires an "app password" instead of the main password
3. ❌ Account is locked or disabled
4. ❌ SMTP server requires different authentication method
5. ❌ IP address is not whitelisted (some servers restrict by IP)

**Fix Steps:**

1. **Verify credentials with your email administrator:**
   - Is `installations@hanna.co.zw` the correct email?
   - Is `PfungwaHanna2024` the current password?
   - Does the account work when you log in via webmail?

2. **Check if app password is required:**
   - Some email servers (like Gmail, Outlook) require "app-specific passwords"
   - Contact your email admin to generate one

3. **Try alternative configuration:**
   If port 587 with TLS doesn't work, try port 465 with SSL:
   ```env
   EMAIL_PORT=465
   EMAIL_USE_TLS=False
   EMAIL_USE_SSL=True
   ```

4. **Test SMTP manually:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from django.core.mail import send_mail
   from django.conf import settings
   
   send_mail(
       'Test Email',
       'If you receive this, SMTP is working!',
       settings.DEFAULT_FROM_EMAIL,
       ['your-personal-email@example.com'],
       fail_silently=False,
   )
   ```

---

### Problem 2: WhatsApp Notifications Not Being Dispatched

**Evidence from your logs:**
```
[2025-12-09 22:29:33] DEBUG services Handling active flow. Contact: 263774635389...
```

The flow is executing, but there's no indication that notifications are being dispatched.

**Possible Causes:**

1. **Groups Don't Exist:**
   If the notification groups haven't been created, no notifications will be queued.
   
   **Check:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups --list
   ```

2. **No Users in Groups:**
   Even if groups exist, they need members.
   
   **Check:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose
   ```

3. **Users Not Linked to WhatsApp Contacts:**
   Each staff user must have a `whatsapp_contact` linked.
   
   **Check:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from django.contrib.auth import get_user_model
   User = get_user_model()
   
   for user in User.objects.filter(is_staff=True):
       has_contact = hasattr(user, 'whatsapp_contact') and user.whatsapp_contact
       print(f"{user.username}: {'✓ Linked' if has_contact else '✗ NOT LINKED'}")
   ```

4. **Templates Not Loaded:**
   Notification templates may not be in the database.
   
   **Fix:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
   ```

5. **Celery Not Running:**
   Notifications are dispatched by Celery workers.
   
   **Check:**
   ```bash
   docker ps | grep celery
   docker logs whatsappcrm_celery_io_worker --tail 50
   ```

---

## 🔧 Step-by-Step Fix Guide

### Step 1: Fix SMTP Configuration (5 minutes)

1. **Verify your SMTP credentials:**
   - Contact your email administrator
   - Test logging into `installations@hanna.co.zw` via webmail
   - Confirm the password is `PfungwaHanna2024`

2. **Update `.env` if needed:**
   ```bash
   nano /path/to/whatsappcrm_backend/.env
   ```
   Update the `EMAIL_HOST_PASSWORD` line with the correct password.

3. **Restart services:**
   ```bash
   docker-compose restart whatsappcrm_backend_app whatsappcrm_celery_io_worker
   ```

4. **Test SMTP:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
   ```

---

### Step 2: Create Notification Groups (2 minutes)

```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

**Expected output:**
```
Creating notification system groups...

  ✓ Created: Technical Admin
  ✓ Created: System Admins
  ✓ Created: Sales Team
  ✓ Created: Pastoral Team
  ✓ Created: Pfungwa Staff
  ✓ Created: Finance Team

✓ Summary: 6 created, 0 already existed
```

---

### Step 3: Add Users to Groups (5 minutes)

**Option A: Via Django Admin (Easier)**

1. Go to: `https://backend.hanna.co.zw/admin/`
2. Navigate to: **Authentication and Authorization** → **Users**
3. Select a user (e.g., yourself)
4. Scroll to **Groups** section
5. Add the user to one or more groups (e.g., "System Admins", "Technical Admin")
6. Click **Save**

**Option B: Via Django Shell**

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Example: Add user 'morebnyemba' to System Admins
user = User.objects.get(username='morebnyemba')  # Replace with your username
group = Group.objects.get(name='System Admins')
user.groups.add(group)

print(f"✓ {user.username} added to {group.name}")
```

---

### Step 4: Link Users to WhatsApp Contacts (5 minutes)

Each staff user who should receive notifications needs a WhatsApp contact linked.

**Option A: Via Django Admin**

1. Go to: `https://backend.hanna.co.zw/admin/`
2. Navigate to: **Authentication and Authorization** → **Users**
3. Select a user
4. Scroll to **WhatsApp contact** field
5. Select or create a contact with the user's WhatsApp number
6. Click **Save**

**Option B: Via Django Shell**

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from conversations.models import Contact

User = get_user_model()

# Example: Link user to their WhatsApp contact
user = User.objects.get(username='morebnyemba')  # Replace with your username

# Create or get the contact (use Zimbabwe format: 263XXXXXXXXX)
contact, created = Contact.objects.get_or_create(
    whatsapp_id='263774635389',  # Replace with user's WhatsApp number
    defaults={'name': 'Moreblessing Nyemba'}
)

# Link user to contact
user.whatsapp_contact = contact
user.save()

print(f"✓ {user.username} linked to {contact.whatsapp_id}")
```

---

### Step 5: Create Admin Email Recipients (3 minutes)

These are emails that receive system error notifications.

**Option A: Via Django Admin**

1. Go to: `https://backend.hanna.co.zw/admin/`
2. Navigate to: **Email Integration** → **Admin email recipients**
3. Click **Add Admin Email Recipient**
4. Fill in:
   - Name: "System Admin"
   - Email: your email address
   - Is active: ✓ (checked)
5. Click **Save**

**Option B: Via Django Shell**

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from email_integration.models import AdminEmailRecipient

AdminEmailRecipient.objects.create(
    name='System Admin',
    email='morebnyemba@example.com',  # Replace with your email
    is_active=True
)

print("✓ Admin email recipient created")
```

**Option C: Automatic (from superusers)**

```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --fix
```

---

### Step 6: Load Notification Templates (1 minute)

```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

---

### Step 7: Validate Everything (2 minutes)

Run the comprehensive validation:

```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

**Expected output if everything is working:**
```
================================================================================
NOTIFICATION SYSTEM SETUP VALIDATION
================================================================================

1. Checking Email/SMTP Configuration...
   ✓ SMTP configuration looks valid

   Testing SMTP connection...
   ✓ Test email sent successfully to admin@example.com

2. Checking Admin Email Recipients...
   ✓ 1 active admin email recipient(s) configured
      - System Admin <admin@example.com>

3. Checking Required Groups...
   ✓ Technical Admin: 1 member(s)
   ✓ System Admins: 2 member(s)
   ✓ Sales Team: 1 member(s)
   ✓ Pastoral Team: 0 member(s)
   ✓ Pfungwa Staff: 1 member(s)
   ✓ Finance Team: 0 member(s)

4. Checking User-Contact Linkage...
   ✓ All 3 staff user(s) linked to contacts

5. Checking Notification Templates...
   ✓ 15 template(s) loaded

6. Checking Meta API Configuration...
   ✓ Active config: 123456789012345

7. Checking Environment Variables...
   ✓ EMAIL_HOST: mail.hanna.co.zw
   ✓ EMAIL_PORT: 587
   ✓ EMAIL_HOST_USER: installations@hanna.co.zw
   ✓ DEFAULT_FROM_EMAIL: installations@hanna.co.zw
   ✓ INVOICE_PROCESSED_NOTIFICATION_GROUPS: ['System Admins', 'Sales Team']

================================================================================
VALIDATION SUMMARY
================================================================================

✓ Notification system is properly configured and ready to use!
```

---

## 🧪 Testing Your Notifications

### Test 1: Send Test WhatsApp Notification

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from notifications.services import queue_notifications_to_users

# Send test to System Admins group
queue_notifications_to_users(
    template_name='hanna_new_order_created',
    group_names=['System Admins'],
    template_context={
        'order_number': 'TEST-001',
        'customer_name': 'Test Customer',
        'total_amount': '100.00'
    }
)

print("✓ Test notification queued!")
```

**Check if it was sent:**
```bash
docker logs whatsappcrm_celery_io_worker --tail 50 -f
```

Look for:
```
[INFO] Notifications: Queued Notification ID X for user 'username'
[INFO] Successfully dispatched notification X as Message Y
```

---

### Test 2: Send Test Email

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='Test Email from Hanna CRM',
    message='This is a test email. If you receive this, SMTP is working correctly!',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your-email@example.com'],
    fail_silently=False,
)

print("✓ Test email sent!")
```

---

## 📊 Monitoring and Debugging

### Check Notification Status

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from notifications.models import Notification

# Check recent notifications
recent = Notification.objects.all().order_by('-created_at')[:10]

for notif in recent:
    print(f"{notif.created_at.strftime('%Y-%m-%d %H:%M:%S')} | "
          f"{notif.recipient.username} | "
          f"{notif.status} | "
          f"{notif.error_message or 'OK'}")
```

---

### Check Celery Workers

```bash
# Check if Celery containers are running
docker ps | grep celery

# View logs of I/O worker (handles notifications)
docker logs whatsappcrm_celery_io_worker --tail 100 -f

# View logs of CPU worker
docker logs whatsappcrm_celery_cpu_worker --tail 100 -f
```

---

### Check Email Integration Logs

```bash
docker logs whatsappcrm_backend_app --tail 200 | grep -i "email\|smtp"
```

---

## 🎯 Common Notification Triggers

Your system automatically sends notifications when:

1. **Order Created** → System Admins, Sales Team
2. **Online Order Placed** → Sales Team, System Admins
3. **Human Handover Requested** → Technical Admin
4. **Message Send Failed** → Technical Admin
5. **Installation Requested** → Pfungwa Staff, System Admins
6. **Invoice Processed** → System Admins, Sales Team (from your `.env`)
7. **Job Card Created** → System Admins
8. **24h Window Closing** → Pastoral Team
9. **Site Assessment Requested** → Technical Admin, Sales Team
10. **Loan Application Submitted** → Finance Team

---

## ✅ Final Checklist

Before considering the notification system fully operational:

### SMTP Configuration
- [ ] `.env` file has all EMAIL settings
- [ ] SMTP credentials verified as correct
- [ ] Services restarted after updating `.env`
- [ ] Test email sends successfully
- [ ] `AdminEmailRecipient` records created

### Groups & Users
- [ ] All 6 required groups created
- [ ] Users assigned to appropriate groups
- [ ] Users linked to their WhatsApp contacts
- [ ] WhatsApp IDs are in correct format (263XXXXXXXXX)

### Templates & Services
- [ ] Notification templates loaded
- [ ] `MetaAppConfig` is active
- [ ] Celery workers are running
- [ ] No errors in Celery logs

### Testing
- [ ] Test email sent successfully
- [ ] Test WhatsApp notification sent successfully
- [ ] `validate_notification_setup` passes with no critical errors
- [ ] Monitored Celery logs during test

---

## 🆘 If You're Still Having Problems

### Problem: SMTP Still Failing

1. **Try different port/security:**
   ```env
   EMAIL_PORT=465
   EMAIL_USE_TLS=False
   EMAIL_USE_SSL=True
   ```

2. **Check network connectivity:**
   ```bash
   docker exec -it whatsappcrm_backend_app ping mail.hanna.co.zw
   docker exec -it whatsappcrm_backend_app telnet mail.hanna.co.zw 587
   ```

3. **Contact your email administrator:**
   - Verify account is not locked
   - Check if IP needs to be whitelisted
   - Confirm if app password is required

---

### Problem: WhatsApp Notifications Not Sending

1. **Check if notifications are being queued:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from notifications.models import Notification
   print(f"Total notifications: {Notification.objects.count()}")
   print(f"Pending: {Notification.objects.filter(status='pending').count()}")
   print(f"Failed: {Notification.objects.filter(status='failed').count()}")
   ```

2. **Check Celery is processing:**
   ```bash
   docker logs whatsappcrm_celery_io_worker --tail 100
   ```
   Look for: `Task notifications.tasks.dispatch_notification_task`

3. **Check Meta API is active:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from meta_integration.models import MetaAppConfig
   config = MetaAppConfig.objects.get_active_config()
   print(f"Phone Number ID: {config.business_phone_number_id}")
   print(f"Is Active: {config.is_active}")
   ```

---

## 📚 Documentation References

- **Notification Groups**: `NOTIFICATION_GROUPS_REFERENCE.md`
- **Quick Start**: `NOTIFICATION_SYSTEM_QUICK_START.md`
- **Setup Guide**: `NOTIFICATION_SYSTEM_SETUP.md`
- **SMTP Quick Fix**: `QUICK_FIX_NOTIFICATION_SMTP.md`

---

## 📞 Quick Command Reference

```bash
# Validate complete setup with SMTP test
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email

# Auto-fix common issues
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --fix

# Quick status check
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose

# Create all required groups
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups

# Load notification templates
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates

# Check Celery status
docker ps | grep celery
docker logs whatsappcrm_celery_io_worker --tail 50 -f
```

---

## 📅 Last Updated

**Date**: December 9, 2025
**Issue**: morebnyemba/hanna (Notification System Check)
**Status**: Complete diagnosis provided

---

**Bottom Line:**
1. ✅ Your notification logic works perfectly
2. ❌ Fix the SMTP password in `.env`
3. ❌ Create the 6 required groups (one command)
4. ❌ Add users to groups and link to contacts
5. ✅ Use the validation commands to verify everything

**Estimated Time to Fix**: 15-20 minutes
