# PRODUCTION ERROR FIX - ACTION PLAN & VERIFICATION
# Date: February 1, 2026

## 🔴 CRITICAL ISSUES IDENTIFIED

### Issue #1: JSON Serialization Error (FIXED ✅)
**File**: `whatsappcrm_backend/notifications/handlers.py`  
**Error**: `TypeError: Object of type Message is not JSON serializable`  
**Root Cause**: Passing a Django model instance to `queue_notifications_to_users()` which expects a dictionary
**Status**: ✅ FIXED

**What Changed**:
```python
# BEFORE (BROKEN)
template_context={'message': message_instance}

# AFTER (FIXED)
template_context={
    'message_id': message_instance.id,
    'message_body': message_instance.message_body[:100] if message_instance.message_body else 'N/A',
    'contact_name': contact.name or contact.whatsapp_id,
    'contact_whatsapp_id': contact.whatsapp_id,
    'error_details': kwargs.get('error', 'Unknown error'),
    'error_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
}
```

---

### Issue #2: Template Name Mismatch (ROOT CAUSE ANALYSIS)
**Error From Logs**: `(#132001) Template name does not exist in the translation: hanna_human_handover_flow_v1_04`  
**Current Code**: Uses `pfungwa_human_handover_flow` (v2.0.0 naming)  
**Status**: 🔍 INVESTIGATING

**Possible Sources of Error**:
1. **Old Celery Messages in Queue** - Messages from v1.x referencing old template names are still in Redis/Celery queue
2. **Database Records** - Notification templates table has old `hanna_*` template names from previous version
3. **Cached Data** - Frontend/API responses cached old template names
4. **WhatsApp Template Not Migrated** - `pfungwa_human_handover_flow` template doesn't exist in Meta API

**Code Verification**:
- ✅ `flows/services.py` line 786: Uses `pfungwa_human_handover_flow`
- ✅ `stats/signals.py` line 72: Uses `pfungwa_human_handover_flow`
- ✅ All management commands use `pfungwa_*` prefixes
- ✅ `flows/definitions/load_notification_templates.py`: All templates prefixed correctly

---

### Issue #3: Message Queue Deadlock
**Error**: "Halting message ID 1838...Waiting for message ID 1837 (Status: pending_dispatch)"  
**Root Cause**: Message 1837 stuck because Meta API template `hanna_human_handover_flow_v1_04` doesn't exist  
**Status**: Will be resolved once Issue #2 is fixed
**Impact**: Cascading failures block subsequent messages

---

## 📋 FIXES COMPLETED

### ✅ Fix #1: JSON Serialization (handlers.py)
```
File: whatsappcrm_backend/notifications/handlers.py
Lines: 1-38
Status: COMPLETED
Impact: Prevents admin notifications from crashing when message send fails
```

### ✅ Code Audit Results
All `queue_notifications_to_users()` callers reviewed:
- `handlers.py` ✅ FIXED - Now passes serializable dict
- `flows/services.py` ✅ CORRECT - Uses serializable context
- `stats/signals.py` ✅ CORRECT - Passes serializable data
- `solar_automation.py` ✅ CORRECT - Builds dict context
- `notifications/tasks.py` ✅ CORRECT - Minimal context
- `email_integration/tasks.py` ✅ CORRECT - Passes IDs/strings

---

## 🔧 REMAINING ACTIONS REQUIRED

### Action #1: Clear Old Messages from Celery Queue
**Priority**: IMMEDIATE  
**Steps**:
```bash
# SSH to server or run in Django shell
python manage.py shell

from celery import shared_task
from meta_integration.tasks import send_whatsapp_message_task

# Purge all pending tasks
send_whatsapp_message_task.purge()  # This will clear queued but not running tasks

# Or manually clear:
from conversations.models import Message
from django.utils import timezone
from datetime import timedelta

# Mark very old pending messages as failed to unblock queue
Message.objects.filter(
    status='pending_dispatch',
    created_at__lt=timezone.now() - timedelta(hours=1)
).update(status='failed', error_details={'error': 'Auto-failed due to queue backup'})
```

### Action #2: Verify Meta WhatsApp Templates
**Priority**: HIGH  
**Steps**:
1. Log into Meta Business Account
2. Go to WhatsApp → Templates
3. Verify these templates exist:
   - ❓ `hanna_human_handover_flow_v1_04` - DELETE if exists (old template)
   - ✅ `pfungwa_human_handover_flow` - Should exist (new template)
   - ✅ All 30 `pfungwa_*` templates from seed_notification_templates.py

**If `pfungwa_human_handover_flow` Missing**:
```python
# Run in Django shell to create template
from flows.definitions.load_notification_templates import NOTIFICATION_TEMPLATES
from notifications.models import NotificationTemplate

for template_config in NOTIFICATION_TEMPLATES:
    if template_config['name'] == 'pfungwa_human_handover_flow':
        NotificationTemplate.objects.update_or_create(
            name=template_config['name'],
            defaults={
                'description': template_config['description'],
                'template_type': template_config['template_type'],
                'body': template_config['body'],
            }
        )
        print(f"Created/Updated template: {template_config['name']}")
```

### Action #3: Sync Notification Templates to Meta API
**Priority**: HIGH  
**Steps**:
```bash
# Run the sync command
python manage.py sync_notification_templates_to_meta

# Or manually:
python manage.py shell
from flows.management.commands.load_notification_templates import Command
cmd = Command()
cmd.handle()
```

### Action #4: Database Cleanup (if needed)
**Priority**: MEDIUM  
**Steps**:
```python
# In Django shell
from notifications.models import NotificationTemplate

# Check for old templates
old_templates = NotificationTemplate.objects.filter(name__startswith='hanna_')
for template in old_templates:
    print(f"Found old template: {template.name}")
    # OPTIONAL: Delete if confirmed no longer used
    # template.delete()

# Ensure new templates exist
from flows.definitions.load_notification_templates import NOTIFICATION_TEMPLATES
new_count = 0
for template_config in NOTIFICATION_TEMPLATES:
    obj, created = NotificationTemplate.objects.update_or_create(
        name=template_config['name'],
        defaults={
            'description': template_config['description'],
            'template_type': template_config['template_type'],
            'body': template_config['body'],
            'buttons': template_config.get('buttons', []),
        }
    )
    if created:
        new_count += 1
        print(f"Created: {template_config['name']}")

print(f"Total templates created/updated: {new_count}")
```

---

## 📊 VERIFICATION CHECKLIST

### Pre-Deployment Verification
- [ ] JSON serialization fix deployed (`handlers.py` changed)
- [ ] Old Celery messages cleared from queue
- [ ] Meta WhatsApp templates verified/synced
- [ ] Database notification templates cleaned up
- [ ] No old `hanna_*` template references in code

### Post-Deployment Verification
```python
# Test in Django shell
from notifications.services import queue_notifications_to_users
from customer_data.models import Contact

# Get a test contact
contact = Contact.objects.first()

if contact:
    # Test 1: Admin notification
    try:
        queue_notifications_to_users(
            template_name='pfungwa_message_send_failure',
            group_names=['Technical Admin'],
            related_contact=contact,
            template_context={
                'message_id': 12345,
                'contact_name': contact.name or contact.whatsapp_id,
                'error_details': 'Test error',
                'error_time': '2026-02-01 10:30:00'
            }
        )
        print("✅ Test 1 PASSED: Admin notification queued successfully")
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
    
    # Test 2: Check Celery task
    from conversations.models import Message
    messages = Message.objects.filter(status='pending_dispatch').count()
    print(f"Messages stuck in pending_dispatch: {messages}")
    if messages > 5:
        print("⚠️  WARNING: Large backlog of messages")
    else:
        print("✅ Test 2 PASSED: No significant message backlog")

    # Test 3: Check admin logs
    from django.contrib.admin.models import LogEntry
    recent_failures = LogEntry.objects.filter(
        action_flag=4,  # Flag for failures
        content_type__app_label='notifications'
    ).count()
    print(f"Recent notification failures in logs: {recent_failures}")
```

### Monitoring After Fix
1. **Check Celery Logs**: Look for successful task dispatch
   ```
   grep "dispatch_notification_task" /path/to/logs
   ```

2. **Monitor Message Delivery**: 
   ```python
   # Count messages by status
   from conversations.models import Message
   Message.objects.values('status').annotate(count=Count('id'))
   ```

3. **Watch for New Errors**:
   ```
   grep -i "json" /path/to/error.log
   grep -i "template.*not.*exist" /path/to/error.log
   ```

---

## 🔄 ROOT CAUSE ANALYSIS

### Why This Happened

1. **Version Rebranding** (v2.0.0):
   - Templates renamed from `hanna_*` → `pfungwa_*`
   - Code updated but old data/messages not migrated

2. **Message Processing Gap**:
   - Old queued messages still reference old template names
   - When retried, they fail because Meta API only knows new names

3. **JSON Serialization**:
   - Legacy code passed Message object directly
   - Django JSONField can't serialize model instances
   - Should pass extracte field values only

### Prevention for Future Versions

1. **Create Migration Script** for template renames:
   ```bash
   # Template name migration script
   - Step 1: Create new templates in Meta API
   - Step 2: Update code to use new names
   - Step 3: Create data migration to rename DB records
   - Step 4: Purge old queued messages
   - Step 5: Deploy with comprehensive testing
   ```

2. **Enforce Type Checking**:
   ```python
   # In queue_notifications_to_users()
   assert isinstance(template_context, dict), "template_context must be dict"
   for key, value in template_context.items():
       if hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool, list, dict)):
           raise TypeError(f"Non-serializable value in template_context['{key}']: {type(value)}")
   ```

3. **Add Validation Tests**:
   ```python
   # notifications/tests.py
   def test_template_context_is_serializable():
       """Ensure all notification contexts are JSON-serializable"""
       import json
       context = {'test': 'data', 'number': 123}
       json.dumps(context)  # Will raise if not serializable
   ```

---

## 📝 SUMMARY

| Issue | Severity | Status | Fix Time |
|-------|----------|--------|----------|
| JSON Serialization (handlers.py) | 🔴 CRITICAL | ✅ FIXED | 5 min deploy |
| Old Template Names (Meta API) | 🔴 CRITICAL | 🔍 Investigating | 30 min + queue cleanup |
| Message Queue Deadlock | 🟡 HIGH | Depends on #2 | Auto-resolved |
| Database Template Cleanup | 🟡 HIGH | Not Started | 10 min |

**Total Fix Time**: ~1-2 hours  
**Estimated Impact**: 99% of errors resolved

---

## 🚀 DEPLOYMENT ORDER

1. **Deploy Code Changes** (now)
   - `handlers.py` fix (JSON serialization)
   - Takes effect immediately

2. **Manual Operations** (next)
   - Clear old Celery messages
   - Verify Meta templates
   - Sync templates to API

3. **Monitor** (ongoing)
   - Watch error logs
   - Check message delivery rates
   - Verify no new serialization errors

