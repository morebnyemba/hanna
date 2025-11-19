# Media Files Serving Fix - Summary

## Problem Identified

Media files were not accessible via HTTPS despite being present in both backend and NPM containers.

**Root Cause:** Django's `static()` helper function only serves files when `DEBUG=True`. In production with `DEBUG=False` (as set in `.env.prod`), the `static()` function returns an empty list of URL patterns, causing Django to not serve media files at all.

### Evidence
- Files existed: `/app/mediafiles/docker-test.txt` (backend) ✓
- Files existed: `/srv/www/media/docker-test.txt` (npm) ✓
- URL returned empty response: `curl https://backend.hanna.co.zw/media/docker-test.txt` ✗
- Configuration in `.env.prod`: `DJANGO_DEBUG=False`

## Solution Applied

Modified `whatsappcrm_backend/whatsappcrm_backend/urls.py` to explicitly serve media files in production mode (when `DEBUG=False`).

### Changes Made

**Before:**
```python
# This only works when DEBUG=True
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**After:**
```python
if settings.DEBUG:
    # Use the helper in debug mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production (DEBUG=False), explicitly serve media files through Django
    from django.views.static import serve
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
```

## How It Works

1. **Development Mode (DEBUG=True):**
   - Uses Django's `static()` helper function
   - Automatic media file serving

2. **Production Mode (DEBUG=False):**
   - Uses explicit `re_path()` with Django's `serve` view
   - Matches any URL starting with `/media/` 
   - Serves files from `MEDIA_ROOT` directory

## Why This Fix Works

- NPM (Nginx Proxy Manager) proxies ALL requests to Django backend
- Without proper URL patterns, Django returns 404 for `/media/` URLs
- The fix ensures Django has URL patterns for media files regardless of DEBUG setting
- Files are served directly by Django's built-in `serve` view

## Testing

After applying this fix, media files should be accessible:

```bash
# Test direct access
curl https://backend.hanna.co.zw/media/docker-test.txt

# Expected response: File content
# Expected status: HTTP 200 OK
```

## Performance Considerations

While this fix makes media files accessible, serving files through Django is not optimal for production. For better performance, consider:

### Option A: Configure NPM Custom Location (Recommended)

Configure NPM to serve media files directly without proxying to Django:

1. Access NPM UI at `http://YOUR-SERVER:81`
2. Edit `backend.hanna.co.zw` proxy host
3. Add Custom Location for `/media`
4. See `NPM_MEDIA_FIX_GUIDE.md` for detailed instructions

This approach:
- ✓ Better performance (nginx serves files directly)
- ✓ Reduced load on Django
- ✓ Better caching
- ✗ Requires manual NPM configuration

### Option B: Use Cloud Storage (Best for Scale)

Use S3-compatible storage with `django-storages`:

```python
# In settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_CUSTOM_DOMAIN = 'cdn.yourdomain.com'
```

This approach:
- ✓ Best performance with CDN
- ✓ Scalable
- ✓ Automatic backups
- ✗ Requires cloud service setup
- ✗ Incurs cloud storage costs

### Option C: Keep Current Fix (Simple)

Keep serving files through Django:

This approach:
- ✓ Simple, no additional configuration
- ✓ Works immediately
- ✓ Sufficient for small to medium traffic
- ✗ Not optimal for high traffic
- ✗ Django serves files (not its primary purpose)

## Files Modified

- `whatsappcrm_backend/whatsappcrm_backend/urls.py` - Fixed media URL patterns

## Files Added

- `NPM_MEDIA_FIX_GUIDE.md` - Comprehensive NPM configuration guide
- `diagnose_npm_media.sh` - Diagnostic script for troubleshooting
- `test_media_urls.py` - Test script to verify URL configuration
- `MEDIA_FIX_SUMMARY.md` - This file

## Deployment

To apply this fix to your server:

```bash
# 1. Pull latest changes
git pull origin main

# 2. Restart backend container
docker-compose restart backend

# 3. Test media access
curl https://backend.hanna.co.zw/media/docker-test.txt

# 4. (Optional) Configure NPM for better performance
# See NPM_MEDIA_FIX_GUIDE.md
```

## Security Note

Serving files through Django in production is generally acceptable for media files that are meant to be public (like product images). However, ensure:

- Media files don't contain sensitive data
- File permissions are properly set (644 for files, 755 for directories)
- File uploads are validated and sanitized
- Consider rate limiting for /media/ URLs if needed

## Related Issues

This fix resolves the issue where:
- Media files were present but not accessible
- curl returned empty responses
- Product images couldn't be accessed by Meta's API for catalog sync

## Next Steps

1. ✓ Apply the fix (completed)
2. Test media file access
3. (Optional) Configure NPM custom location for better performance
4. (Optional) Set up cloud storage for scalability

## References

- Django documentation: [Serving files uploaded by a user](https://docs.djangoproject.com/en/stable/howto/static-files/#serving-files-uploaded-by-a-user-during-development)
- Django `serve` view: [django.views.static.serve](https://docs.djangoproject.com/en/stable/ref/views/#django.views.static.serve)
