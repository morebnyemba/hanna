# Zoho API Login Redirect Fix

## Issue Description

When Celery workers attempt to sync products from Zoho Inventory, they fail with the following error:

```
Failed to parse JSON response from Zoho API. 
URL: https://www.zoho.com/fr/crm/?r=null&q=null&i=https%3A%2F%2Faccounts.zoho.com%2Flogin...
Status: 200
Content-Type: text/html
```

**What's happening:**
- The Zoho API is redirecting to a **login page** instead of returning JSON data
- The HTTP client follows the redirect automatically
- A login HTML page is returned instead of the expected JSON API response
- The JSON parser fails because it receives HTML

## Root Cause

The issue occurs when the Zoho access token is invalid, expired, or not properly configured. When this happens:

1. Zoho API receives a request with invalid/expired token
2. Zoho responds with HTTP 302 redirect to login page
3. Python `requests` library follows the redirect automatically (default behavior)
4. Login page HTML is returned with status 200
5. Code tries to parse HTML as JSON and fails

## Solution

### Code Changes (Already Applied)

Modified `/whatsappcrm_backend/integrations/utils.py` to prevent redirect issues:

#### 1. Disabled Automatic Redirects

Changed all HTTP requests to include `allow_redirects=False`:

```python
# Before (would follow redirects)
response = requests.get(url, headers=headers, params=params, timeout=30)

# After (stops at first redirect)
response = requests.get(url, headers=headers, params=params, timeout=30, allow_redirects=False)
```

#### 2. Added Redirect Detection

```python
# Check if we're being redirected (usually means invalid/expired token)
if response.status_code in (301, 302, 303, 307, 308):
    redirect_location = response.headers.get('Location', 'unknown')
    logger.error(
        f"Zoho API returned redirect (status {response.status_code}) to: {redirect_location}. "
        f"This typically indicates an invalid or expired access token."
    )
    raise Exception(
        f"Authentication failed: Zoho API redirected to login page (status {response.status_code}). "
        f"The access token may be invalid or expired. Please re-authenticate with Zoho."
    )
```

#### 3. Added HTML Response Detection

```python
# Check if response is HTML (indicates we hit a web page, not an API)
content_type = response.headers.get('Content-Type', '')
if 'text/html' in content_type:
    response_preview = response.text[:500] if response.text else "(empty response)"
    logger.error(
        f"Received HTML response instead of JSON from Zoho API. "
        f"URL: {response.url}, Status: {response.status_code}, "
        f"Content-Type: {content_type}, "
        f"Response preview: {response_preview}"
    )
    raise Exception(
        f"Authentication failed: Received HTML page instead of JSON API response. "
        f"The access token may be invalid or expired, or the API endpoint may be incorrect. "
        f"Please verify Zoho credentials and re-authenticate if necessary."
    )
```

## How to Fix in Production

### Step 1: Deploy the Code Fix

The code fix is already in this PR. Deploy it to production:

```bash
# Pull the latest changes
git pull origin <branch-name>

# Restart the backend and Celery workers
docker-compose restart backend celery_io_worker celery_cpu_worker
```

### Step 2: Re-authenticate with Zoho

The fix will now show clear error messages if the token is invalid. You need to refresh the Zoho credentials:

#### Option A: Use Django Admin (Recommended)

1. Log in to Django Admin: `https://backend.hanna.co.zw/django-admin/`
2. Navigate to **Integrations → Zoho Credentials**
3. Click on the existing credential record
4. Follow the Zoho OAuth flow to re-authenticate:
   - Click "Authorize with Zoho" (if there's a link/button)
   - Or manually update the access token and refresh token

#### Option B: Re-run OAuth Flow

If you have an OAuth callback URL configured:

1. Access the Zoho authorization URL
2. Grant permissions
3. System will automatically update the tokens in the database

#### Option C: Manual Token Update

If you have valid tokens from another source:

```python
# Using Django shell
python manage.py shell

from integrations.models import ZohoCredential
from django.utils import timezone
from datetime import timedelta

cred = ZohoCredential.get_instance()
cred.access_token = 'your_new_access_token'
cred.refresh_token = 'your_refresh_token'
cred.expires_in = timezone.now() + timedelta(hours=1)
cred.save()
```

Or via Docker:

```bash
docker-compose exec backend python manage.py shell
# Then run the Python commands above
```

### Step 3: Verify the Fix

After re-authenticating, trigger a Zoho sync:

1. From Django Admin: Click "Sync Zoho" button in the top menu
2. Or via Python:
   ```python
   from products_and_services.tasks import task_sync_zoho_products
   task_sync_zoho_products.delay()
   ```

Check the Celery logs for success:

```bash
docker-compose logs -f celery_io_worker | grep -i zoho
```

Expected output:
```
Successfully fetched X items from page 1
Zoho sync completed. Created: Y, Updated: Z, Failed: 0
```

## Preventing Future Issues

### 1. Monitor Token Expiration

Zoho access tokens typically expire after 1 hour. The system should automatically refresh them, but you should monitor for failures:

```bash
# Check for authentication errors in logs
docker-compose logs celery_io_worker | grep -i "authentication failed"
```

### 2. Verify Credentials Configuration

Ensure these fields are properly set in Django Admin → Integrations → Zoho Credentials:

- ✅ **Client ID**: Your Zoho OAuth client ID
- ✅ **Client Secret**: Your Zoho OAuth client secret  
- ✅ **Refresh Token**: Valid refresh token (doesn't expire)
- ✅ **Access Token**: Current access token (auto-refreshed)
- ✅ **Organization ID**: Your Zoho organization/company ID
- ✅ **API Domain**: Correct regional domain (e.g., `https://www.zohoapis.com`)

### 3. Set Up Periodic Token Refresh

Consider adding a periodic Celery task to refresh tokens before they expire:

```python
# In your Celery beat schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'refresh-zoho-token': {
        'task': 'integrations.tasks.refresh_zoho_token',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}
```

### 4. Alert on Sync Failures

Set up monitoring/alerts for Zoho sync failures:

```python
# In products_and_services/tasks.py
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_sync_zoho_products(self):
    try:
        result = sync_zoho_products_to_db()
        if result['failed'] > 0:
            # Send alert notification
            send_admin_alert(f"Zoho sync completed with {result['failed']} failures")
        return result
    except Exception as e:
        # Send alert for complete failure
        send_admin_alert(f"Zoho sync failed: {str(e)}")
        raise self.retry(exc=e)
```

## Error Messages Reference

After this fix, you'll see clearer error messages:

### Redirect Detection
```
Authentication failed: Zoho API redirected to login page (status 302). 
The access token may be invalid or expired. Please re-authenticate with Zoho.
```
**Action**: Re-authenticate with Zoho to get new tokens

### HTML Response Detection
```
Authentication failed: Received HTML page instead of JSON API response. 
The access token may be invalid or expired, or the API endpoint may be incorrect. 
Please verify Zoho credentials and re-authenticate if necessary.
```
**Action**: Check both credentials AND API domain configuration

### Token Refresh Failure
```
Token refresh failed: Received redirect instead of token response. 
Please verify Zoho credentials (client_id, client_secret, refresh_token) are correct.
```
**Action**: Verify client credentials and refresh token in Django Admin

## Technical Details

### Why Redirects Happen

Zoho APIs use HTTP redirects for various reasons:
- **Invalid/expired token**: Redirect to login page
- **Wrong region**: Redirect to correct regional API
- **Maintenance**: Redirect to maintenance page

By disabling automatic redirects, we can:
1. Detect these scenarios immediately
2. Provide specific error messages
3. Prevent HTML parsing errors
4. Guide users to the correct fix

### HTTP Status Codes Detected

- **301**: Moved Permanently
- **302**: Found (Temporary Redirect)
- **303**: See Other
- **307**: Temporary Redirect
- **308**: Permanent Redirect

### Content-Type Validation

The fix checks the `Content-Type` header:
- ✅ Expected: `application/json`
- ❌ Rejected: `text/html`, `text/plain`, etc.

This catches cases where the API returns an error page without a redirect.

## Testing Checklist

- [x] Code changes prevent automatic redirect following
- [x] Redirect status codes (301-308) are detected and logged
- [x] HTML responses are detected via Content-Type header
- [x] Error messages clearly indicate authentication issues
- [x] All three methods updated: `fetch_products`, `_refresh_token`, `exchange_code_for_tokens`
- [ ] Test with invalid token to verify error message
- [ ] Test with valid token to verify normal operation
- [ ] Test token auto-refresh functionality
- [ ] Verify Celery logs show clear error messages

## Related Documentation

- **Zoho Integration Guide**: `ZOHO_INTEGRATION_README.md`
- **Zoho API Domain Fix**: `ZOHO_API_DOMAIN_FIX.md`
- **Zoho Deployment Guide**: `ZOHO_DEPLOYMENT_GUIDE.md`
- **Zoho Quick Start**: `ZOHO_INTEGRATION_QUICK_START.md`

## Summary

✅ **Fixed**: Added redirect prevention and HTML detection  
✅ **Improved**: Clear error messages for authentication failures  
✅ **Applied**: Fix to all Zoho API request methods  
❌ **Still Required**: Re-authenticate with Zoho to get valid tokens  

The code fix prevents the confusing "JSON parse error" and instead shows:
- Clear authentication failure messages
- Specific guidance on what to do next
- Better logging for troubleshooting

**Next Step**: Re-authenticate with Zoho using Django Admin to get fresh tokens.
