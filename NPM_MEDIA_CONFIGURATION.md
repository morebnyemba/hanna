# Nginx Proxy Manager - Media Files Configuration

## Overview

To make product images accessible to Meta's servers for catalog synchronization, you need to configure Nginx Proxy Manager (NPM) to serve media files from the shared `mediafiles_volume`.

## Prerequisites

1. Docker containers are running with the updated `docker-compose.yml`
2. The `mediafiles_volume` is now mounted to NPM at `/srv/www/media` (read-only)
3. You have access to the NPM Admin UI at `http://your-server:81`

## Configuration Steps

### Step 1: Access NPM Admin UI

1. Open your browser and navigate to: `http://your-server-ip:81`
2. Login with your NPM admin credentials
   - Default credentials (if first time):
     - Email: `admin@example.com`
     - Password: `changeme`
   - **IMPORTANT**: Change these credentials immediately after first login

### Step 2: Add Custom Location for Media Files

For your `backend.hanna.co.zw` proxy host:

1. Go to **Hosts** → **Proxy Hosts**
2. Find and click on `backend.hanna.co.zw` entry
3. Go to the **Custom Locations** tab
4. Click **Add Location**

Configure the location as follows:

**Location:**
```
/media/
```

**Scheme:**
```
http
```

**Forward Hostname / IP:**
```
npm
```

**Forward Port:**
```
Leave empty or use any value (won't be used)
```

**Custom Config:**
```nginx
# Serve media files directly from the volume
alias /srv/www/media/;
expires 7d;
add_header Cache-Control "public";
add_header Access-Control-Allow-Origin "*";

# Security headers
add_header X-Content-Type-Options "nosniff";

# Enable directory indexing for testing (optional, can remove in production)
# autoindex on;

# Logging
access_log /data/logs/media-access.log;
error_log /data/logs/media-error.log;
```

5. Click **Save**

### Step 3: Verify Configuration

Test that media files are accessible:

```bash
# 1. Check if the media directory exists in NPM container
docker exec whatsappcrm_npm ls -la /srv/www/media/

# 2. Test a specific image (replace with actual filename)
curl -I https://backend.hanna.co.zw/media/product_images/your-image.png

# Expected response:
# HTTP/2 200
# Content-Type: image/png
# Cache-Control: public
# ...

# 3. If you get 404, check:
#    - File exists: docker exec whatsappcrm_backend ls -la /app/mediafiles/product_images/
#    - Volume is mounted: docker inspect whatsappcrm_npm | grep -A 10 Mounts
```

### Step 4: Test Product Sync

1. Go to Django Admin → Products
2. Select a product with an image
3. Click "Reset Meta sync attempts" action
4. Save the product
5. Check logs for successful sync:
   ```bash
   docker logs whatsappcrm_backend_app | grep "✓ Successfully"
   ```

## Troubleshooting

### Issue: 404 Not Found for /media/ URLs

**Cause**: NPM custom location not configured or media volume not mounted

**Solution**:
1. Verify volume is mounted: `docker inspect whatsappcrm_npm | grep media`
2. Check NPM custom location configuration
3. Restart NPM: `docker-compose restart npm`

### Issue: 403 Forbidden

**Cause**: Permission issues on media files

**Solution**:
```bash
# Check permissions in backend container
docker exec whatsappcrm_backend ls -la /app/mediafiles/

# If needed, fix permissions
docker exec whatsappcrm_backend chmod -R 755 /app/mediafiles/
```

### Issue: Images still not syncing

**Cause**: Meta's servers might be caching the 404 response

**Solution**:
1. Wait a few minutes for Meta's cache to expire
2. Use Django admin to reset sync attempts
3. Save product again to trigger retry

## Alternative: Direct Django Serving (Development Only)

If you're in development and don't want to configure NPM, you can temporarily serve media files directly from Django:

**In `whatsappcrm_backend/whatsappcrm_backend/urls.py`:**

```python
from django.conf import settings
from django.conf.urls.static import static

# At the end of urlpatterns:
if settings.DEBUG or True:  # Force enable for testing
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Note**: This is NOT recommended for production as Django is inefficient at serving static files.

## Production Best Practices

### 1. Use a CDN (Recommended)

For production, consider using a CDN:

**Option A: AWS S3 + CloudFront**
```python
# In settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_CUSTOM_DOMAIN = 'cdn.yourdomain.com'
```

**Option B: DigitalOcean Spaces**
```python
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_ENDPOINT_URL = 'https://nyc3.digitaloceanspaces.com'
AWS_STORAGE_BUCKET_NAME = 'your-space'
```

### 2. Enable CORS for Meta

If using a separate domain for media:

```nginx
# In NPM custom location config
add_header Access-Control-Allow-Origin "https://facebook.com";
add_header Access-Control-Allow-Origin "https://graph.facebook.com";
add_header Access-Control-Allow-Methods "GET, HEAD";
```

### 3. Monitor Access Logs

```bash
# View media access logs
docker exec whatsappcrm_npm tail -f /data/logs/media-access.log

# Check for Meta's user agent
docker exec whatsappcrm_npm grep "facebookexternalua" /data/logs/media-access.log
```

## Security Considerations

1. **Read-only mount**: The mediafiles_volume is mounted read-only (`:ro`) to NPM for security
2. **No directory listing**: Remove `autoindex on;` in production
3. **Rate limiting**: Consider adding rate limiting in NPM for /media/ location
4. **HTTPS only**: Ensure FORCE_SCRIPT_NAME and secure redirects are configured

## Summary

After following this guide:
- ✅ Media files are publicly accessible at `https://backend.hanna.co.zw/media/`
- ✅ Meta's servers can fetch product images
- ✅ Product sync will work with images
- ✅ Images are cached for 7 days for performance

For questions or issues, check the logs:
```bash
# Backend logs (product sync)
docker logs whatsappcrm_backend_app

# NPM logs (media serving)
docker exec whatsappcrm_npm tail -f /data/logs/media-error.log
```
