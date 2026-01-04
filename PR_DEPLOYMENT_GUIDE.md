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

**Important:** Invoices will now only create OrderItems for products that exist in the database.

Test flow:
1. Ensure products are synced from Zoho first
2. Send a test invoice via email
3. Check that:
   - Order is created successfully
   - OrderItems are created for products that exist
   - Warning logs appear for missing products (expected behavior)

### 3. Monitor Logs

Watch for these warning messages (they are expected and not errors):
```
Product not found for SKU 'XXX' or name 'YYY'. Skipping OrderItem creation. 
Please create product manually or sync from Zoho.
```

These warnings indicate products that need to be synced or created manually.

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

### Issue: "Product not found" warnings in logs
**Solution:** This is expected behavior. Sync products from Zoho or create them manually.

### Issue: OrderItems not created for some invoice line items
**Solution:** 
1. Check which products are missing
2. Sync from Zoho or create products manually
3. Products must exist before processing invoices

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
1. **Product Sync**: Run "Sync Zoho" regularly to keep products updated
2. **Monitor Logs**: Watch for "Product not found" warnings
3. **Create Missing Products**: Address warnings by syncing or manually creating products

### Future Considerations
- Consider setting up automated Zoho sync (e.g., via Celery Beat)
- Create products in Zoho before sending invoices
- Monitor product sync success rate
