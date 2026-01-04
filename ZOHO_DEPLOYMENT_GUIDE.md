# Deployment Guide for Zoho API Domain Fix

## Overview
This guide helps you deploy the fix for the Zoho API domain error that was causing Celery tasks to fail with the message: "Use the zohoapis domain for API requests."

## What Was Fixed

### 1. Zoho API Integration
- **Updated API domain format**: Changed from deprecated `https://inventory.zoho.com` to `https://www.zohoapis.com`
- **Updated API path**: Changed from `/api/v1/items` to `/inventory/v1/items`
- **Regional support**: Proper support for EU, India, Australia, China, and other regions

### 2. Invoice Processing (No Changes Needed)
- Confirmed that products are NOT automatically created from Gemini invoice processing
- System correctly creates OrderItems with SKU/description for manual product linking
- No code changes were necessary for this requirement

## Deployment Steps

### Step 1: Pull the Latest Changes

```bash
git pull origin copilot/fix-whatsapp-integration-errors
```

### Step 2: Restart Services

If using Docker Compose:
```bash
docker-compose down
docker-compose up -d --build
```

Or restart individual services:
```bash
docker-compose restart backend
docker-compose restart celery
```

### Step 3: Update Zoho Domain in Database

Run the management command to update existing ZohoCredential records:

```bash
# Option 1: Preview changes first (recommended)
docker-compose exec backend python manage.py update_zoho_domain --dry-run

# Option 2: Apply changes
docker-compose exec backend python manage.py update_zoho_domain
```

**Expected output:**
```
✓ Updated domain from 'https://inventory.zoho.com' to 'https://www.zohoapis.com'

✓ Successfully updated 1 credential(s).
```

### Step 4: Verify the Fix

#### A. Check Celery Logs
Monitor the Celery worker logs for successful Zoho API calls:

```bash
docker-compose logs -f celery | grep -i zoho
```

**Look for:**
- ✅ "Successfully refreshed Zoho access token"
- ✅ "Successfully fetched X items from page Y"
- ✅ No more "Use the zohoapis domain" errors

#### B. Trigger Manual Sync (Optional)
You can manually trigger a Zoho sync to verify immediately:

1. Go to Django Admin → Integrations → Zoho Credentials
2. Click on your credential
3. Click "Sync Products" button
4. Check that products are being synced without errors

#### C. Check Database
Verify the domain was updated:

```bash
docker-compose exec backend python manage.py shell
```

```python
from integrations.models import ZohoCredential

cred = ZohoCredential.get_instance()
print(f"Current API domain: {cred.api_domain}")
# Should output: Current API domain: https://www.zohoapis.com
```

### Step 5: Monitor Invoice Processing

Invoice processing should continue to work without any changes. Verify by:

1. Send a test invoice email
2. Check that OrderItems are created correctly
3. Verify products are NOT automatically created (expected behavior)

## Regional Configurations

If you're not in the US, update your API domain to the correct region:

| Region | API Domain |
|--------|------------|
| US (Americas) | `https://www.zohoapis.com` |
| EU (Europe) | `https://www.zohoapis.eu` |
| IN (India) | `https://www.zohoapis.in` |
| AU (Australia) | `https://www.zohoapis.com.au` |
| JP (Japan) | `https://www.zohoapis.jp` |
| CN (China) | `https://www.zohoapis.com.cn` |

To update manually:
1. Go to Django Admin → Integrations → Zoho Credentials
2. Edit the API Domain field
3. Save

## Troubleshooting

### Issue: Still getting domain errors after update

**Solution:**
1. Verify the management command ran successfully
2. Check the database directly:
   ```sql
   SELECT api_domain FROM integrations_zohocredential;
   ```
3. Manually update if needed via Django Admin

### Issue: DNS resolution errors (host not found)

**Solution:**
- Check your region and use the correct regional domain
- Verify network connectivity to Zoho APIs
- Check firewall/proxy settings

### Issue: 404 errors from Zoho API

**Solution:**
- Verify the API path is `/inventory/v1/items` (not `/api/v1/items`)
- Check that you pulled the latest code changes
- Restart backend and celery services

### Issue: Products still not syncing

**Solution:**
1. Verify OAuth tokens are valid:
   - Go to Django Admin → Integrations → Zoho Credentials
   - Check "Token Expiration" field
   - If expired, re-authenticate via OAuth flow
2. Verify Organization ID is correct
3. Check Celery worker logs for detailed errors

## Rollback Plan

If you need to rollback (not recommended as old domain is deprecated):

1. Via Django Admin:
   - Go to Integrations → Zoho Credentials
   - Change API Domain back to old value
   - Note: Old domain may not work as Zoho deprecated it

2. Via Git:
   ```bash
   git revert HEAD~3..HEAD
   docker-compose up -d --build
   ```

## Support

If you encounter issues:

1. Check the updated documentation: `ZOHO_API_DOMAIN_FIX.md`
2. Review Celery logs: `docker-compose logs celery`
3. Review Django logs: `docker-compose logs backend`
4. Check this deployment guide's troubleshooting section

## Summary of Changes

- ✅ Updated Zoho API domain format
- ✅ Updated Zoho API path
- ✅ Created management command for easy updates
- ✅ Updated tests
- ✅ Updated documentation
- ✅ Confirmed invoice processing doesn't auto-create products (no changes needed)
- ✅ Passed code review
- ✅ Passed security scan (CodeQL)

## Verification Checklist

After deployment, verify:

- [ ] Management command ran successfully
- [ ] Celery logs show no more domain errors
- [ ] Zoho product sync works (manual test)
- [ ] Invoice processing works (if applicable)
- [ ] No new errors in logs

Once all items are checked, the deployment is complete! 🎉
