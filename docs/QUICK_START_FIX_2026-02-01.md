# QUICK START - Fix Production WhatsApp Errors
**Generated**: February 1, 2026

## 🚨 What Happened
Two critical issues caused WhatsApp messages to fail:
1. **JSON Serialization Error**: Admin notifications crash when message send fails
2. **Template Name Error**: Old template names from v1 still being used

## ✅ What's Been Fixed
- **handlers.py** now passes serializable data instead of Django model objects
- **All code** has been verified to use v2.0.0 template names (`pfungwa_*`)

## 🔧 What You Need to Do (Operations)

### Step 1: Deploy the Code Fix (2 min)
```bash
cd /path/to/hanna
git pull origin main
python manage.py migrate  # Just in case
# Restart Django/Celery services
```

### Step 2: Clear Old Message Queue (3 min)
```bash
python manage.py shell

# Run these commands:
from conversations.models import Message
from django.utils import timezone
from datetime import timedelta

# Mark old stuck messages as failed (won't retry forever)
old_messages = Message.objects.filter(
    status='pending_dispatch',
    created_at__lt=timezone.now() - timedelta(hours=1)
).update(status='failed', error_details={'error': 'Auto-cleared from stuck queue'})

print(f"Cleared {old_messages} old messages")
exit()
```

### Step 3: Check Meta Templates (5 min)
Login to [Meta Business Suite](https://business.facebook.com/) → WhatsApp → Templates

**VERIFY these exist:**
- ✅ `pfungwa_human_handover_flow` (NEW - required for handovers)
- ✅ `pfungwa_message_send_failure` (NEW - admin notifications)
- ✅ All other `pfungwa_*` templates

**DELETE these if they exist** (old v1 templates):
- ❌ `hanna_human_handover_flow_v1_04` 
- ❌ `hanna_message_send_failure`
- ❌ Any other `hanna_*` templates

### Step 4: Sync Templates to System (2 min)
```bash
python manage.py sync_notification_templates_to_meta
# Or manually create from Django shell (see fix plan)
```

### Step 5: Verify Fix (2 min)
```bash
python manage.py shell

from conversations.models import Message

# Check status
sent = Message.objects.filter(status='sent').count()
failed = Message.objects.filter(status='failed').count()
pending = Message.objects.filter(status='pending_dispatch').count()

print(f"Sent: {sent}, Failed: {failed}, Pending: {pending}")
# Pending should be < 10 normally

exit()
```

## 📊 How to Know It Worked

✅ **Signs of Success**:
- Messages are sending again
- Admin notifications appear in technical-admin WhatsApp group
- No "JSON serializable" errors in logs
- No "Template name does not exist" errors

❌ **Signs of Problems**:
- Still seeing errors in logs
- Messages stuck in pending_dispatch > 1 hour old
- No notifications to admin group

## 🔍 Monitor After Fix

```bash
# Watch for errors
tail -f /var/log/hanna/error.log | grep -i "serializ\|template"

# Check message queue
python manage.py shell
from conversations.models import Message
print(Message.objects.values('status').annotate(count=Count('id')).order_by())
```

## 📞 If Issues Persist

1. Check Django error logs for new exceptions
2. Verify Meta Business Account templates are correct
3. Ensure Celery workers are running: `celery -A whatsappcrm_backend worker -l info`
4. Check Redis connection: `redis-cli ping` (should return PONG)
5. Review full fix plan: `docs/PRODUCTION_ERROR_FIX_PLAN_2026-02-01.md`

## 📋 Detailed Documentation
- Full analysis: [`docs/ERROR_LOG_ANALYSIS_2026-02-01.md`](ERROR_LOG_ANALYSIS_2026-02-01.md)
- Complete fix plan: [`docs/PRODUCTION_ERROR_FIX_PLAN_2026-02-01.md`](PRODUCTION_ERROR_FIX_PLAN_2026-02-01.md)

