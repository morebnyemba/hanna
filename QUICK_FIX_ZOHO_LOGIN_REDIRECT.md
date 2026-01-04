# Quick Fix: Zoho API Login Redirect Error

## What You're Seeing

```
[ERROR] Failed to parse JSON response from Zoho API
URL: https://www.zoho.com/fr/crm/?r=null&q=null...
Status: 200, Content-Type: text/html
```

## What It Means

🔴 **Your Zoho access token is invalid or expired**  
The API is redirecting to a login page instead of returning data.

## Quick Fix (3 Steps)

### 1. Deploy This PR

```bash
# Pull the latest code
git pull origin main  # or your branch name

# Restart services
docker-compose restart backend celery_io_worker celery_cpu_worker
```

### 2. Re-authenticate with Zoho

**Option A: Django Admin (Easiest)**
1. Go to `https://backend.hanna.co.zw/django-admin/`
2. Navigate to **Integrations → Zoho Credentials**
3. Update the access token and refresh token
4. Save

**Option B: Django Shell**
```bash
docker-compose exec backend python manage.py shell
```
```python
from integrations.models import ZohoCredential
from django.utils import timezone
from datetime import timedelta

cred = ZohoCredential.get_instance()
cred.access_token = 'your_new_access_token_here'
cred.refresh_token = 'your_refresh_token_here'
cred.expires_in = timezone.now() + timedelta(hours=1)
cred.save()
print("Tokens updated successfully!")
```

### 3. Test the Fix

**From Django Admin:**
- Click the "Sync Zoho" button in the top menu

**Or check Celery logs:**
```bash
docker-compose logs -f celery_io_worker | grep -i zoho
```

**Expected output:**
```
Successfully fetched X items from page 1
Zoho sync completed. Created: Y, Updated: Z, Failed: 0
```

## What Changed

✅ **Before this fix:**
- Confusing "JSON parse error" message
- No indication that token was invalid
- Hard to diagnose the real issue

✅ **After this fix:**
- Clear "Authentication failed" message
- Tells you exactly what to do (re-authenticate)
- No more HTML parsing errors

## Still Having Issues?

### Check These:

1. **API Domain is correct** (Django Admin → Integrations → Zoho Credentials)
   - US: `https://www.zohoapis.com`
   - EU: `https://www.zohoapis.eu`
   - IN: `https://www.zohoapis.in`

2. **Organization ID is set**
   - Find it in your Zoho account settings
   - Must match your Zoho Inventory organization

3. **Credentials are valid**
   - Client ID and Client Secret from Zoho Console
   - Refresh Token doesn't expire (keep it safe!)

### Get More Help

See full documentation: `ZOHO_LOGIN_REDIRECT_FIX.md`

## Why Did This Happen?

Zoho access tokens expire after **1 hour**. When expired:
- Old behavior: Followed redirect → Got HTML → JSON parse error 😵
- New behavior: Detected redirect → Clear error message ✅

The system should auto-refresh tokens, but if the refresh token is invalid, you need to re-authenticate manually.

## Prevention

To avoid this in the future:
1. Keep your refresh token valid
2. Monitor Celery logs for authentication errors
3. Set up alerts for sync failures

---

**Need help?** Check the detailed guide in `ZOHO_LOGIN_REDIRECT_FIX.md`
