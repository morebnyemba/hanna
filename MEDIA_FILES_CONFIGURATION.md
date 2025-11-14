# Media Files Configuration for Meta Catalog Integration

## Overview

For products to sync successfully with Meta (Facebook) Product Catalog, product images must be publicly accessible via HTTPS. This document explains the media file configuration for the Hanna CRM application.

## Current Setup

### Docker Compose Configuration

The `docker-compose.yml` has been configured with a shared `mediafiles_volume` that is mounted across all backend services:

```yaml
volumes:
  mediafiles_volume:  # Shared volume for user-uploaded media files

services:
  backend:
    volumes:
      - mediafiles_volume:/app/mediafiles
  
  celery_io_worker:
    volumes:
      - mediafiles_volume:/app/mediafiles
  
  celery_cpu_worker:
    volumes:
      - mediafiles_volume:/app/mediafiles
  
  celery_beat:
    volumes:
      - mediafiles_volume:/app/mediafiles
  
  email_idle_fetcher:
    volumes:
      - mediafiles_volume:/app/mediafiles
```

### Django Configuration

**Settings (`whatsappcrm_backend/settings.py`):**
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'
```

**URLs (`whatsappcrm_backend/urls.py`):**
Media files are served by Django even in production mode since Nginx Proxy Manager proxies all requests to the backend.

### Nginx Proxy Manager (NPM) Setup

Since the application uses Nginx Proxy Manager (a web-based GUI tool), the media file serving is handled as follows:

1. **Current Approach**: Media requests to `https://backend.hanna.co.zw/media/*` are proxied to Django, which serves the files from the `mediafiles_volume`.

2. **Recommended Production Approach** (for better performance):
   - Configure NPM to serve media files directly without proxying to Django
   - Add a custom location in NPM's advanced configuration:

   ```nginx
   # In NPM Advanced tab for backend.hanna.co.zw proxy host:
   location /media/ {
       alias /app/mediafiles/;
       expires 7d;
       add_header Cache-Control "public";
   }
   ```

   Note: This requires NPM to have access to the mediafiles volume, which would need an update to the docker-compose.yml:

   ```yaml
   npm:
     image: 'jc21/nginx-proxy-manager:latest'
     volumes:
       - npm_data:/data
       - npm_letsencrypt:/etc/letsencrypt
       - mediafiles_volume:/app/mediafiles:ro  # Read-only access to media files
   ```

## Testing Media File Access

To verify that product images are accessible to Meta's servers:

1. **Upload a product image** via Django admin
2. **Check the image URL** in the Product model (e.g., `/media/product_images/image.png`)
3. **Test public accessibility**:
   ```bash
   curl -I https://backend.hanna.co.zw/media/product_images/image.png
   ```
   
   Expected response:
   ```
   HTTP/2 200
   content-type: image/png
   content-length: [size]
   ```

4. **Verify in browser**: Open `https://backend.hanna.co.zw/media/product_images/image.png` in a browser. The image should load without requiring authentication.

## Troubleshooting

### Issue: 404 Not Found for Media Files

**Possible causes:**
1. Media files are not being served by Django (check `urls.py`)
2. NPM is not proxying `/media/` requests to the backend
3. File doesn't exist in the mediafiles directory

**Solution:**
- Verify Django is serving media files by checking `urls.py`
- Check NPM proxy host configuration includes all paths (use `/` as the forward path)
- Verify file exists: `docker exec whatsappcrm_backend_app ls -la /app/mediafiles/product_images/`

### Issue: 403 Forbidden for Media Files

**Possible causes:**
1. File permissions are incorrect
2. ALLOWED_HOSTS doesn't include the domain
3. CORS or CSP headers are blocking the request

**Solution:**
- Check file permissions: `docker exec whatsappcrm_backend_app ls -la /app/mediafiles/`
- Ensure `backend.hanna.co.zw` is in ALLOWED_HOSTS
- Check CORS configuration in settings.py

### Issue: Meta API Rejects Product Creation (Image-Related Error)

**Possible causes:**
1. Image URL is not publicly accessible
2. Image URL uses HTTP instead of HTTPS
3. Meta's servers cannot reach the URL (firewall/VPN)

**Solution:**
1. Test image URL accessibility from external location (not from your network)
2. Verify HTTPS is working with valid SSL certificate
3. Check NPM SSL configuration and ensure certificate is valid

## Meta Catalog Requirements

For product images to work with Meta Catalog:

1. **Protocol**: Must use HTTPS
2. **Authentication**: No authentication required (publicly accessible)
3. **Content-Type**: Must return proper image Content-Type header (e.g., `image/jpeg`, `image/png`)
4. **Accessibility**: Must be reachable from Meta's servers (no firewall/VPN blocking)
5. **File Size**: Recommended max 8MB per image
6. **Format**: JPEG or PNG recommended

## Future Improvements

For better performance and scalability:

1. **Use a CDN**: Store media files on a CDN (e.g., AWS CloudFront, Cloudflare)
2. **Object Storage**: Use S3-compatible storage (e.g., AWS S3, MinIO, DigitalOcean Spaces)
3. **Django-storages**: Configure django-storages to automatically upload media files to cloud storage
4. **Nginx Direct Serving**: Configure NPM to serve media files directly (see recommended approach above)

## Related Files

- `docker-compose.yml`: Volume configuration
- `whatsappcrm_backend/whatsappcrm_backend/settings.py`: Django media settings
- `whatsappcrm_backend/whatsappcrm_backend/urls.py`: Media URL patterns
- `whatsappcrm_backend/meta_integration/catalog_service.py`: Meta Catalog API integration
- `whatsappcrm_backend/products_and_services/models.py`: Product and ProductImage models
