# Media Files Configuration for Docker Setup

## Current Setup Analysis

### Docker Compose Configuration
✅ **Volumes properly configured:**
- `mediafiles_volume` is a named Docker volume
- Backend mounts it at `/app/mediafiles/`
- All celery workers mount it at `/app/mediafiles/`
- NPM mounts it at `/srv/www/media/` (but NOT being used correctly)

### The Problem
You're using **Nginx Proxy Manager (NPM)** which:
1. Has its own web UI for configuration (port 81)
2. Does NOT use the `nginx_proxy/nginx.conf` file
3. Needs to be configured through its web interface

## Solution Options

### Option 1: Let Django Serve Media Files (Recommended for Now)

Since NPM proxies all requests to Django, just let Django handle media files:

**Configure NPM Web UI (http://your-server:81):**

1. Log into NPM admin (port 81)
2. Edit your backend proxy host (backend.hanna.co.zw)
3. In "Advanced" tab, add:
   ```nginx
   # Let Django serve media files - no special handling needed
   # All requests go to backend:8000
   ```
4. Save and test: https://backend.hanna.co.zw/media/test.txt

**This works because:**
- Django's `urls.py` already has `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)`
- Django will serve files from `/app/mediafiles/` automatically
- The volume ensures persistence across container restarts

### Option 2: NPM Serves Media Directly (Better Performance)

Configure NPM to serve media files directly without hitting Django:

**Configure NPM Web UI:**

1. Edit backend proxy host in NPM
2. In "Custom Locations" tab, add:
   - Location: `/media`
   - Scheme: `http`
   - Forward Hostname/IP: `backend`
   - Forward Port: `8000`
   - In "Advanced" tab for this location:
     ```nginx
     # Serve directly from volume instead of proxying
     root /srv/www;
     try_files $uri @backend;
     
     location @backend {
         proxy_pass http://backend:8000;
     }
     ```

**OR simpler - just proxy media to Django:**
   - Location: `/media/`
   - Forward to: `http://backend:8000/media/`
   - No custom config needed

### Option 3: Use Custom Nginx Container (Most Control)

Replace NPM with a custom nginx container that uses your `nginx.conf`:

**Update docker-compose.yml:**
```yaml
  nginx:
    image: nginx:alpine
    container_name: whatsappcrm_nginx
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx_proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - mediafiles_volume:/srv/www/media:ro
      - npm_letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

Then your `nginx.conf` would work as written.

## Recommended Quick Fix

**Just let Django serve the files** - it's already configured correctly!

1. Make sure Django's urls.py has:
   ```python
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

2. In NPM, proxy all `/media/` requests to Django:
   - No special configuration needed
   - NPM already forwards everything to `backend:8000`

3. Test:
   ```bash
   # Upload a file via Django admin or API
   # Then access: https://backend.hanna.co.zw/media/<filename>
   ```

## Testing

### Create Test File in Volume
```bash
# From host
docker-compose exec backend sh -c "echo 'Test media file from Docker' > /app/mediafiles/docker-test.txt"

# Test access
curl https://backend.hanna.co.zw/media/docker-test.txt
```

### Check Volume Contents
```bash
docker-compose exec backend ls -la /app/mediafiles/
```

### Check NPM Mount
```bash
docker-compose exec npm ls -la /srv/www/media/
```

They should show the same files (it's the same volume).

## Current Status

✅ **Docker volumes: Configured correctly**
✅ **Django settings: Configured to serve media**
✅ **URLs: Configured with static() helper**

❓ **NPM Configuration: Needs to be checked in web UI**

## Next Steps

1. Access NPM web UI: http://your-server:81
2. Check backend.hanna.co.zw proxy host configuration
3. Verify it's forwarding ALL requests (including /media/) to backend:8000
4. Test media file access
5. If not working, check NPM logs: `docker-compose logs npm`

## Why Media Might Not Be Working

Common issues:
1. NPM not forwarding `/media/` URLs to Django
2. Custom location in NPM that's blocking media requests
3. SSL certificate issues preventing HTTPS access
4. File permissions in volume (Django can't write)

Check NPM configuration first!
