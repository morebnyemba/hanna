# Quick Fix: SMTP Authentication Issues and Notification Setup

## 🚨 Your Issue

You're experiencing SMTP authentication failures when trying to send email notifications:
```
SMTPAuthenticationError: (535, b'5.7.8 Error: authentication failed: (reason unavailable)')
```

## ✅ What I Fixed

### 1. Removed Hardcoded Credentials from `settings.py`
- **Security Risk**: Credentials were hardcoded in the source code
- **Fixed**: Now properly reads from `.env` file with empty string defaults

### 2. Added Missing SMTP Settings to `.env` File
- **Problem**: Your `.env` file was missing EMAIL configuration
- **Fixed**: Added complete SMTP configuration section

### 3. Created Comprehensive Documentation
- **New File**: `NOTIFICATION_SYSTEM_DIAGNOSIS.md` - Complete guide with troubleshooting

---

## 🔧 Immediate Actions Required

### Step 1: Verify SMTP Credentials

Your `.env` file now has these settings, but **you need to verify they're correct**:

```bash
EMAIL_HOST=mail.hanna.co.zw
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=installations@hanna.co.zw
EMAIL_HOST_PASSWORD=PfungwaHanna2024
DEFAULT_FROM_EMAIL=installations@hanna.co.zw
```

**Action**: Check with your email administrator that:
- ✅ Username is correct: `installations@hanna.co.zw`
- ✅ Password is correct: `PfungwaHanna2024`
- ✅ Port 587 with TLS is the right configuration
- ✅ The email server allows connections from your Docker containers

### Step 2: Restart Services

After verifying the credentials, restart your services to load the new configuration:

```bash
# Stop all services
docker-compose down

# Start services again
docker-compose up -d

# Or just restart the key services
docker-compose restart app celery_io_worker celery_cpu_worker
```

### Step 3: Test SMTP Connection

```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

**Expected Output** (if working):
```
✓ SMTP configuration looks valid
✓ Test email sent successfully to admin@example.com
```

**If Still Failing**, you'll see specific error messages. Common issues:

1. **Wrong Password**: Update `EMAIL_HOST_PASSWORD` in `.env`
2. **Wrong Port**: Try port 465 with `EMAIL_USE_SSL=True` instead
3. **Network Issue**: Check firewall/Docker network settings
4. **App Password Required**: Some mail servers need app-specific passwords

---

## 👥 Notification Groups Setup

### Required Groups

You mentioned asking "which groups I need to create". Here are the **6 required groups**:

| # | Group Name | Purpose | Who Should Be In It |
|---|------------|---------|---------------------|
| 1 | **Technical Admin** | System errors, failures | System admins, DevOps |
| 2 | **System Admins** | All important events | All administrators |
| 3 | **Sales Team** | Customer orders, inquiries | Sales staff |
| 4 | **Pastoral Team** | 24h reminders | Community team |
| 5 | **Pfungwa Staff** | Installation requests | Installation techs |
| 6 | **Finance Team** | Loan applications | Finance staff |

### Create All Groups

```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

This will create all 6 groups automatically.

### Verify Groups Were Created

```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups --list
```

---

## 🔗 Link Users to Groups and Contacts

### Critical: Users Must Be Linked to WhatsApp Contacts

For notifications to work, each staff user needs:
1. To be in at least one group
2. To have a WhatsApp Contact linked

### Quick Setup Example

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from conversations.models import Contact

User = get_user_model()

# Example 1: Link user to contact and add to group
user = User.objects.get(username='john_doe')  # Replace with actual username
contact = Contact.objects.get(whatsapp_id='263771234567')  # Replace with actual WhatsApp ID
group = Group.objects.get(name='System Admins')

user.whatsapp_contact = contact
user.save()
user.groups.add(group)

print(f"✓ {user.username} linked to {contact.whatsapp_id}")
print(f"✓ {user.username} added to {group.name}")

# Example 2: Create contact if it doesn't exist
contact, created = Contact.objects.get_or_create(
    whatsapp_id='263771234567',
    defaults={'name': 'John Doe'}
)
if created:
    print(f"✓ Created new contact: {contact.whatsapp_id}")
```

### Or Use Django Admin (Easier)

1. Go to: http://your-domain/admin/
2. Navigate to: **Users** → Select a user
3. Scroll to: **WhatsApp Contact** field
4. Select the contact from dropdown
5. Scroll to: **Groups** field
6. Select one or more groups
7. Click **Save**

---

## 🧪 Testing Notifications

### 1. Create Admin Email Recipient (for Error Notifications)

```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```

```python
from email_integration.models import AdminEmailRecipient

# Create recipient for system error emails
AdminEmailRecipient.objects.create(
    name='System Admin',
    email='your-email@example.com',  # Replace with your email
    is_active=True
)
print("✓ Admin email recipient created")
```

### 2. Load Notification Templates

```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

### 3. Send a Test WhatsApp Notification

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

Check Celery logs to see if it was sent:
```bash
docker logs whatsappcrm_celery_io_worker --tail 50 -f
```

---

## 📊 Check System Status

Run this comprehensive check:

```bash
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose
```

**This will tell you:**
- ✓ SMTP configuration status
- ✓ Which groups exist and how many members
- ✓ Which users are linked to contacts
- ✓ If templates are loaded
- ✓ Recent notification statuses
- ⚠ Any warnings or issues

---

## 🐛 Common Issues and Solutions

### Issue 1: "SMTP authentication failed"

**Causes:**
- Wrong password in `.env`
- Email server requires app password
- Wrong port/TLS configuration

**Solutions:**
1. Verify credentials with email admin
2. Check if your mail server requires "app passwords"
3. Try port 465 with SSL instead of 587 with TLS
4. Test manually with a mail client first

### Issue 2: "Network is unreachable"

**Causes:**
- Docker container can't reach SMTP server
- Firewall blocking outbound connections

**Solutions:**
1. Test connectivity:
   ```bash
   docker exec -it whatsappcrm_backend_app ping mail.hanna.co.zw
   ```
2. Test SMTP port:
   ```bash
   docker exec -it whatsappcrm_backend_app telnet mail.hanna.co.zw 587
   ```

### Issue 3: "No notification templates found"

**Solution:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

### Issue 4: "User not receiving notifications"

**Check:**
1. Is user in a group?
2. Is user linked to a WhatsApp contact?
3. Is the contact's WhatsApp ID correct?
4. Is Celery running?

**Debug:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```
```python
from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()
user = User.objects.get(username='username_here')

# Check groups
print(f"Groups: {list(user.groups.values_list('name', flat=True))}")

# Check contact
print(f"Contact: {user.whatsapp_contact}")

# Check recent notifications
for n in Notification.objects.filter(recipient=user)[:5]:
    print(f"{n.created_at} - {n.status} - {n.error_message or 'OK'}")
```

---

## ✅ Final Checklist

Before considering setup complete:

### SMTP Configuration
- [ ] `.env` file has all EMAIL settings
- [ ] Credentials verified as correct
- [ ] Services restarted after updating `.env`
- [ ] Test email sends successfully
- [ ] AdminEmailRecipient created

### Groups & Users
- [ ] All 6 groups created
- [ ] Users assigned to groups
- [ ] Users linked to WhatsApp contacts
- [ ] WhatsApp IDs are in correct format (e.g., 263771234567)

### Templates & Services
- [ ] Notification templates loaded
- [ ] MetaAppConfig active
- [ ] Celery workers running
- [ ] No errors in Celery logs

### Testing
- [ ] Test email sent successfully
- [ ] Test WhatsApp notification sent successfully
- [ ] System check passes with no critical errors

---

## 🆘 Still Having Problems?

If you're still stuck:

1. **Share the output of:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
   ```

2. **Check Celery logs:**
   ```bash
   docker logs whatsappcrm_celery_io_worker --tail 100
   ```

3. **Verify .env is loaded:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from django.conf import settings
   print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
   print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
   print(f"PASSWORD SET: {'Yes' if settings.EMAIL_HOST_PASSWORD else 'No'}")
   ```

---

## 📋 Summary

### What Was Done
1. ✅ Removed hardcoded SMTP credentials from `settings.py` (security fix)
2. ✅ Added complete EMAIL configuration to `.env` file
3. ✅ Added INVOICE_PROCESSED_NOTIFICATION_GROUPS setting
4. ✅ Created comprehensive troubleshooting guide

### What You Need to Do
1. ⚠️ **Verify SMTP credentials** in `.env` are correct
2. ⚠️ **Restart services** to load new configuration
3. ⚠️ **Test SMTP** with validation command
4. ⚠️ **Create notification groups** (run create_notification_groups)
5. ⚠️ **Link users to contacts** (via Django Admin or shell)
6. ⚠️ **Load templates** (run load_notification_templates)
7. ✅ **Verify everything works** (run check_notification_system)

---

**Need More Help?** See `NOTIFICATION_SYSTEM_DIAGNOSIS.md` for complete troubleshooting guide.

**Last Updated**: 2025-12-09
**Issue**: morebnyemba/hanna#156
