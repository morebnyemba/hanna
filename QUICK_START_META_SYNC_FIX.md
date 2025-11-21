# Quick Start: Meta Sync Version Suffix Fix

## Problem Fixed
Meta's WhatsApp API was rejecting template and flow names with periods (dots) in them. The version suffix `v1.02` was changed to `v1_02` to comply with Meta's naming rules: **only lowercase letters and underscores are allowed**.

## What Changed?

### 1. Default Version Suffix
- **Before**: `v1.02` (contained periods - INVALID ❌)
- **After**: `v1_02` (uses underscores - VALID ✅)

### 2. Template Names Sent to Meta
When you send template messages, the system now automatically appends the version suffix:
- **Local name**: `hanna_admin_24h_window_reminder`
- **Sent to Meta**: `hanna_admin_24h_window_reminder_v1_02`

### 3. Flow Names Sent to Meta
When you sync flows, the version suffix is appended:
- **Local name**: `Solar Installation`
- **Sent to Meta**: `Solar Installation_v1_02`

## How to Deploy

### Step 1: Test with Dry Run (Recommended)
```bash
cd whatsappcrm_backend
python manage.py sync_meta_templates --dry-run
```

Review the output to ensure template names look correct with `_v1_02` suffix.

### Step 2: Sync Templates to Meta
```bash
python manage.py sync_meta_templates
```

This will create templates on Meta with the new naming format.

### Step 3: Sync Flows to Meta
```bash
# Sync all flows as drafts
python manage.py sync_whatsapp_flows --all

# Or sync and publish immediately
python manage.py sync_whatsapp_flows --all --publish
```

## What to Expect

### Success Output
You should see output like:
```
Processing template: 'hanna_admin_24h_window_reminder' (will be synced as 'hanna_admin_24h_window_reminder_v1_02')...
  SUCCESS: Template 'hanna_admin_24h_window_reminder_v1_02' created successfully. ID: 123456789
```

### Error Resolution
If you still see the old format errors, check:
1. Make sure you pulled the latest code
2. Verify `META_SYNC_VERSION_SUFFIX` setting in `.env` (should be `v1_02`)
3. Restart your Django application

## Environment Variable (Optional)

You can customize the version suffix by setting:

```bash
# In .env file
META_SYNC_VERSION_SUFFIX=v1_03

# IMPORTANT: Always use underscores, never dots!
# VALID:   v1_03, v2_00, prod_v1
# INVALID: v1.03, v2.00, V1_03 (uppercase)
```

## Code Changes Summary

### New Utility Function
A new utility function was added to avoid code duplication:

```python
from notifications.utils import get_versioned_template_name

# Usage:
template_name = "new_order_notification"
versioned_name = get_versioned_template_name(template_name)
# Returns: "new_order_notification_v1_02"
```

### Files Modified
1. `whatsappcrm_backend/settings.py` - Default suffix changed
2. `notifications/utils.py` - New utility function added
3. `notifications/services.py` - Uses new utility function
4. `notifications/tasks.py` - Uses new utility function (also fixed a bug)
5. `conversations/tasks.py` - Uses new utility function
6. `flows/test_version_suffix.py` - Tests updated
7. `META_SYNC_VERSION_SUFFIX.md` - Documentation updated

## Troubleshooting

### Issue: Old templates with dots still exist on Meta
**Solution**: Delete old templates from Meta's dashboard, or let them coexist (they won't be used by the new code).

### Issue: Messages failing to send
**Symptom**: "Template not found" errors
**Solution**: Make sure you've run the sync commands after deploying the code.

### Issue: Custom version suffix not working
**Check**:
1. Environment variable is set correctly
2. No dots or special characters in the suffix
3. All characters are lowercase

## Testing Checklist

- [ ] Run dry-run and verify template names look correct
- [ ] Sync templates to Meta successfully
- [ ] Sync flows to Meta successfully
- [ ] Send a test template message
- [ ] Verify message is received correctly
- [ ] Check Django logs for any errors

## Need Help?

If you encounter any issues:
1. Check the logs: `docker-compose logs backend`
2. Review the error messages from sync commands
3. Verify your Meta App Configuration in Django admin
4. Consult `META_SYNC_VERSION_SUFFIX.md` for detailed documentation

## Summary

✅ **Version suffix format fixed**: `v1.02` → `v1_02`  
✅ **Complies with Meta's naming rules**: Only lowercase letters and underscores  
✅ **Automatic versioning**: Template names automatically versioned when sent  
✅ **Backward compatible**: Local database names unchanged  
✅ **No security issues**: CodeQL scan passed with 0 alerts  
✅ **Well tested**: All tests updated and passing  

The fix is ready for deployment! 🚀
