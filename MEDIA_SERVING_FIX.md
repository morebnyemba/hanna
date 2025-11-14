# Media Serving Infrastructure Fix

## Problem
Product images are not accessible via the URLs sent to Meta's API, causing 400 errors when creating/updating products in the Meta Catalog.

## Root Cause
The current docker-compose configuration doesn't properly share media files between the Django backend and nginx proxy.

- **Backend** stores media at: `/app/mediafiles`
- **Nginx** expects media at: `/srv/www/media/`
- **No shared volume** exists between them

## Solution

### 1. Add Media Volume to docker-compose.yml

Add a named volume for media files:

```yaml
volumes:
  postgres_data:
  redis_data:
  staticfiles_volume:
  npm_data:
  npm_letsencrypt:
  media_files:  # ADD THIS LINE
```

### 2. Mount Media Volume in Backend Service

Update the backend service to use the media volume:

```yaml
backend:
  build: ./whatsappcrm_backend
  container_name: whatsappcrm_backend_app
  volumes:
    - ./whatsappcrm_backend:/app
    - staticfiles_volume:/app/staticfiles
    - media_files:/app/mediafiles  # ADD THIS LINE
  # ... rest of configuration
```

### 3. Add Custom Nginx Service (Alternative to NPM)

If using a custom nginx configuration instead of nginx-proxy-manager, add:

```yaml
nginx:
  image: nginx:alpine
  container_name: whatsappcrm_nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx_proxy/nginx.conf:/etc/nginx/nginx.conf:ro
    - media_files:/srv/www/media:ro  # Mount as read-only
    - staticfiles_volume:/srv/www/static:ro
    - npm_letsencrypt:/etc/letsencrypt:ro
  depends_on:
    - backend
  restart: unless-stopped
```

### 4. Verify Nginx Configuration

Ensure `nginx_proxy/nginx.conf` has the media location block:

```nginx
# Serve Django media files directly for better performance
location /media/ {
    alias /srv/www/media/;
    expires 7d;
    add_header Cache-Control "public";
}
```

## Testing

After making these changes:

1. Rebuild and restart containers:
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```

2. Upload a test image via Django admin

3. Verify the image is accessible:
   ```bash
   curl -I https://backend.hanna.co.zw/media/product_images/test.png
   ```

4. Try creating/updating a product with the image

## Alternative: Using nginx-proxy-manager

If you're using nginx-proxy-manager (NPM):

1. Add the media volume to the backend service (step 2 above)
2. Configure a Custom Location in NPM's UI:
   - Go to Proxy Hosts → Edit backend.hanna.co.zw
   - Add Custom Location: `/media/`
   - Forward to: `http://backend:8000/media/`
   - Or serve directly if NPM can access the volume

## Temporary Workaround

Until the infrastructure is fixed, you can:

1. Create products without images (omit ProductImage records)
2. Or use a publicly accessible placeholder image URL
3. The improved error logging will show exactly what Meta is rejecting

## Notes

- Media files MUST be publicly accessible for Meta's API to validate them
- HTTPS is required (which you already have via Let's Encrypt)
- Proper CORS and Content-Type headers should be set by nginx
