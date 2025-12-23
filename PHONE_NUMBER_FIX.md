# Phone Number Normalization Fix

## Issue Summary

The system was experiencing database errors when processing email attachments with Gemini AI:

```
django.db.utils.DataError: value too long for type character varying(20)
```

This occurred when creating `InstallationRequest` records with phone numbers that were:
1. Not properly normalized (e.g., `'0773854789-0772368614'` → `'2637738547890772368614'` = 22 chars)
2. Exceeding the database field length constraint of `varchar(20)`

### Root Causes

1. **Phone delimiter pattern incomplete**: The regex pattern for splitting multiple phone numbers didn't include hyphen (`-`) as a delimiter, only slash (`/`), pipe (`|`), comma (`,`), and "or".

2. **Database field length mismatch**: The `contact_phone` field in `InstallationRequest` model is defined as `max_length=50` in the code, but the actual database schema has `varchar(20)`.

## Changes Made

### 1. Fixed Phone Normalization Pattern

**File**: `whatsappcrm_backend/conversations/utils.py`

**Change**: Updated `PHONE_DELIMITER_PATTERN` to include hyphen as a delimiter:

```python
# Before:
PHONE_DELIMITER_PATTERN = re.compile(r'[/\\|,]|\s+or\s+', re.IGNORECASE)

# After:
PHONE_DELIMITER_PATTERN = re.compile(r'[/\\|,\-]|\s+or\s+', re.IGNORECASE)
```

This ensures phone numbers like `'0773854789-0772368614'` are correctly split into `['0773854789', '0772368614']` and only the first number is used.

**Test Added**: Added test case in `test_phone_normalization.py`:
```python
def test_normalize_multiple_numbers_separated_by_hyphen(self):
    """Test multiple numbers separated by hyphen - should use first."""
    result = normalize_phone_number("0773854789-0772368614", default_country_code='263')
    self.assertEqual(result, "263773854789")
```

### 2. Added Defensive Truncation

**Files**: 
- `whatsappcrm_backend/email_integration/tasks.py`
- `whatsappcrm_backend/flows/whatsapp_flow_response_processor.py`

**Change**: Added truncation to 50 characters before saving phone numbers to `InstallationRequest.contact_phone`:

```python
# In email_integration/tasks.py (line ~562):
contact_phone = customer_profile.contact.whatsapp_id[:50] if customer_profile.contact.whatsapp_id else "N/A"

# In flows/whatsapp_flow_response_processor.py (line ~156):
contact_phone = data['contact_phone'][:50] if data.get('contact_phone') else ''
alt_contact_number = data.get('alt_contact_phone', '')[:50] if data.get('alt_contact_phone') else ''
```

This provides defense-in-depth protection even if phone normalization fails or produces unexpected results.

## Required Database Migration

⚠️ **IMPORTANT**: You need to run a database migration to update the schema:

```bash
# Step 1: Generate the migration
docker compose exec backend python manage.py makemigrations customer_data

# Step 2: Apply the migration
docker compose exec backend python manage.py migrate customer_data
```

This will alter the `contact_phone` field from `varchar(20)` to `varchar(50)` to match the model definition.

### Expected Migration

The migration will contain:

```python
operations = [
    migrations.AlterField(
        model_name='installationrequest',
        name='contact_phone',
        field=models.CharField(max_length=50, verbose_name='Contact Phone'),
    ),
]
```

## Testing

### Unit Tests

Run the phone normalization tests:

```bash
docker compose exec backend python manage.py test conversations.test_phone_normalization
```

Expected output: All tests pass, including the new hyphen delimiter test.

### Manual Testing

1. Send an email with an invoice that has a phone number like `0773854789-0772368614`
2. Verify the Celery task processes successfully without the `DataError`
3. Check the created `InstallationRequest` has `contact_phone = '263773854789'`

## Impact

- ✅ Fixes the immediate crash when processing invoices with hyphen-separated phone numbers
- ✅ Prevents future crashes from oversized phone number data
- ✅ Maintains backward compatibility with existing phone number formats
- ✅ No changes to API or external interfaces

## Files Changed

1. `whatsappcrm_backend/conversations/utils.py` - Updated phone delimiter pattern
2. `whatsappcrm_backend/conversations/test_phone_normalization.py` - Added test case
3. `whatsappcrm_backend/email_integration/tasks.py` - Added defensive truncation
4. `whatsappcrm_backend/flows/whatsapp_flow_response_processor.py` - Added defensive truncation

## Migration Status

✅ Code changes complete and committed
⚠️ Database migration required (not committed per repo policy - migrations are gitignored)
📝 User action needed: Run makemigrations and migrate commands above
