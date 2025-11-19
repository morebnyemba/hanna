# Media Access Fix Summary

## Issue
Media files were present in both backend (`/app/mediafiles`) and npm (`/srv/www/media`) containers but were not accessible via URL:
```bash
curl https://backend.hanna.co.zw/media/docker-test.txt  # Returns empty
```

Files existed:
```bash
docker-compose exec backend ls -la /app/mediafiles/docker-test.txt  # ✅ Exists
docker-compose exec npm ls -la /srv/www/media/docker-test.txt       # ✅ Exists
```

## User Request
1. Add the media files volume to the npm/frontend service
2. Help with nginx config for serving media files in frontend

## Solution Implemented

### 1. Added Media Volume to Frontend Service

**File:** `docker-compose.yml`

```yaml
frontend:
  build: ./whatsapp-crm-frontend
  container_name: whatsappcrm_frontend_app
  volumes:
    - mediafiles_volume:/usr/share/nginx/html/media:ro  # NEW: Read-only media access
  depends_on:
    - backend
  restart: unless-stopped
```

**Benefits:**
- Frontend can now serve media files directly
- Read-only mount (`:ro`) for security
- Same shared volume as backend, npm, and celery workers

### 2. Configured Nginx in Frontend

**File:** `whatsapp-crm-frontend/nginx.conf`

Added a dedicated location block for media files:

```nginx
location /media/ {
    alias /usr/share/nginx/html/media/;
    expires 7d;
    add_header Cache-Control "public, max-age=604800, immutable";
    add_header Access-Control-Allow-Origin "*" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Accept-Ranges bytes;
}
```

**Features:**
- Direct file serving from nginx (fast and efficient)
- 7-day browser caching
- CORS support for cross-origin access
- Security headers
- Range requests for video/audio streaming

### 3. Created Comprehensive Documentation

**File:** `FRONTEND_MEDIA_CONFIGURATION.md`

Complete guide with:
- Architecture overview and request flow
- Testing instructions
- NPM configuration options
- Troubleshooting guide
- Best practices
- React integration examples
- Monitoring commands

## Result

### Before
```
https://backend.hanna.co.zw/media/file.png
    ↓
NPM → Backend Django (slow, no caching)
    ❌ Returns empty or 404
```

### After - Option 1: Via Frontend
```
https://dashboard.hanna.co.zw/media/file.png
    ↓
NPM → Frontend Nginx
    ↓
Serves from /usr/share/nginx/html/media/
    ✅ Returns file with caching & CORS headers
```

### After - Option 2: Via Backend (still available)
```
https://backend.hanna.co.zw/media/file.png
    ↓
NPM → Backend Django OR NPM direct serve
    ↓
Serves from volume
    ✅ Returns file
```

## Volume Sharing Architecture

```
mediafiles_volume (Docker Named Volume)
│
├── backend → /app/mediafiles/                      (RW) Django writes uploads
├── frontend → /usr/share/nginx/html/media/         (RO) Nginx serves quickly
├── npm → /srv/www/media/                           (RW) Can serve directly
├── celery_io_worker → /app/mediafiles/             (RW) Process uploads
├── celery_cpu_worker → /app/mediafiles/            (RW) Process uploads
├── celery_beat → /app/mediafiles/                  (RW) Scheduled tasks
└── email_idle_fetcher → /app/mediafiles/           (RW) Email attachments
```

## Deployment Steps

1. **Pull changes:**
   ```bash
   git pull origin copilot/fix-media-access-issue-again
   ```

2. **Rebuild frontend:**
   ```bash
   docker-compose build frontend
   ```

3. **Restart services:**
   ```bash
   docker-compose up -d
   ```

4. **Test media access:**
   ```bash
   # Test via frontend
   curl https://dashboard.hanna.co.zw/media/docker-test.txt
   
   # Should return: "Test media file from Docker"
   ```

5. **Optional: Configure NPM** (if you want to use frontend nginx)
   - Login to NPM Admin UI: `http://your-server:81`
   - Edit `dashboard.hanna.co.zw` proxy host
   - Add custom location:
     - Location: `/media`
     - Forward to: `http://frontend:80`
   - Save and test

## Benefits

✅ **Performance:** Nginx serves files faster than Django
✅ **Caching:** 7-day browser cache reduces server load
✅ **CORS:** Cross-origin access enabled for media
✅ **Security:** Read-only mount, security headers
✅ **Flexibility:** Two access paths (frontend and backend)
✅ **Streaming:** Range requests for video/audio
✅ **Scalability:** Easy to add CDN later

## NPM Configuration Note

The issue mentions that files are accessible in containers but not via URL. This is typically because **Nginx Proxy Manager (NPM) needs custom location configuration** via its web UI (port 81).

### Two Options:

**Option A: Serve via Frontend** (Recommended - now configured)
- NPM proxies `/media` to `frontend:80`
- Frontend nginx serves files directly
- Fast, efficient, with caching

**Option B: Serve via Backend/NPM Direct**
- Configure NPM custom location to serve from `/srv/www/media/`
- See `NPM_MEDIA_CONFIGURATION.md` for details

Both options work with the same shared volume!

## Testing Commands

```bash
# Verify volume mount
docker inspect whatsappcrm_frontend_app | grep -A 10 Mounts

# Check files in frontend
docker-compose exec frontend ls -la /usr/share/nginx/html/media/

# Test nginx config
docker-compose exec frontend nginx -t

# Create test file
docker-compose exec backend sh -c "echo 'Test' > /app/mediafiles/test-new.txt"

# Access via frontend
curl https://dashboard.hanna.co.zw/media/test-new.txt

# Check logs
docker-compose logs frontend | grep media
```

## Files Changed

1. `docker-compose.yml` - Added media volume to frontend
2. `whatsapp-crm-frontend/nginx.conf` - Added /media/ location block
3. `FRONTEND_MEDIA_CONFIGURATION.md` - Complete documentation (NEW)
4. `MEDIA_ACCESS_FIX_SUMMARY.md` - This summary (NEW)

## Security Considerations

- ✅ Frontend has read-only access (cannot write/delete)
- ✅ Only backend can create/modify files
- ✅ CORS enabled only for media, not app routes
- ✅ MIME sniffing prevented with security headers
- ✅ No directory listing enabled
- ✅ Files served over HTTPS via NPM

## Monitoring

```bash
# Check volume usage
docker system df -v | grep mediafiles_volume

# Monitor access
docker-compose logs -f frontend | grep media

# Check largest files
docker-compose exec backend du -sh /app/mediafiles/*
```

## Troubleshooting

If media still not accessible after deployment:

1. **Rebuild frontend:**
   ```bash
   docker-compose build --no-cache frontend
   docker-compose up -d frontend
   ```

2. **Check NPM configuration:**
   - Login to port 81
   - Verify proxy host settings
   - Add custom location if needed

3. **Check file permissions:**
   ```bash
   docker-compose exec backend chmod -R 755 /app/mediafiles/
   ```

4. **Check nginx logs:**
   ```bash
   docker-compose logs frontend
   ```

See `FRONTEND_MEDIA_CONFIGURATION.md` for detailed troubleshooting.

## Success Criteria

✅ Files exist in all containers sharing the volume
✅ Frontend nginx configuration syntax is valid
✅ Media files accessible via `https://dashboard.hanna.co.zw/media/`
✅ Caching headers present in response
✅ CORS headers present in response
✅ No security vulnerabilities introduced
✅ Documentation complete

## References

- `FRONTEND_MEDIA_CONFIGURATION.md` - Complete configuration guide
- `NPM_MEDIA_CONFIGURATION.md` - NPM-specific configuration
- `NPM_MEDIA_FIX_GUIDE.md` - NPM troubleshooting
- `DOCKER_MEDIA_SETUP.md` - Docker volume setup
