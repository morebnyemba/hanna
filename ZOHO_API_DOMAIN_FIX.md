# Zoho API Domain Fix

## Issue
The Zoho API was returning a 400 error with the message: "Use the zohoapis domain for API requests."

## Root Cause
The integration was using the old Zoho API domain format (`inventory.zoho.com`) instead of the new required format (`inventory.zohoapis.com`).

## Changes Made

### 1. Updated Model Default (integrations/models.py)
- Changed the default `api_domain` from `https://inventory.zoho.com` to `https://inventory.zohoapis.com`
- Updated help text to reflect correct domain format
- This fix applies to new ZohoCredential instances

### 2. Updated Documentation
- Updated ZOHO_INTEGRATION_README.md to use correct API domain examples

## Migration Steps for Existing Installations

If you have an existing ZohoCredential record in your database, you need to update it:

### Option 1: Via Django Admin Panel
1. Go to Admin → Integrations → Zoho Credentials
2. Edit your existing credential
3. Update the **API Domain** field:
   - Old: `https://inventory.zoho.com`
   - New: `https://inventory.zohoapis.com`
   - For EU: `https://inventory.zohoapis.eu`
   - For India: `https://inventory.zohoapis.in`
   - For Australia: `https://inventory.zohoapis.com.au`
   - For Japan: `https://inventory.zohoapis.jp`
4. Save the changes

### Option 2: Via Django Shell
```python
python manage.py shell

from integrations.models import ZohoCredential

# Get the credential instance
cred = ZohoCredential.get_instance()

# Update the API domain
cred.api_domain = 'https://inventory.zohoapis.com'  # or your regional domain
cred.save()

print(f"Updated API domain to: {cred.api_domain}")
```

### Option 3: Via SQL (PostgreSQL)
```sql
UPDATE integrations_zohocredential 
SET api_domain = REPLACE(api_domain, 'inventory.zoho.com', 'inventory.zohoapis.com');

UPDATE integrations_zohocredential 
SET api_domain = REPLACE(api_domain, 'inventory.zoho.eu', 'inventory.zohoapis.eu');

-- Add similar updates for other regions as needed
```

## Verification

After updating, verify the fix works:

1. Trigger a Zoho sync from the admin panel
2. Check the logs - you should see successful API calls
3. Verify products are being synced without errors

## Related Changes

### Gemini Invoice Processing - Automatic Product Creation ENABLED
Products are automatically created from Gemini invoice processing when they are not found in the database.

**Behavior:**
- When processing invoices, if a product is not found in the database, the system will:
  - Automatically create the product with `is_active=False` (requires manual review)
  - Create the OrderItem with the new product
  - Continue processing other items normally
  
**Product Creation Details:**
- Created products have `is_active=False` to require manual review before activation
- Product type defaults to `HARDWARE`
- Price is taken from the invoice line item
- SKU and name come from the invoice data

**For Job Cards:**
- Similarly, if a product is not found, it will be automatically created
- SerializedItems are created with the new product
- The job card is linked to the SerializedItem

## Testing

After applying these changes, test the following:

1. ✓ Zoho product sync works without errors
2. ✓ Invoice processing creates products automatically when not found
3. ✓ Job card processing creates products automatically when not found
4. ✓ Existing products continue to work normally
5. ✓ Created products have `is_active=False` for manual review

## Rollback

If you need to rollback this change:

1. Edit the ZohoCredential in admin
2. Change the API domain back to the old format
3. Note: The old domain will likely not work as Zoho has deprecated it

## Support

If you encounter issues after this fix:

1. Check that the API domain is correctly set in the admin panel
2. Verify your Zoho OAuth credentials are still valid
3. Check the Django logs for detailed error messages
4. Ensure your Zoho organization_id is correct
