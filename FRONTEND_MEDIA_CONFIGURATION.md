# Frontend Media Configuration Guide

## Overview

This guide explains how media files are now configured to be accessible through the frontend nginx service in addition to the backend.

## What Changed

### 1. Docker Compose Configuration

The frontend service now has the media files volume mounted:

```yaml
frontend:
  build: ./whatsapp-crm-frontend
  container_name: whatsappcrm_frontend_app
  volumes:
    - mediafiles_volume:/usr/share/nginx/html/media:ro  # Mount media files for serving (read-only)
  depends_on:
    - backend
  restart: unless-stopped
```

**Key points:**
- Volume is mounted at `/usr/share/nginx/html/media/` inside the frontend container
- `:ro` flag means read-only access for security
- Same `mediafiles_volume` shared with backend, celery workers, and npm

### 2. Frontend Nginx Configuration

The `whatsapp-crm-frontend/nginx.conf` now includes a dedicated location block for serving media files:

```nginx
location /media/ {
    alias /usr/share/nginx/html/media/;
    expires 7d;
    add_header Cache-Control "public, max-age=604800, immutable";
    add_header Access-Control-Allow-Origin "*" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Enable range requests for video/audio
    add_header Accept-Ranges bytes;
}
```

**Features:**
- Direct file serving from nginx (fast and efficient)
- 7-day cache expiration for better performance
- CORS headers enabled for cross-origin access
- Security headers to prevent MIME type sniffing
- Range request support for streaming media

## How It Works

### Request Flow

1. **Frontend Media Access:**
   - User/App requests: `https://dashboard.hanna.co.zw/media/product_images/item.png`
   - NPM forwards to frontend container (port 80)
   - Frontend nginx serves directly from `/usr/share/nginx/html/media/`
   - Fast response with caching headers

2. **Backend Media Access:**
   - User/App requests: `https://backend.hanna.co.zw/media/product_images/item.png`
   - NPM forwards to backend container (port 8000)
   - Can be served by Django or NPM depending on NPM configuration
   - See `NPM_MEDIA_CONFIGURATION.md` for NPM setup

### Volume Sharing

All services access the same files:

```
mediafiles_volume (Docker named volume)
├── backend → /app/mediafiles/        (read-write)
├── frontend → /usr/share/nginx/html/media/  (read-only)
├── npm → /srv/www/media/             (read-write)
├── celery_io_worker → /app/mediafiles/     (read-write)
├── celery_cpu_worker → /app/mediafiles/    (read-write)
├── celery_beat → /app/mediafiles/          (read-write)
└── email_idle_fetcher → /app/mediafiles/   (read-write)
```

## Testing

### 1. Rebuild and Restart Frontend

After making these changes, rebuild the frontend container:

```bash
# Rebuild frontend image with new nginx.conf
docker-compose build frontend

# Restart frontend service
docker-compose up -d frontend
```

### 2. Create Test File

```bash
# Create a test file in the media volume
docker-compose exec backend sh -c "echo 'Test media file from Docker' > /app/mediafiles/test-frontend.txt"

# Verify file exists in frontend container
docker-compose exec frontend ls -la /usr/share/nginx/html/media/
```

### 3. Test Access Through Frontend

```bash
# Test direct access to frontend container
docker-compose exec frontend cat /usr/share/nginx/html/media/test-frontend.txt

# Test via curl (if you have direct access to frontend)
curl http://localhost:80/media/test-frontend.txt

# Test via NPM proxy (actual production URL)
curl https://dashboard.hanna.co.zw/media/test-frontend.txt
```

### 4. Test Product Images

```bash
# List product images
docker-compose exec frontend ls -la /usr/share/nginx/html/media/product_images/

# Test accessing a product image
curl -I https://dashboard.hanna.co.zw/media/product_images/your-image.png
```

Expected response headers:
```
HTTP/2 200
content-type: image/png
cache-control: public, max-age=604800, immutable
access-control-allow-origin: *
x-content-type-options: nosniff
accept-ranges: bytes
```

## NPM Configuration for Frontend Media

If you want NPM to serve media files through the frontend nginx:

### Option 1: Proxy to Frontend (Recommended)

1. In NPM Admin UI (port 81)
2. Edit the `dashboard.hanna.co.zw` proxy host
3. Add a custom location:
   - **Location:** `/media`
   - **Scheme:** `http`
   - **Forward Hostname/IP:** `frontend`
   - **Forward Port:** `80`
   - **Custom Config:** (leave empty, frontend nginx will handle it)

### Option 2: Direct Serve from NPM

Keep the existing NPM configuration to serve directly from `/srv/www/media/` as documented in `NPM_MEDIA_CONFIGURATION.md`.

## Troubleshooting

### Issue: 404 Not Found for /media/ URLs

**Causes:**
1. Frontend container not rebuilt with new nginx.conf
2. Volume not mounted correctly
3. Files don't exist in the volume

**Solutions:**
```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Check volume mount
docker inspect whatsappcrm_frontend_app | grep -A 10 Mounts

# Verify files exist
docker-compose exec frontend ls -la /usr/share/nginx/html/media/
```

### Issue: 403 Forbidden

**Cause:** File permissions issue

**Solution:**
```bash
# Fix permissions (run in backend where files are created)
docker-compose exec backend chmod -R 755 /app/mediafiles/
```

### Issue: NPM not forwarding to frontend

**Cause:** NPM custom location configured to forward to backend instead of frontend

**Solution:**
1. Check NPM configuration for `dashboard.hanna.co.zw`
2. Ensure `/media` location forwards to `frontend:80` not `backend:8000`
3. Or remove custom location to let default proxy rules apply

### Issue: Changes not taking effect

**Solutions:**
```bash
# Full rebuild and restart
docker-compose down
docker-compose build frontend
docker-compose up -d

# Check nginx config inside container
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# Check nginx syntax
docker-compose exec frontend nginx -t

# Check nginx logs
docker-compose logs frontend
```

## Best Practices

### 1. Cache Control
- Media files are cached for 7 days
- Good for static product images
- If you need to update an image, use a new filename or clear CDN cache

### 2. Security
- Frontend has read-only access (`:ro` mount)
- Only backend can write files
- CORS enabled only for media files, not app routes

### 3. Performance
- Nginx serves files directly (faster than Django)
- Range requests enabled for streaming
- Consider adding Cloudflare or CDN for global distribution

### 4. Storage Management
```bash
# Check volume usage
docker system df -v

# Clean old unused volumes
docker volume prune

# Backup media files
docker run --rm -v mediafiles_volume:/data -v /backup:/backup alpine tar czf /backup/mediafiles-backup.tar.gz /data
```

## Integration with React App

Your React app can now access media files via:

```javascript
// Using relative URL (works because same domain)
const imageUrl = '/media/product_images/item.png';

// Using full URL
const imageUrl = `${window.location.origin}/media/product_images/item.png`;

// In your components
<img src="/media/product_images/item.png" alt="Product" />

// For API responses that include media URLs
const product = await fetch('/api/products/1');
// product.image_url = "/media/product_images/item.png"
<img src={product.image_url} alt={product.name} />
```

### CORS Considerations

The media location allows CORS (`Access-Control-Allow-Origin: *`), so you can:
- Load images from other origins
- Use in canvas elements
- Fetch with JavaScript without CORS issues

## Monitoring

### Check Media Access Logs

```bash
# Frontend nginx logs
docker-compose logs -f frontend | grep media

# NPM logs
docker-compose exec npm tail -f /data/logs/media-access.log

# Check for errors
docker-compose exec npm tail -f /data/logs/media-error.log
```

### Monitor Volume Usage

```bash
# Check volume size
docker system df -v | grep mediafiles_volume

# List largest files
docker-compose exec backend du -sh /app/mediafiles/*
```

## Summary

After these changes:
- ✅ Frontend can serve media files directly via nginx
- ✅ Media files accessible at `https://dashboard.hanna.co.zw/media/`
- ✅ Same volume shared across all services
- ✅ Optimized with caching and CORS
- ✅ Secure with read-only mount and security headers
- ✅ Performance optimized with nginx serving static files

For NPM-specific configuration to serve media via backend, see `NPM_MEDIA_CONFIGURATION.md`.
