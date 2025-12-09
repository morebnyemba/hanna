# 🎯 START HERE - Issue #156 Resolution Guide

## Quick Navigation

**Your Question:**
> "Check if my notification logic is set to work, also enlighten me on which groups I need to create for the notification system to work"

**Your Error:**
```
SMTPAuthenticationError: (535, b'5.7.8 Error: authentication failed: (reason unavailable)')
```

---

## 📖 What to Read First

### 1. **Quick Fix** ⚡ (Read This First)
**File:** `QUICK_FIX_NOTIFICATION_SMTP.md`

**What it covers:**
- What was wrong and what I fixed
- Immediate actions you need to take
- How to test if SMTP works now
- How to create the 6 required notification groups

**Time to complete:** 15-30 minutes

---

### 2. **Issue Resolution Summary** 📋 (After Quick Fix)
**File:** `NOTIFICATION_ISSUE_RESOLUTION.md`

**What it covers:**
- Detailed explanation of root causes
- All changes made to fix the issues
- Complete answer to your question about notification groups
- Step-by-step verification checklist
- Testing procedures

**Time to complete:** 30-45 minutes

---

### 3. **Complete Diagnostic Guide** 🔍 (If Problems Persist)
**File:** `NOTIFICATION_SYSTEM_DIAGNOSIS.md`

**What it covers:**
- Comprehensive troubleshooting for all notification issues
- Detailed SMTP configuration guide
- Group setup with examples
- Common problems and solutions
- Advanced testing and debugging

**Time to complete:** 1-2 hours to implement fully

---

### 4. **Security Warning** ⚠️ (Important!)
**File:** `SECURITY_WARNING_ENV_FILES.md`

**What it covers:**
- Critical security issue discovered (.env files in Git)
- Why this is a problem
- How to fix it (change credentials, stop tracking .env)
- Best practices for managing secrets

**Time to complete:** 30 minutes to understand, 1-2 hours to fix properly

---

## 🎯 Quick Start - Do This Now

### Step 1: Verify Your SMTP Credentials (5 minutes)

Check that these are correct in `whatsappcrm_backend/.env`:
```bash
EMAIL_HOST=mail.hanna.co.zw
EMAIL_HOST_USER=installations@hanna.co.zw
EMAIL_HOST_PASSWORD=PfungwaHanna2024
```

**Action:** Confirm with your email administrator that the password is correct.

---

### Step 2: Restart Services (2 minutes)

```bash
cd /home/runner/work/hanna/hanna
docker-compose restart app celery_io_worker celery_cpu_worker
```

---

### Step 3: Test SMTP (2 minutes)

```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

**Expected:** `✓ Test email sent successfully`

**If Failed:** See troubleshooting section in `QUICK_FIX_NOTIFICATION_SMTP.md`

---

### Step 4: Create Notification Groups (2 minutes)

```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

This creates these 6 groups:
1. Technical Admin
2. System Admins
3. Sales Team
4. Pastoral Team
5. Pfungwa Staff
6. Finance Team

---

### Step 5: Verify Setup (2 minutes)

```bash
docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose
```

**Look for:** 
- ✓ Green checkmarks = working
- ⚠ Yellow warnings = needs attention
- ✗ Red errors = critical issues

---

## 📋 Complete Setup Checklist

Use this to track your progress:

### Critical (Do First)
- [ ] Verify SMTP credentials are correct
- [ ] Restart services
- [ ] Test SMTP connection
- [ ] Create 6 notification groups
- [ ] Load notification templates: `python manage.py load_notification_templates`

### Important (Do Soon)
- [ ] Add users to notification groups (via Django Admin)
- [ ] Link users to WhatsApp contacts (via Django Admin)
- [ ] Create AdminEmailRecipient entries for error notifications
- [ ] Test WhatsApp notification sending
- [ ] Verify Celery is running properly

### Security (Do This Week)
- [ ] Change all credentials (SMTP, DB, Redis, WhatsApp)
- [ ] Stop tracking .env files in Git
- [ ] Create .env.example template
- [ ] Document credential rotation process

---

## 👥 Answer: Required Notification Groups

You asked which groups to create. Here's the complete answer:

| # | Group Name | Receives | Who Should Be In It |
|---|------------|----------|---------------------|
| 1 | **Technical Admin** | System errors, message failures | System admins, DevOps |
| 2 | **System Admins** | All orders, installations, events | All administrators |
| 3 | **Sales Team** | Customer orders, site assessments | Sales staff |
| 4 | **Pastoral Team** | 24h window reminders | Community team |
| 5 | **Pfungwa Staff** | Installation requests | Installation techs |
| 6 | **Finance Team** | Loan applications | Finance staff |

**Create all at once:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups
```

**See which groups exist:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py create_notification_groups --list
```

---

## 🔧 What Was Fixed

### 1. Security Issue
**Problem:** SMTP credentials were hardcoded in `settings.py`

**Fixed:** Now properly reads from `.env` file

**File:** `whatsappcrm_backend/whatsappcrm_backend/settings.py`

### 2. Missing Configuration
**Problem:** `.env` file was missing EMAIL settings

**Fixed:** Added complete EMAIL configuration section

**File:** `whatsappcrm_backend/.env`

### 3. Documentation Gap
**Problem:** No clear guide on notification setup

**Fixed:** Created 4 comprehensive documentation files

---

## 🐛 If Something Doesn't Work

### SMTP Still Failing?

1. **Check credentials:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py shell
   ```
   ```python
   from django.conf import settings
   print(f"Host: {settings.EMAIL_HOST}")
   print(f"User: {settings.EMAIL_HOST_USER}")
   print(f"Pass Set: {'Yes' if settings.EMAIL_HOST_PASSWORD else 'No'}")
   ```

2. **Test manually:**
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Test message', 'installations@hanna.co.zw', ['your@email.com'])
   ```

3. **Check logs:**
   ```bash
   docker logs whatsappcrm_backend_app --tail 50
   docker logs whatsappcrm_celery_io_worker --tail 50
   ```

### Users Not Getting Notifications?

1. **Check they're in a group:**
   - Django Admin → Users → Groups

2. **Check they're linked to contact:**
   - Django Admin → Users → WhatsApp Contact field

3. **Check Celery is running:**
   ```bash
   docker ps | grep celery
   ```

### Templates Not Found?

```bash
docker exec -it whatsappcrm_backend_app python manage.py load_notification_templates
```

---

## 📊 Testing Everything Works

### Test Email Notifications
```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

### Test WhatsApp Notifications
```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```
```python
from notifications.services import queue_notifications_to_users

queue_notifications_to_users(
    template_name='hanna_new_order_created',
    group_names=['System Admins'],
    template_context={
        'order_number': 'TEST-001',
        'customer_name': 'Test Customer',
        'total_amount': '100.00'
    }
)
```

Check logs:
```bash
docker logs whatsappcrm_celery_io_worker --tail 50 -f
```

---

## 📚 All Documentation Files

1. **START_HERE_ISSUE_156.md** (this file) - Start here guide
2. **QUICK_FIX_NOTIFICATION_SMTP.md** - Quick fix for your issue
3. **NOTIFICATION_ISSUE_RESOLUTION.md** - Complete resolution summary
4. **NOTIFICATION_SYSTEM_DIAGNOSIS.md** - Full diagnostic guide
5. **SECURITY_WARNING_ENV_FILES.md** - Security warning and fix
6. **NOTIFICATION_GROUPS_REFERENCE.md** - Detailed group info (already existed)
7. **NOTIFICATION_SYSTEM_SETUP.md** - Original setup guide (already existed)

---

## ⏱️ Time Estimates

### Minimal Setup (To Get Working)
- Read quick fix guide: 10 minutes
- Verify credentials: 5 minutes
- Restart services: 2 minutes
- Create groups: 2 minutes
- Test SMTP: 2 minutes
- **Total: ~20-30 minutes**

### Complete Setup (Production Ready)
- All of above: 30 minutes
- Link users to contacts: 15 minutes
- Add users to groups: 15 minutes
- Load templates: 5 minutes
- Test thoroughly: 15 minutes
- **Total: ~1-2 hours**

### With Security Fixes (Recommended)
- Complete setup: 1-2 hours
- Change credentials: 30 minutes
- Fix Git tracking: 30 minutes
- Document process: 30 minutes
- **Total: ~2-4 hours**

---

## ✅ Success Criteria

You'll know everything is working when:

1. ✅ SMTP test sends email successfully
2. ✅ All 6 notification groups exist
3. ✅ Users are in groups and linked to contacts
4. ✅ Templates are loaded
5. ✅ Test WhatsApp notification is received
6. ✅ `check_notification_system --verbose` shows no critical errors
7. ✅ No authentication errors in Celery logs

---

## 🆘 Getting Help

If you're stuck:

1. **Run the diagnostic:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py check_notification_system --verbose
   ```

2. **Check the logs:**
   ```bash
   docker logs whatsappcrm_backend_app --tail 100
   docker logs whatsappcrm_celery_io_worker --tail 100
   ```

3. **Share the output** of these commands when asking for help

---

## 🎓 Understanding the Fix

### What Was Wrong?

1. **SMTP credentials were hardcoded** in the source code instead of being in the `.env` file only
2. **The `.env` file was missing** EMAIL configuration entirely
3. **Documentation was unclear** about which notification groups are required

### What Changed?

1. **`settings.py`**: Removed hardcoded credentials (security fix)
2. **`.env`**: Added complete EMAIL configuration
3. **Documentation**: Created 4 new comprehensive guides

### What You Need to Do?

1. **Verify credentials** in `.env` are correct
2. **Restart services** to load new configuration
3. **Create groups** using management command
4. **Link users** to contacts and groups
5. **Test** that everything works

---

## 🔒 Security Note

⚠️ **Important:** The `.env` file with credentials is currently tracked in Git. This is a security risk.

**What to do:**
1. Read `SECURITY_WARNING_ENV_FILES.md`
2. Change all exposed credentials
3. Stop tracking .env files
4. Create .env.example templates

**Priority:** HIGH (but can be done after getting notifications working)

---

## 🎯 Next Steps

1. ✅ **You've read this** - Good start!
2. 📖 **Read `QUICK_FIX_NOTIFICATION_SMTP.md`** - Do the actions listed
3. 🧪 **Test everything** - Follow the testing section
4. 📋 **Complete the checklist** - Track your progress
5. 🔒 **Fix security issues** - Read the security warning
6. ✨ **Enjoy working notifications!** - You're done!

---

**Created:** 2025-12-09  
**Issue:** morebnyemba/hanna#156  
**Status:** Fixed - User actions required  
**Time to complete:** 30 minutes (minimal) to 2-4 hours (complete with security)
