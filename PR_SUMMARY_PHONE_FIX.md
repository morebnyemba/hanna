# PR Summary: WhatsApp Notification Phone Number Format Fix

## Overview
This PR resolves the issue where WhatsApp notifications were failing to send due to phone numbers being stored in an incorrect format.

## Problem Statement
**Issue:** WhatsApp notification sending failed
**Root Cause:** Phone numbers were stored with a leading "0" (e.g., `0772354523`) instead of the E.164 format required by WhatsApp's API (e.g., `263772354523`)

## Evidence from Logs
```
[2025-12-10 09:17:43] DEBUG utils Sending WhatsApp message via config 'Hanna1'. 
URL: https://graph.facebook.com/v24.0/804344219427309/messages, 
Payload: {"messaging_product": "whatsapp", "to": "0772354523", ...}
```

The payload shows `"to": "0772354523"` which is not a valid E.164 format for WhatsApp.

## Solution Implemented

### 1. Phone Number Normalization Utility (`conversations/utils.py`)
Created a robust function that:
- Removes non-digit characters (spaces, dashes, parentheses)
- Strips leading '+' symbol
- Removes leading '0' and adds country code
- Handles already-formatted international numbers
- Validates result length (10-15 digits)

**Example Transformations:**
| Input | Output |
|-------|--------|
| `0772354523` | `263772354523` |
| `077 235 4523` | `263772354523` |
| `+263 77 235 4523` | `263772354523` |
| `263772354523` | `263772354523` (unchanged) |

### 2. Updated Contact Creation Points
Modified three key locations where contacts are created:

**a) Email Integration (`email_integration/tasks.py`)**
- Modified `_get_or_create_customer_profile()` function
- Added phone normalization before contact creation
- Added validation to handle normalization failures

**b) API Serializer (`customer_data/serializers.py`)**
- Added `validate_whatsapp_id()` method to `SimpleContactSerializer`
- Automatically normalizes phone numbers from API requests
- Preserves non-phone values (emails, placeholders)

**c) Flow Processing (`flows/tasks.py`)**
- Normalizes recipient WhatsApp IDs before message dispatch
- Handles empty/null values gracefully
- Falls back to original value if normalization fails

### 3. Management Command
Created `normalize_contact_phone_numbers` command to fix existing data:

```bash
# Preview changes (safe)
python manage.py normalize_contact_phone_numbers --dry-run

# Apply changes
python manage.py normalize_contact_phone_numbers

# Use different country code
python manage.py normalize_contact_phone_numbers --country-code=27
```

Features:
- Dry-run mode for safe testing
- Duplicate detection
- Skips email addresses and placeholders
- Detailed progress reporting
- Error handling

### 4. Testing
Created comprehensive unit tests (`conversations/test_phone_normalization.py`):
- 14 test cases covering various input formats
- Edge cases (empty strings, None values)
- International numbers
- Different country codes

### 5. Documentation
Created `WHATSAPP_PHONE_NUMBER_FIX.md` with:
- Problem explanation
- Solution overview
- Deployment instructions
- Troubleshooting guide
- Rollback procedures

## Files Changed
```
New files:
  + conversations/utils.py (56 lines)
  + conversations/management/commands/normalize_contact_phone_numbers.py (111 lines)
  + conversations/test_phone_normalization.py (72 lines)
  + WHATSAPP_PHONE_NUMBER_FIX.md (146 lines)

Modified files:
  ~ email_integration/tasks.py (+7 lines)
  ~ customer_data/serializers.py (+10 lines)
  ~ flows/tasks.py (+7 lines)

Total: 7 files, +407 lines, -2 lines
```

## Code Quality
✅ **Code Review:** All feedback addressed
✅ **Security Scan:** No vulnerabilities detected (CodeQL)
✅ **Syntax Check:** All files compile successfully
✅ **Unit Tests:** All tests pass

## Deployment Steps

### 1. Deploy the Code
```bash
git pull origin copilot/fix-whatsapp-notification-error
# Restart application
```

### 2. Preview Changes (Optional)
```bash
python manage.py normalize_contact_phone_numbers --dry-run
```

### 3. Fix Existing Contacts
```bash
python manage.py normalize_contact_phone_numbers
```

### 4. Verify
```bash
# Check that no contacts have leading 0
python manage.py shell
>>> from conversations.models import Contact
>>> Contact.objects.filter(whatsapp_id__startswith='0').count()
# Should return 0

# Check Zimbabwe numbers are properly formatted
>>> Contact.objects.filter(whatsapp_id__startswith='263').count()
# Should show the count of Zimbabwe numbers
```

### 5. Test Notifications
Process a new invoice or trigger a notification to verify WhatsApp messages are sent successfully.

## Impact Assessment

### Positive Impact
✅ WhatsApp notifications will now send successfully
✅ All new contacts will be created with correct phone format
✅ Existing contacts can be easily fixed with management command
✅ Better handling of international phone numbers
✅ Improved code maintainability

### Risk Assessment
⚠️ **Low Risk:**
- Changes are surgical and focused
- Backward compatible (old format still handled)
- Dry-run mode available for testing
- No database schema changes
- Existing functionality preserved

### Rollback Plan
If issues occur:
1. Revert to previous commit
2. Restore database from backup (if contacts were normalized)
3. No migrations to reverse

## Testing Recommendations

### Manual Testing
1. **Email Invoice Processing**
   - Send a test invoice with phone number "077 235 4523"
   - Verify contact created with "263772354523"
   - Verify WhatsApp notification sent

2. **API Contact Creation**
   - POST to contact API with "0772354523"
   - Verify stored as "263772354523"

3. **Flow Processing**
   - Trigger a flow that creates contacts
   - Verify phone numbers are normalized

### Monitoring
Watch for:
- WhatsApp API success rates
- Contact creation logs
- Any normalization warnings in logs

## Questions & Support
- **Documentation:** See `WHATSAPP_PHONE_NUMBER_FIX.md`
- **Issues:** Check logs for normalization warnings
- **Contact:** Open an issue on the repository

## Conclusion
This fix resolves the WhatsApp notification failure by ensuring all phone numbers are stored in the E.164 format required by WhatsApp's API. The solution is minimal, well-tested, and includes tools to fix existing data.

**Status:** ✅ Ready for Deployment
