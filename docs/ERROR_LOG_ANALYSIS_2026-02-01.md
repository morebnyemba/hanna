# CRITICAL ERRORS - ANALYSIS AND FIXES
# Date: February 1, 2026

## ERROR 1: Old Template Name Not Found ❌ (CRITICAL)

### Error Message
```
(#132001) Template name does not exist in the translation
template name (hanna_human_handover_flow_v1_04) does not exist in en_US
```

### Root Cause
Code is using OLD `hanna_` prefixed template name that was rebranded to `pfungwa_` in v2.0.0

### Locations with Old Template Names
Need to find and replace:
- `hanna_human_handover_flow_v1_04` → `pfungwa_human_handover_required`
- `hanna_human_handover_flow` → `pfungwa_human_handover_required`
- Any other `hanna_*` templates → `pfungwa_*` equivalents

### Fix Strategy
Run this audit:
```bash
grep -r "hanna_" whatsappcrm_backend/ --include="*.py" | grep -v "test" | grep -v "old"
```

Then replace with corresponding `pfungwa_` templates from v2.0.0 notification templates list.

---

## ERROR 2: JSON Serialization Error ❌ (CRITICAL)

### Error Message
```
TypeError: Object of type Message is not JSON serializable
File: notifications/handlers.py, line 25
```

### Root Cause
```python
# WRONG - Passing Message object
queue_notifications_to_users(
    template_name='pfungwa_message_send_failure',
    group_names=["Technical Admin"],
    related_contact=contact,
    template_context={'message': message_instance}  # ❌ Message object not JSON serializable
)
```

### The Fix
```python
# CORRECT - Pass only serializable data (IDs, strings, dicts)
queue_notifications_to_users(
    template_name='pfungwa_message_send_failure',
    group_names=["Technical Admin"],
    related_contact=contact,
    template_context={
        'message_id': message_instance.id,
        'message_body': message_instance.message_body,
        'error_time': message_instance.updated_at.isoformat() if message_instance.updated_at else '',
        'contact_name': contact.name or contact.whatsapp_id,
        'contact_whatsapp_id': contact.whatsapp_id
    }
)
```

### What Can Be Passed in template_context
✅ **Allowed**:
- Strings, numbers, booleans
- Lists/dicts (with serializable content)
- Dates/times (as .isoformat() strings)
- Model IDs (integer primary keys)

❌ **NOT Allowed**:
- Django model instances (Message, Contact, User, etc.)
- QuerySets
- Complex objects

### Affected Files to Fix
1. `whatsappcrm_backend/notifications/handlers.py` (line 25)
2. Check any other places calling `queue_notifications_to_users()` with model objects

---

## ERROR 3: Message Queue Deadlock ⚠️ (BLOCKING)

### Error Message
```
Halting message ID 1838 for contact 263787211325. 
Waiting for preceding message ID 1837 (Status: pending_dispatch).
Max retries exceeded for message 1838 while waiting. Marking as failed.
```

### Root Cause
Message 1837 is stuck in `pending_dispatch` state, blocking message 1838.
The retry loop waits for the preceding message indefinitely until max retries exceeded.

### Why It's Stuck
- Meta API called with template `hanna_human_handover_flow_v1_04`
- Template doesn't exist (Error #132001)
- Message never transitions from `pending_dispatch` to `sent` or `failed`
- Message 1838 waits forever for 1837

### The Solution
**Root issue is ERROR 1** (old template name). Once templates are renamed:
1. Old messages with bad template names will fail quickly (not hang)
2. New messages will send successfully
3. No more queue deadlocks

### Temporary Mitigation
If you can't fix immediately:
```python
# In meta_integration/tasks.py
# Add a max wait time to prevent infinite hangs
MAX_WAIT_RETRIES = 5  # Not 100+
if wait_retries >= MAX_WAIT_RETRIES:
    # Mark waiting message as failed instead of retrying forever
    message_to_send.status = 'failed'
    message_to_send.save()
    # Skip this message and continue with next
    return
```

---

## IMPLEMENTATION PRIORITY

### P0 - Do Immediately (Blocks Everything)
1. **Fix template names: `hanna_*` → `pfungwa_*`**
   - Find all old template references
   - Replace with new v2.0.0 template names
   - Verify templates exist in Meta

### P1 - Do Next (Prevents New Errors)
2. **Fix JSON serialization in handlers.py**
   - Replace Message object with serializable data
   - Audit all queue_notifications_to_users() calls
   - Ensure no model objects in template_context

### P2 - Do After (Prevents Future Issues)
3. **Add queue timeout logic**
   - Prevent infinite waiting
   - Fail fast on stuck messages
   - Log queue issues clearly

---

## TEMPLATE NAME MAPPING (v2.0.0)

From releases/RELEASE_NOTES_v2.0.0.md:

| Old Name | New Name | Purpose |
|----------|----------|---------|
| `hanna_human_handover_required` | `pfungwa_human_handover_required` | Human intervention needed |
| `hanna_message_send_failure` | `pfungwa_message_send_failure` | Message failed to send |
| `hanna_admin_24h_window_reminder` | `pfungwa_admin_24h_window_reminder` | 24h window expiring |
| `hanna_installation_scheduled` | `pfungwa_installation_scheduled` | Installation scheduled |
| `hanna_installation_complete` | `pfungwa_installation_complete` | Installation done |
| `hanna_warranty_claim_submitted` | `pfungwa_warranty_claim_submitted` | Warranty claim received |
| `hanna_warranty_claim_approved` | `pfungwa_warranty_claim_approved` | Warranty approved |
| (All 30 templates) | (Prefixed with `pfungwa_`) | See releases/RELEASE_NOTES_v2.0.0.md |

---

## VERIFICATION STEPS

After fixes:

1. **Check Meta has templates**
   ```
   Meta Business Account → WhatsApp → Templates
   Verify all 30 pfungwa_* templates exist
   ```

2. **Test notification sending**
   ```python
   from notifications.services import queue_notifications_to_users
   from django.contrib.auth.models import Group
   
   # Test 1: Simple notification
   queue_notifications_to_users(
       template_name='pfungwa_message_send_failure',
       group_names=['Technical Admin'],
       template_context={
           'contact_name': 'Test User',
           'contact_whatsapp_id': '+1234567890',
           'message_id': 123,
           'error_time': '2026-02-01 10:15:36'
       }
   )
   ```

3. **Monitor logs**
   ```
   Should see: "Task dispatch_notification_task succeeded"
   Should NOT see: "Object of type Message is not JSON serializable"
   Should NOT see: "#132001 Template name does not exist"
   ```

4. **Check message queue**
   ```python
   from conversations.models import Message
   
   # Should NOT have pending_dispatch messages > 5 minutes old
   Message.objects.filter(
       status='pending_dispatch',
       created_at__lt=timezone.now() - timedelta(minutes=5)
   )
   ```

---

## RELATED CODE REVIEW NEEDED

After main fixes, audit these files for similar issues:

1. `meta_integration/tasks.py` - Message sending logic
2. `flows/whatsapp_flow_response_processor.py` - Flow notifications
3. `stats/signals.py` - Stats notification calls
4. `products_and_services/solar_automation.py` - Automation notifications
5. `notifications/tasks.py` - Task dispatch logic

All places calling `queue_notifications_to_users()` should be checked for:
- ✅ Using `pfungwa_*` template names
- ✅ Passing only serializable data in template_context
- ✅ Not passing model instances

---

## SUMMARY

| Issue | Severity | Fix Time | Impact |
|-------|----------|----------|--------|
| Old template names | 🔴 CRITICAL | 30 min | Messages fail, queue deadlocks |
| JSON serialization | 🔴 CRITICAL | 15 min | Notifications crash on error |
| Queue deadlock | 🟡 HIGH | 5 min | Temporary fix + root cause resolution |

**Total Time to Fix**: ~1 hour
**Estimated Impact**: Fixes 95% of current errors

