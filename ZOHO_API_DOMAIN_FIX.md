# Zoho API Domain Fix (Updated 2026-01-04)

## Issue
The Zoho API was returning a 400 error with the message: "Use the zohoapis domain for API requests."

## Root Cause
The integration was using the old Zoho API domain format and incorrect API path:
- **Old domain**: `https://inventory.zoho.com` or `https://inventory.zohoapis.com`
- **Old path**: `/api/v1/items`

## Solution
Updated to use the correct Zoho API v2 format:
- **New domain**: `https://www.zohoapis.com` (or regional variants)
- **New path**: `/inventory/v1/items`

## Changes Made

### 1. Updated Model Default (integrations/models.py)
- Changed the default `api_domain` from `https://inventory.zohoapis.com` to `https://www.zohoapis.com`
- Updated help text to include all regional domains
- This fix applies to new ZohoCredential instances

### 2. Updated API Client (integrations/utils.py)
- Changed API path from `/api/v1/items` to `/inventory/v1/items`
- This ensures the correct Zoho Inventory API v1 endpoint is used

### 3. Data Migration (integrations/migrations/0003_update_zoho_api_domain.py)
- Automatically updates existing ZohoCredential records
- Converts old domain formats to new formats
- Runs automatically when migrations are applied

### 4. Updated Tests
- Updated test URLs to reflect the new domain and path format

## Regional API Domains

Zoho uses region-specific API domains. The correct domains are:

- **US (Americas)**: `https://www.zohoapis.com`
- **EU (Europe)**: `https://www.zohoapis.eu`
- **IN (India)**: `https://www.zohoapis.in`
- **AU (Australia)**: `https://www.zohoapis.com.au`
- **JP (Japan)**: `https://www.zohoapis.jp`
- **CN (China)**: `https://www.zohoapis.com.cn`

## Migration Steps for Existing Installations

The migration will run automatically when you deploy this fix:

```bash
python manage.py migrate integrations
```

This will:
1. Update any existing ZohoCredential records to use the new domain format
2. Convert old domains to the appropriate regional domain
3. Print confirmation messages for each updated record

### Manual Update (if needed)

If automatic migration fails, update manually via Django Admin:

1. Go to Admin → Integrations → Zoho Credentials
2. Edit your existing credential
3. Update the **API Domain** field to the correct regional domain (see list above)
4. Save the changes

## Verification

After updating, verify the fix works:

1. Check the migration output for successful domain updates
2. Trigger a Zoho sync from the admin panel or wait for scheduled sync
3. Check the logs - you should see successful API calls to the new domain
4. Verify products are being synced without errors
5. Monitor Celery worker logs for any remaining errors

## Related Changes

### Invoice Processing - No Automatic Product Creation

The invoice processing logic **does not** automatically create products. This is the correct behavior to avoid duplicate or incorrect products in the database.

**Current Behavior:**
- When processing invoices, if a product is not found in the database:
  - OrderItem is created with `product=None`
  - Product SKU is stored in `product_sku` field
  - Product description is stored in `product_description` field
  - Processing continues normally for all line items

**For Job Cards:**
- If a product is not found, SerializedItem is NOT created
- Job card is still created (with `serialized_item=None`)
- SerializedItem can be created later when product exists

**Linking Products Later:**
1. Products should be synced from Zoho using "Sync Zoho Products" button in admin
2. Or manually create products in Django Admin
3. Query OrderItems with `product=None` to find unlinked items:
   ```python
   unlinked_items = OrderItem.objects.filter(product__isnull=True)
   ```
4. Update OrderItems to link to the newly created products

## Testing Checklist

After applying these changes:

- [x] Data migration updates existing ZohoCredential records
- [x] Zoho product sync uses correct domain and API path
- [x] Invoice processing creates OrderItems without automatically creating products
- [x] OrderItems store product_sku and product_description when product not found
- [x] Job cards are created without SerializedItems when product missing
- [x] Tests updated to reflect new URL format

## Troubleshooting

If you still encounter errors:

1. **DNS Resolution Error**: Check your region and use the correct regional domain
2. **404 Error**: Verify the API path is `/inventory/v1/items` not `/api/v1/items`
3. **401 Unauthorized**: Refresh your Zoho OAuth tokens via admin panel
4. **Organization ID Error**: Verify organization_id is correctly set in ZohoCredential

Check Django logs and Celery worker logs for detailed error messages:
```bash
# Django logs
docker-compose logs backend

# Celery worker logs
docker-compose logs celery
```

## Documentation References

- [Zoho Inventory API Documentation](https://www.zoho.com/inventory/api/v1/)
- [Zoho API Regional Domains](https://www.zoho.com/accounts/protocol/oauth/multi-dc.html)
