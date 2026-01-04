# Deployment Instructions for PR: Fix Zoho API Domain and Remove Auto Product Creation

## Changes Summary
This PR fixes two issues:
1. **Zoho API Domain Error**: Updated to use the correct `zohoapis.com` domain
2. **Removed Automatic Product Creation**: Gemini invoice processing no longer creates products automatically

## Pre-Deployment Steps

### 1. Review Documentation
- Read `ZOHO_API_DOMAIN_FIX.md` for detailed information about the changes
- Understand the impact on invoice and job card processing

### 2. Backup Database (Recommended)
```bash
# Create a backup of your database before deploying
docker compose exec db pg_dump -U your_user your_database > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Deployment Steps

### 1. Pull Latest Changes
```bash
git pull origin main
```

### 2. Restart Backend Services
```bash
docker compose restart backend
docker compose restart celery
```

### 3. Update Zoho API Domain (CRITICAL)

You MUST update the API domain for existing installations:

**Via Django Admin:**
1. Go to Admin → Integrations → Zoho Credentials
2. Edit your existing credential
3. Update the **API Domain** field:
   - Old: `https://inventory.zoho.com`
   - New: `https://inventory.zohoapis.com`
   - (Use appropriate regional domain if not .com)
4. Save the changes

**Via Django Shell:**
```bash
docker compose exec backend python manage.py shell

from integrations.models import ZohoCredential
cred = ZohoCredential.get_instance()
cred.api_domain = 'https://inventory.zohoapis.com'
cred.save()
print(f"Updated to: {cred.api_domain}")
exit()
```

### 4. Sync Products from Zoho

After updating the API domain, sync your products:

1. Go to Django Admin
2. Click "Sync Zoho" button in the top menu
3. Wait for completion
4. Verify products were synced successfully

## Post-Deployment Verification

### 1. Test Zoho Sync
```bash
# Check Celery logs for successful sync
docker compose logs celery --tail=100 | grep "Zoho"
```

Expected output:
- "Successfully fetched X items from Zoho Inventory"
- No 400 errors about API domain

### 2. Test Invoice Processing

### 2. Test Invoice Processing

**Important:** Invoices will automatically create products if they don't exist in the database.

Test flow:
1. Send a test invoice via email
2. Check that:
   - Order is created successfully
   - OrderItems are created for all line items
   - Products are automatically created with `is_active=False` if they didn't exist
   - Review and activate products manually in Django Admin

### 3. Monitor Logs

Watch for these log messages:
- "Created product: [product_name]" - indicates a new product was created
- Products created from invoices will have `is_active=False` and need manual review


## Rollback Plan

If issues occur after deployment:

### Quick Rollback
```bash
git revert HEAD
docker compose restart backend
docker compose restart celery
```

### Restore API Domain
If you need to use the old API domain (not recommended):
```bash
docker compose exec backend python manage.py shell

from integrations.models import ZohoCredential
cred = ZohoCredential.get_instance()
cred.api_domain = 'https://inventory.zoho.com'  # Old domain
cred.save()
exit()
```

Note: The old domain may not work as Zoho has deprecated it.

## Known Issues & Solutions

### Issue: Too many automatically created products
**Solution:** Products created from invoices have `is_active=False`. Review them regularly in Django Admin and activate only legitimate products. Delete duplicates or incorrect entries.

### Issue: Products created with incorrect information
**Solution:** 
1. Edit the product in Django Admin
2. Update SKU, name, price, and other fields as needed
3. Set `is_active=True` when the product is correct
4. Consider syncing from Zoho to get accurate product data

### Issue: Zoho sync still returns 400 error
**Solution:** 
1. Verify API domain is updated correctly
2. Check that domain uses `zohoapis.com` not `zoho.com`
3. Verify OAuth tokens are still valid

## Support

If you encounter issues:
1. Check Django logs: `docker compose logs backend --tail=100`
2. Check Celery logs: `docker compose logs celery --tail=100`
3. Review `ZOHO_API_DOMAIN_FIX.md` for detailed troubleshooting
4. Contact the development team with log outputs

## Maintenance Notes

### Regular Tasks
1. **Product Sync**: Run "Sync Zoho" regularly to keep products updated from the authoritative source
2. **Review Auto-Created Products**: Check Django Admin for products with `is_active=False` from invoice processing
3. **Activate Valid Products**: Review and activate products that are legitimate
4. **Clean Up Duplicates**: Remove duplicate or incorrect auto-created products

### Future Considerations
- Set up automated Zoho sync (e.g., via Celery Beat) to minimize auto-created products
- Ensure Zoho is the primary source of truth for product data
- Periodically review and clean up auto-created products
- Consider deactivating auto-creation if Zoho sync is reliable and frequent
