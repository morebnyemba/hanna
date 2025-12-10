# WhatsApp Phone Number Format Fix

## Problem
WhatsApp notifications were failing because phone numbers were being stored in an incorrect format. The system was storing phone numbers like `0772354523` (with a leading 0), but WhatsApp's API requires E.164 format like `263772354523` (country code + number without leading 0).

## Root Cause
In `email_integration/tasks.py`, the `_get_or_create_customer_profile()` function was normalizing phone numbers by removing all non-digit characters, but it wasn't properly formatting them for WhatsApp's E.164 standard.

## Solution
This fix implements the following changes:

### 1. Phone Number Normalization Utility
Created `conversations/utils.py` with a `normalize_phone_number()` function that:
- Removes non-digit characters (except +)
- Removes leading 0 from local numbers
- Adds the default country code (263 for Zimbabwe)
- Returns phone numbers in E.164 format without the + sign

### 2. Updated Contact Creation
Modified the following files to use the new normalization function:
- `email_integration/tasks.py` - When creating contacts from email invoices
- `customer_data/serializers.py` - When creating contacts via API
- `flows/tasks.py` - When processing flow actions

### 3. Management Command
Created `conversations/management/commands/normalize_contact_phone_numbers.py` to fix existing contacts in the database.

## How to Apply the Fix

### Step 1: Review Existing Contacts (Optional)
Run the management command in dry-run mode to see what changes will be made:

```bash
python manage.py normalize_contact_phone_numbers --dry-run
```

### Step 2: Normalize Existing Contacts
Apply the normalization to existing contacts:

```bash
python manage.py normalize_contact_phone_numbers
```

### Step 3: Verify the Changes
Check that contacts now have properly formatted phone numbers:

```bash
python manage.py shell
>>> from conversations.models import Contact
>>> Contact.objects.filter(whatsapp_id__startswith='0').count()  # Should be 0
>>> Contact.objects.filter(whatsapp_id__startswith='263').count()  # Should show Zimbabwe numbers
```

## Testing

### Unit Tests
Run the phone number normalization tests:

```bash
python manage.py test conversations.test_phone_normalization
```

### Integration Testing
1. Process a new invoice via email with a phone number like "077 235 4523"
2. Verify the contact is created with whatsapp_id "263772354523"
3. Verify WhatsApp notifications are sent successfully

## Phone Number Format Examples

| Input Format | Output Format | Notes |
|-------------|---------------|-------|
| `0772354523` | `263772354523` | Removes leading 0, adds country code |
| `077 235 4523` | `263772354523` | Removes spaces |
| `077-235-4523` | `263772354523` | Removes dashes |
| `+263772354523` | `263772354523` | Removes + |
| `263772354523` | `263772354523` | Already correct, unchanged |

## Configuration

The default country code is 263 (Zimbabwe). To use a different country code:

```bash
python manage.py normalize_contact_phone_numbers --country-code=27  # South Africa
```

You can also modify the default in `conversations/utils.py`:

```python
def normalize_phone_number(phone_number: str, default_country_code: str = '263') -> str:
```

## Important Notes

1. **Duplicate Detection**: The normalization command checks for duplicate phone numbers before updating and skips any that would create conflicts.

2. **Email Addresses**: The command automatically skips any `whatsapp_id` values that appear to be email addresses or placeholders (not phone numbers).

3. **Already Formatted Numbers**: Phone numbers that are already in the correct format are skipped.

4. **Future Contact Creation**: All new contacts created after this fix will automatically be normalized to E.164 format.

## Troubleshooting

### Issue: "Contact with whatsapp_id already exists"
**Solution**: This means multiple contacts have the same phone number with different formats (e.g., one with "077..." and another with "263..."). You'll need to manually merge or delete the duplicate contacts before running the normalization.

### Issue: WhatsApp notifications still failing
**Possible causes**:
1. The WhatsApp Business API credentials are incorrect
2. The template names don't match what's synced to Meta
3. The 24-hour messaging window has expired for non-template messages

**Debug steps**:
```bash
# Check notification logs
tail -f logs/django.log | grep -i "whatsapp\|notification"

# Verify contact phone format
python manage.py shell
>>> from conversations.models import Contact
>>> contact = Contact.objects.get(whatsapp_id='<the_number>')
>>> print(contact.whatsapp_id)  # Should be like '263772354523'
```

## Rollback (if needed)

If you need to rollback the changes:

1. The original phone numbers are not backed up automatically
2. You would need to restore from a database backup
3. Consider taking a database backup before running the normalization:

```bash
# For PostgreSQL
pg_dump hanna_db > backup_before_phone_fix.sql

# For Docker
docker exec postgres_container pg_dump -U username hanna_db > backup_before_phone_fix.sql
```

## Support

For issues or questions:
1. Check the logs in `logs/django.log`
2. Review the test cases in `conversations/test_phone_normalization.py`
3. Open an issue on the project repository
