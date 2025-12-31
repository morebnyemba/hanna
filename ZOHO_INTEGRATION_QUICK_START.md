# Zoho Integration Quick Start Guide

## Prerequisites
1. Zoho Inventory account with API access
2. OAuth Client ID and Secret from Zoho API Console
3. Initial access and refresh tokens

## Getting OAuth Tokens (First-Time Setup)

### Step 0: Generate Tokens from Zoho

1. **Create OAuth App in Zoho API Console** (https://api-console.zoho.com/):
   - Create "Server-based Application"
   - Note your Client ID and Client Secret
   - Set Redirect URI (examples):
     - Development: `http://localhost:8000/oauth/callback`
     - Production: `https://backend.hanna.co.zw/oauth/callback`
     - Or use: `https://www.getpostman.com/oauth2/callback` (for testing)

2. **Get Authorization Code**:
   - Open in browser (replace YOUR_CLIENT_ID and YOUR_REDIRECT_URI):
   ```
   https://accounts.zoho.com/oauth/v2/auth?scope=ZohoInventory.items.READ&client_id=YOUR_CLIENT_ID&response_type=code&access_type=offline&redirect_uri=YOUR_REDIRECT_URI
   ```
   - Authorize the app
   - Copy the `code` parameter from the redirect URL

3. **Exchange Code for Tokens**:
   ```bash
   curl -X POST https://accounts.zoho.com/oauth/v2/token \
     -d "code=YOUR_AUTH_CODE" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=YOUR_REDIRECT_URI" \
     -d "grant_type=authorization_code"
   ```
   - Save the `access_token` and `refresh_token` from the response

**Note**: The redirect URI is only needed for initial setup. After that, the system uses the refresh token automatically (no redirect endpoint needed in your app).

## Quick Setup (5 Minutes)

### Step 1: Add Zoho Credentials
1. Go to Django Admin: `/admin`
2. Navigate to: **Integrations → Zoho Credentials**
3. Click **Add Zoho Credential**
4. Fill in:
   ```
   Client ID: [Your Zoho Client ID]
   Client Secret: [Your Zoho Client Secret]
   Access Token: [Initial token from OAuth flow]
   Refresh Token: [Refresh token from OAuth flow]
   Organization ID: [Your Zoho Org ID]
   API Domain: https://inventory.zoho.com
   Scope: ZohoInventory.items.READ
   ```
5. Save

### Step 2: Run Migrations
```bash
cd whatsappcrm_backend
python manage.py migrate integrations
python manage.py migrate products_and_services
```

### Step 3: Trigger First Sync
**Option A - Admin UI (Recommended):**
1. Click **"Sync Zoho"** button in top menu
2. Wait for success message

**Option B - Django Shell:**
```python
python manage.py shell
>>> from products_and_services.tasks import task_sync_zoho_products
>>> task = task_sync_zoho_products.delay()
>>> print(f"Task ID: {task.id}")
```

**Option C - Direct Function Call:**
```python
python manage.py shell
>>> from products_and_services.services import sync_zoho_products_to_db
>>> result = sync_zoho_products_to_db()
>>> print(result)
```

### Step 4: Verify Sync
1. Go to **Products and Services → Products**
2. Check that products have **Zoho Item ID** populated
3. Verify prices and stock quantities are correct

## Common Tasks

### Check Token Status
Admin → Integrations → Zoho Credentials
- Look for **Token Status** column:
  - 🟢 **Valid**: Token is active
  - 🟠 **Expired**: Token will auto-refresh
  - 🔴 **No Token**: Need to add tokens

### Manual Sync Trigger
```python
from products_and_services.services import sync_zoho_products_to_db
stats = sync_zoho_products_to_db()
print(f"Created: {stats['created']}, Updated: {stats['updated']}")
```

### Check Sync History
Look at Product model fields:
- `zoho_item_id`: Zoho's unique identifier
- `updated_at`: Last modification time
- Check logs: `tail -f logs/django.log | grep -i zoho`

## Troubleshooting

### Issue: "Zoho credentials not configured"
**Solution:** Add credentials in Admin → Integrations → Zoho Credentials

### Issue: "Failed to refresh Zoho token"
**Solution:** 
1. Get new tokens from Zoho OAuth flow
2. Update Access Token and Refresh Token in admin

### Issue: "No items fetched"
**Solution:**
1. Verify Organization ID is correct
2. Check API Domain matches your region
3. Ensure scope includes `ZohoInventory.items.READ`

### Issue: Celery task not running
**Solution:**
1. Check Celery worker is running: `celery -A whatsappcrm_backend worker -l info`
2. Check Redis is running: `redis-cli ping`

## File Locations

```
whatsappcrm_backend/
├── integrations/
│   ├── models.py          # ZohoCredential model
│   ├── utils.py           # ZohoClient API wrapper
│   ├── admin.py           # Admin interface
│   └── migrations/
├── products_and_services/
│   ├── models.py          # Product model (with zoho_item_id)
│   ├── services.py        # sync_zoho_products_to_db()
│   ├── tasks.py           # task_sync_zoho_products
│   ├── admin.py           # Product admin actions
│   ├── views.py           # trigger_sync_view
│   └── urls.py            # /admin/sync-zoho/
└── whatsappcrm_backend/
    └── settings.py        # JAZZMIN_SETTINGS (Sync button)
```

## Configuration Options

### Environment Variables
Add to `.env`:
```bash
# Optional: Override Celery settings
CELERY_TASK_TIME_LIMIT_SECONDS=1800
```

### Jazzmin Button Customization
In `settings.py`:
```python
JAZZMIN_SETTINGS = {
    "topmenu_links": [
        {"name": "Sync Zoho", "url": "/api/products-and-services/admin/sync-zoho/", 
         "permissions": ["auth.view_user"], "icon": "fas fa-sync"},
    ],
}
```

## API Endpoints

- **Sync Trigger**: `/api/products-and-services/admin/sync-zoho/` (GET, staff only)
- **Admin Panel**: `/admin/integrations/zohocredential/`

## Next Steps

1. **Schedule Regular Syncs**: Set up Celery Beat for automatic daily syncs
2. **Monitor Sync Logs**: Configure log aggregation for sync monitoring
3. **Customize Field Mapping**: Modify `sync_zoho_products_to_db()` for custom fields
4. **Add Product Images**: Extend sync to include Zoho product images

## Support Resources

- Full Documentation: `ZOHO_INTEGRATION_README.md`
- Test Suite: `integrations/tests.py` and `products_and_services/tests.py`
- Logs: `logs/django.log` and `logs/celery.log`
