# NPM Media Files Fix Guide

## Issue Summary
Media files are present in both backend and npm containers but not accessible via HTTPS URL.

**Symptoms:**
- ✅ Files exist: `docker-compose exec backend ls -la /app/mediafiles/docker-test.txt`
- ✅ Files visible in NPM: `docker-compose exec npm ls -la /srv/www/media/docker-test.txt`
- ❌ URL returns empty: `curl https://backend.hanna.co.zw/media/docker-test.txt`

## Root Cause
**Nginx Proxy Manager (NPM)** requires custom location configuration via its web UI. Without this configuration, NPM proxies ALL requests (including `/media/`) to the Django backend, but the response might not reach the client properly.

## Solution: Configure NPM Custom Location

### Step 1: Access NPM Admin UI
1. Navigate to: `http://YOUR-SERVER-IP:81`
2. Login with your credentials

### Step 2: Configure Custom Location for Media Files

1. Go to **Hosts** → **Proxy Hosts**
2. Find and click on `backend.hanna.co.zw`
3. Click the **Custom Locations** tab
4. Click **Add Location**

Configure as follows:

**Define Location:**
```
/media
```
*Note: Use `/media` NOT `/media/` for proper matching*

**Scheme:**
```
http
```

**Forward Hostname / IP:**
```
localhost
```
*Or leave empty - we're serving directly from filesystem*

**Forward Port:**
```
80
```
*Leave empty if possible*

**Advanced Settings - Custom Nginx Configuration:**
```nginx
# Serve media files directly from the volume mounted at /srv/www/media
alias /srv/www/media/;

# Add trailing slash if missing
rewrite ^(/media)$ $1/ permanent;

# Cache media files for 7 days
expires 7d;
add_header Cache-Control "public, max-age=604800, immutable";

# CORS headers for cross-origin requests
add_header Access-Control-Allow-Origin "*" always;
add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS" always;
add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept" always;

# Security headers
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;

# Disable buffering for large files
proxy_buffering off;
proxy_request_buffering off;

# Enable range requests for video/audio
add_header Accept-Ranges bytes;

# Logging
access_log /data/logs/media-access.log;
error_log /data/logs/media-error.log warn;

# Disable logging for successful requests (optional)
# access_log off;

# Enable directory listing for debugging (REMOVE IN PRODUCTION)
# autoindex on;
# autoindex_exact_size off;
# autoindex_localtime on;
```

5. **Important**: Check the box for **Force SSL** if SSL is enabled
6. Click **Save**

### Step 3: Verify Configuration

```bash
# Test 1: Check file exists in NPM container
docker-compose exec npm ls -la /srv/www/media/docker-test.txt

# Test 2: Test direct access from inside NPM container
docker-compose exec npm cat /srv/www/media/docker-test.txt

# Test 3: Test from your server
curl -v https://backend.hanna.co.zw/media/docker-test.txt

# Test 4: Check NPM logs
docker-compose exec npm tail -f /data/logs/media-error.log
docker-compose exec npm tail -f /data/logs/media-access.log
```

Expected successful response:
```
HTTP/2 200 
content-type: text/plain
cache-control: public, max-age=604800, immutable
access-control-allow-origin: *
x-content-type-options: nosniff

Test media file from Docker
```

### Step 4: Restart NPM (if needed)

If changes don't take effect immediately:

```bash
docker-compose restart npm
```

## Troubleshooting

### Issue: Still getting empty response

**Possible causes:**
1. Custom location not saved properly in NPM
2. NPM needs restart after configuration change
3. Permissions issue on media files

**Solutions:**

1. **Check NPM container has access to media files:**
   ```bash
   docker-compose exec npm ls -la /srv/www/media/
   ```
   
2. **Verify volume mount:**
   ```bash
   docker inspect whatsappcrm_npm | grep -A 10 Mounts
   ```
   Should show: `/srv/www/media`

3. **Check file permissions:**
   ```bash
   docker-compose exec npm stat /srv/www/media/docker-test.txt
   ```
   Should be readable (permissions like `-rw-r--r--`)

4. **Verify NPM configuration:**
   ```bash
   docker-compose exec npm cat /data/nginx/proxy_host/*.conf | grep -A 20 "location /media"
   ```

### Issue: 404 Not Found

**Cause:** File path mismatch or location block not matching

**Solution:**
1. Verify the alias path is `/srv/www/media/` (with trailing slash)
2. Verify location is `/media` (without trailing slash)
3. Check if file actually exists in the container

### Issue: 403 Forbidden

**Cause:** Permission issues

**Solution:**
```bash
# Fix permissions in backend container (where files are created)
docker-compose exec backend chmod -R 755 /app/mediafiles/
docker-compose exec backend chown -R root:root /app/mediafiles/
```

### Issue: NPM doesn't apply custom config

**Cause:** Syntax error in custom config or NPM cache

**Solutions:**
1. Remove any syntax errors from the custom configuration
2. Try removing and re-adding the custom location
3. Restart NPM: `docker-compose restart npm`
4. Check NPM error logs: `docker logs whatsappcrm_npm`

## Alternative Solution: Use Custom Nginx

If NPM custom locations don't work, you can switch to a custom nginx container:

### Option A: Add custom nginx alongside NPM

Edit `docker-compose.yml`:

```yaml
services:
  nginx:
    image: nginx:alpine
    container_name: whatsappcrm_nginx_static
    ports:
      - "8080:80"
    volumes:
      - mediafiles_volume:/usr/share/nginx/html/media:ro
      - ./nginx_static.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - npm
    restart: unless-stopped
```

Create `nginx_static.conf`:
```nginx
server {
    listen 80;
    server_name _;
    
    location /media/ {
        alias /usr/share/nginx/html/media/;
        autoindex on;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

Then access files via: `http://YOUR-SERVER-IP:8080/media/docker-test.txt`

### Option B: Replace NPM with custom nginx

This requires more setup but gives you full control. See `nginx_proxy/nginx.conf` for reference.

## Verification Checklist

After configuration:

- [ ] Files exist in NPM container: `/srv/www/media/`
- [ ] NPM custom location configured for `/media`
- [ ] Custom nginx config includes `alias /srv/www/media/;`
- [ ] NPM restarted after configuration
- [ ] Test URL returns file content (not empty)
- [ ] HTTP response includes `Cache-Control` header
- [ ] HTTP response includes `Access-Control-Allow-Origin` header
- [ ] Product images accessible from external network
- [ ] Meta catalog sync working with images

## Testing Product Images

Once media serving works:

```bash
# 1. Upload a product image via Django admin
# 2. Note the image URL (e.g., /media/product_images/test.png)
# 3. Test external access
curl -I https://backend.hanna.co.zw/media/product_images/test.png

# 4. Check from external tool (like from Meta's servers would)
# Visit: https://reqbin.com/
# Enter: https://backend.hanna.co.zw/media/product_images/test.png
# Click "Send"
# Should get 200 OK and image data
```

## Summary

The key issue is that **NPM requires explicit custom location configuration** via its web UI. The configuration must:

1. Match location `/media` (without trailing slash)
2. Use `alias /srv/www/media/;` (with trailing slash)
3. Include proper headers for caching and CORS
4. Be saved and NPM restarted

Without this custom location, NPM proxies requests to Django, but the response doesn't reach the client properly due to proxy buffering or other NPM internal handling issues.
