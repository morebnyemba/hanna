# Notification System Diagnosis and Setup Guide

## 🔍 Issue Summary

Based on the error logs provided, the notification system has an **SMTP authentication failure** preventing email notifications from being sent.

### Error Analysis

```
SMTPAuthenticationError: (535, b'5.7.8 Error: authentication failed: (reason unavailable)')
```

**Root Causes Identified:**

1. **SMTP Configuration Issue**: The email server authentication is failing
2. **Potential Network Issues**: Later logs show "Network is unreachable" errors
3. **Configuration Location**: SMTP credentials need to be properly set in `.env` file

---

## ✅ What Was Fixed

### 1. Removed Hardcoded Credentials from settings.py

**Before:**
```python
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER','installations@hanna.co.zw')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD','PfungwaHanna2024')
```

**After:**
```python
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
```

**Why?** Hardcoded credentials in source code are a security risk and make it harder to troubleshoot when values don't match the `.env` file.

---

## 🔧 Required SMTP Configuration

### Step 1: Update Your `.env` File

Ensure your `/home/runner/work/hanna/hanna/whatsappcrm_backend/.env` file has these settings:

```bash
# --- Email/SMTP Settings ---
EMAIL_HOST=mail.hanna.co.zw
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=installations@hanna.co.zw
EMAIL_HOST_PASSWORD=<your-actual-password-here>
DEFAULT_FROM_EMAIL=installations@hanna.co.zw
```

### Step 2: Verify SMTP Server Settings

The current configuration shows:
- **Host**: `mail.hanna.co.zw`
- **Port**: `587` (STARTTLS)
- **TLS**: Enabled

**Common SMTP Issues:**

1. **Wrong Password**: Ensure the password is correct and hasn't been changed
2. **App Passwords**: Some email providers require "app passwords" instead of regular passwords
3. **Port Issues**: 
   - Port 587 = STARTTLS (EMAIL_USE_TLS=True)
   - Port 465 = SSL/TLS (EMAIL_USE_SSL=True)
   - Port 25 = Unencrypted (not recommended)
4. **Firewall/Network**: Docker container must be able to reach the SMTP server

### Step 3: Test SMTP Configuration

After updating `.env`, restart your services and test:

```bash
# Restart Django to load new .env variables
docker-compose restart app

# Run the validation command with SMTP test
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

This will:
- Check all SMTP settings
- Attempt to send a test email
- Report any authentication errors

---

## 👥 Required Notification Groups

The notification system requires **6 specific groups** to be created in Django. Here's what each group does and who should be in it:

### 1. **Technical Admin** 🔴 (Critical)

**Receives:**
- WhatsApp message send failures
- Human intervention requests
- Site assessment requests
- System errors

**Members:** System admins, DevOps engineers, technical staff

---

### 2. **System Admins** 🔴 (Critical)

**Receives:**
- New orders created (all sources)
- Installation requests
- Job card creations
- General system events
- Invoice processing notifications

**Members:** All administrators, operations managers, senior management

---

### 3. **Sales Team** 🟡 (High Priority)

**Receives:**
- New online orders from customers
- Site assessment requests
- Customer inquiries
- Invoice processing notifications

**Members:** Sales representatives, customer service staff, account managers

---

### 4. **Pastoral Team** 🟢 (Medium Priority)

**Receives:**
- 24-hour window closing reminders

**Members:** Community team members, staff who need regular bot interaction

---

### 5. **Pfungwa Staff** 🟡 (High Priority)

**Receives:**
- Solar installation requests
- Starlink installation requests
- Solar panel cleaning requests
- Service-related notifications

**Members:** Installation technicians, service team, field staff

---

### 6. **Finance Team** 🟢 (Medium Priority)

**Receives:**
- Loan application submissions
- Financial transaction notifications

**Members:** Finance officers, accounting staff, credit managers

---

## 📋 Setup Commands

### Create All Required Groups

```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

**Output Example:**
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

### List Groups (Without Creating)

```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups --list
```

### Load Notification Templates

```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

### Validate Complete Setup

```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

### Check System Status

```bash
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose
```

---

## 🔗 Linking Users to WhatsApp Contacts

**Critical**: For staff to receive WhatsApp notifications, they must be linked to a Contact record.

### Via Django Admin:

1. Go to **Django Admin** → **Users**
2. Edit a user
3. In the **WhatsApp Contact** field, select the Contact record with the user's WhatsApp number
4. Save

### Via Django Shell:

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from conversations.models import Contact
from django.contrib.auth.models import Group

User = get_user_model()

# Example: Link a user to their WhatsApp contact
user = User.objects.get(username='john_doe')
contact = Contact.objects.get(whatsapp_id='263771234567')
user.whatsapp_contact = contact
user.save()

# Add user to a group
group = Group.objects.get(name='System Admins')
user.groups.add(group)

print(f"✓ Linked {user.username} to contact {contact.whatsapp_id}")
print(f"✓ Added {user.username} to group '{group.name}'")
```

---

## 🧪 Testing the Notification System

### 1. Create Test Admin Email Recipient

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from email_integration.models import AdminEmailRecipient

# Create a recipient for error notifications
AdminEmailRecipient.objects.create(
    name='System Admin',
    email='admin@example.com',
    is_active=True
)
```

### 2. Test Email Notification

```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

This sends a test email to all active `AdminEmailRecipient` entries.

### 3. Trigger a Test WhatsApp Notification

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from notifications.services import queue_notifications_to_users

# Send test notification to System Admins group
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

### 4. Check Celery Logs

```bash
# View Celery worker logs
docker logs whatsappcrm_celery_io_worker --tail 100 -f

# Check if Celery is running
docker ps | grep celery
```

---

## 🐛 Troubleshooting

### Issue: SMTP Authentication Failed

**Symptoms:**
```
SMTPAuthenticationError: (535, b'5.7.8 Error: authentication failed')
```

**Solutions:**

1. **Verify Credentials**:
   ```bash
   # Check what Django is using
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from django.conf import settings
   print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
   print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
   print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
   print(f"EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
   ```

2. **Test SMTP Manually**:
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from django.core.mail import send_mail
   from django.conf import settings
   
   try:
       send_mail(
           'Test Email',
           'This is a test message.',
           settings.DEFAULT_FROM_EMAIL,
           ['admin@example.com'],
           fail_silently=False,
       )
       print("✓ Email sent successfully!")
   except Exception as e:
       print(f"✗ Error: {e}")
   ```

3. **Check Email Server Logs**: Contact your email provider to check their logs

4. **Try Different Port**:
   - Port 587 with TLS (most common)
   - Port 465 with SSL
   - Port 25 (unencrypted, not recommended)

5. **Use App Password**: Some email providers require app-specific passwords

---

### Issue: Network Unreachable

**Symptoms:**
```
OSError: [Errno 101] Network is unreachable
```

**Solutions:**

1. **Check Docker Network**:
   ```bash
   # Can the container reach the SMTP server?
   docker exec -it whatsappcrm_backend_app ping -c 3 mail.hanna.co.zw
   ```

2. **Check DNS Resolution**:
   ```bash
   docker exec -it whatsappcrm_backend_app nslookup mail.hanna.co.zw
   ```

3. **Test SMTP Port**:
   ```bash
   docker exec -it whatsappcrm_backend_app telnet mail.hanna.co.zw 587
   ```

4. **Check Firewall Rules**: Ensure Docker containers can make outbound connections

---

### Issue: Users Not Receiving WhatsApp Notifications

**Check:**

1. **User in Group?**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from django.contrib.auth import get_user_model
   User = get_user_model()
   
   user = User.objects.get(username='username_here')
   print(f"Groups: {list(user.groups.values_list('name', flat=True))}")
   ```

2. **User Linked to Contact?**
   ```python
   print(f"WhatsApp Contact: {user.whatsapp_contact}")
   ```

3. **Celery Running?**
   ```bash
   docker ps | grep celery
   docker logs whatsappcrm_celery_io_worker --tail 50
   ```

4. **Check Notification Status**:
   ```python
   from notifications.models import Notification
   
   # Recent notifications for user
   notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:10]
   for n in notifications:
       print(f"{n.created_at} - {n.status} - {n.error_message or 'OK'}")
   ```

---

### Issue: No Templates Found

**Solution:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

---

## 📊 Verification Checklist

Use this checklist to ensure everything is configured:

### SMTP Configuration
- [ ] `EMAIL_HOST` set in `.env`
- [ ] `EMAIL_PORT` set in `.env`
- [ ] `EMAIL_HOST_USER` set in `.env`
- [ ] `EMAIL_HOST_PASSWORD` set in `.env`
- [ ] `DEFAULT_FROM_EMAIL` set in `.env`
- [ ] SMTP test email sends successfully
- [ ] At least one `AdminEmailRecipient` created

### Groups
- [ ] Technical Admin group exists with members
- [ ] System Admins group exists with members
- [ ] Sales Team group exists with members
- [ ] Pastoral Team group exists with members
- [ ] Pfungwa Staff group exists with members
- [ ] Finance Team group exists with members

### User Configuration
- [ ] Staff users linked to WhatsApp Contact records
- [ ] Users assigned to appropriate groups
- [ ] WhatsApp IDs are correct (format: 263771234567)

### Templates & Infrastructure
- [ ] Notification templates loaded
- [ ] Active MetaAppConfig exists
- [ ] Celery workers running
- [ ] Redis accessible

### Testing
- [ ] Test email successfully sent
- [ ] Test WhatsApp notification successfully sent
- [ ] No Celery errors in logs

---

## 🎯 Quick Start Commands

**If you're setting up from scratch, run these in order:**

```bash
# 1. Create all notification groups
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups

# 2. Load notification templates
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates

# 3. Run full validation (with SMTP test if ready)
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email

# 4. Check system status
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose

# 5. Restart services to apply .env changes
docker-compose restart app celery_io_worker celery_cpu_worker
```

---

## 📚 Additional Documentation

For more information, see:
- `NOTIFICATION_GROUPS_REFERENCE.md` - Detailed group information
- `NOTIFICATION_SYSTEM_SETUP.md` - Complete setup guide
- `NOTIFICATION_SYSTEM_QUICK_START.md` - Quick start guide
- `START_HERE_NOTIFICATION_SYSTEM.md` - Overview
- `ISSUE_91_NOTIFICATION_SYSTEM_SUMMARY.md` - Issue resolution summary

---

## 🆘 Still Having Issues?

If you're still experiencing problems:

1. **Check Celery logs**: `docker logs whatsappcrm_celery_io_worker --tail 100 -f`
2. **Check Django logs**: `docker logs whatsappcrm_backend_app --tail 100 -f`
3. **Run diagnostics**: `docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose`
4. **Verify `.env` loaded**: Restart Docker Compose after changing `.env`

---

## 📝 Summary of Required Actions

Based on your error logs, here's what you need to do:

### Immediate Actions (Critical)

1. **Fix SMTP Configuration**:
   - Update `.env` file with correct SMTP credentials
   - Verify email host, port, username, and password
   - Test with: `python manage.py validate_notification_setup --test-email`

2. **Create Notification Groups**:
   - Run: `python manage.py create_notification_groups`
   - Required groups: Technical Admin, System Admins, Sales Team, Pastoral Team, Pfungwa Staff, Finance Team

3. **Add Users to Groups**:
   - Go to Django Admin → Groups
   - Add appropriate users to each group

4. **Link Users to WhatsApp Contacts**:
   - Each staff user must have a `whatsapp_contact` linked
   - Do this via Django Admin → Users → WhatsApp Contact field

### Verification Actions

5. **Create Admin Email Recipients**:
   - Add at least one AdminEmailRecipient in Django Admin
   - This is where error notifications will be sent

6. **Load Templates** (if not already done):
   - Run: `python manage.py load_notification_templates`

7. **Restart Services**:
   ```bash
   docker-compose restart app celery_io_worker celery_cpu_worker
   ```

8. **Verify Everything Works**:
   - Run: `python manage.py check_notification_system --verbose`
   - Check Celery logs for any errors

---

**Last Updated**: 2025-12-09
**Issue Reference**: morebnyemba/hanna#156
