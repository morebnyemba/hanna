# Migration from NPM to Custom Nginx

This guide explains how to migrate from Nginx Proxy Manager (NPM) to a custom nginx setup.

## Why Switch to Custom Nginx?

- **Simpler architecture:** Direct nginx configuration without web UI
- **Better control:** Full control over nginx configuration
- **Easier to version control:** Configuration in git
- **More efficient:** No NPM overhead
- **Better suited for Django:** Media files served by Django

## What Changed

### Before (NPM)
```
User → NPM :443
    ↓
├── dashboard.hanna.co.zw → frontend:80
└── backend.hanna.co.zw → backend:8000
```

### After (Custom Nginx)
```
User → Custom Nginx :443
    ↓
├── dashboard.hanna.co.zw → frontend:80 (React)
├── backend.hanna.co.zw → backend:8000 (Django serves /media/)
└── hanna.co.zw → hanna-management-frontend:3000 (Next.js)
```

## Configuration Changes

### 1. docker-compose.yml

**Removed:**
```yaml
npm:
  image: 'jc21/nginx-proxy-manager:latest'
  container_name: whatsappcrm_npm
  ports:
    - '80:80'
    - '443:443'
    - '81:81'  # Admin UI
  volumes:
    - npm_data:/data
    - npm_letsencrypt:/etc/letsencrypt
    - mediafiles_volume:/srv/www/media
```

**Added:**
```yaml
nginx:
  image: nginx:1.25-alpine
  container_name: whatsappcrm_nginx
  ports:
    - '80:80'
    - '443:443'
  volumes:
    - ./nginx_proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    - mediafiles_volume:/srv/www/media:ro
    - npm_letsencrypt:/etc/letsencrypt:ro
    - ./nginx_proxy/ssl_custom:/etc/nginx/ssl_custom:ro
```

### 2. nginx_proxy/nginx.conf

**Key Changes:**
- Added `management_frontend_server` upstream for Next.js app
- Added `hanna.co.zw` to HTTP redirect list
- Changed backend `/media/` from direct file serving to Django proxy
- Added new HTTPS server block for `hanna.co.zw`

**Backend Media Configuration:**
```nginx
# Before: Direct file serving
location /media/ {
    alias /srv/www/media/;
    expires 7d;
    add_header Cache-Control "public";
}

# After: Proxy to Django
location /media/ {
    proxy_pass http://backend_server;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $http_host;
    proxy_redirect off;
    proxy_buffering off;
}
```

## Migration Steps

### Step 1: Backup Current Configuration

```bash
# Backup NPM data
docker-compose exec npm tar czf /data/npm-backup.tar.gz /data/nginx /data/letsencrypt_certs

# Copy backup to host
docker cp whatsappcrm_npm:/data/npm-backup.tar.gz ./npm-backup.tar.gz

# Backup docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup
```

### Step 2: Pull the Changes

```bash
git pull origin copilot/fix-media-access-issue-again
```

### Step 3: Stop and Remove NPM

```bash
# Stop NPM service
docker-compose stop npm

# Remove NPM container
docker-compose rm -f npm

# Note: npm_data and npm_letsencrypt volumes are kept for SSL certificates
```

### Step 4: Verify SSL Certificates

```bash
# Check if certificates exist
docker volume inspect npm_letsencrypt

# List certificates
docker run --rm -v npm_letsencrypt:/certs alpine ls -la /certs/live/
```

If certificates don't exist, you'll need to:
1. Use self-signed certificates for testing
2. Or obtain new Let's Encrypt certificates

### Step 5: Start Custom Nginx

```bash
# Start all services with new nginx
docker-compose up -d

# Check nginx logs
docker-compose logs nginx

# Check if nginx is running
docker-compose ps nginx
```

### Step 6: Verify Configuration

```bash
# Test dashboard frontend
curl -k https://dashboard.hanna.co.zw

# Test backend API
curl -k https://backend.hanna.co.zw/api/

# Test media files (Django serves them)
curl -k https://backend.hanna.co.zw/media/docker-test.txt

# Test management frontend
curl -k https://hanna.co.zw
```

### Step 7: (Optional) Generate DH Parameters

For enhanced SSL security:

```bash
# Generate 2048-bit DH parameters (recommended)
docker-compose exec nginx sh -c "apk add openssl && openssl dhparam -out /etc/nginx/ssl_custom/ssl-dhparams.pem 2048"

# Or on host and copy to container
openssl dhparam -out nginx_proxy/ssl_custom/ssl-dhparams.pem 2048

# Uncomment in nginx_proxy/nginx.conf:
# ssl_dhparam /etc/nginx/ssl_custom/ssl-dhparams.pem;

# Restart nginx
docker-compose restart nginx
```

## Troubleshooting

### Issue: nginx fails to start with "host not found" error

**Cause:** Backend or frontend containers not running

**Solution:**
```bash
# Start all services
docker-compose up -d

# Check all containers are running
docker-compose ps
```

### Issue: SSL certificate not found

**Cause:** Certificates not in npm_letsencrypt volume

**Solution:**
```bash
# Option 1: Use existing certificates from NPM
docker volume inspect npm_letsencrypt

# Option 2: Generate self-signed certificates for testing
docker-compose exec nginx sh -c "apk add openssl && \
  mkdir -p /etc/letsencrypt/live/dashboard.hanna.co.zw && \
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem \
  -out /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem \
  -subj '/CN=dashboard.hanna.co.zw'"

# Option 3: Obtain new Let's Encrypt certificates
# See "Obtaining New SSL Certificates" section below
```

### Issue: 502 Bad Gateway

**Cause:** Upstream service not responding

**Solution:**
```bash
# Check backend is running
docker-compose ps backend

# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Issue: Media files return 404

**Cause:** Django not configured to serve media files

**Solution:**
Ensure Django's `urls.py` has:
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your patterns
]

# Serve media files in development and production
if settings.DEBUG or True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Obtaining New SSL Certificates

If you need new Let's Encrypt certificates:

### Option 1: Using Certbot Container

```bash
# Stop nginx temporarily
docker-compose stop nginx

# Run certbot
docker run -it --rm \
  -v npm_letsencrypt:/etc/letsencrypt \
  -v /var/www/letsencrypt:/var/www/letsencrypt \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  -d dashboard.hanna.co.zw \
  -d backend.hanna.co.zw \
  -d hanna.co.zw

# Start nginx
docker-compose start nginx
```

### Option 2: Using acme.sh

```bash
# Install acme.sh
curl https://get.acme.sh | sh

# Obtain certificates
~/.acme.sh/acme.sh --issue -d dashboard.hanna.co.zw -d backend.hanna.co.zw -d hanna.co.zw --webroot /var/www/letsencrypt

# Copy to docker volume
# (Manual process - copy certificates to npm_letsencrypt volume)
```

## Reverting to NPM

If you need to revert:

```bash
# Restore backup
cp docker-compose.yml.backup docker-compose.yml

# Stop custom nginx
docker-compose stop nginx
docker-compose rm -f nginx

# Start NPM
docker-compose up -d npm

# Restore NPM configuration from backup if needed
docker cp npm-backup.tar.gz whatsappcrm_npm:/data/
docker-compose exec npm tar xzf /data/npm-backup.tar.gz -C /
```

## Configuration Management

### Adding New Domains

Edit `nginx_proxy/nginx.conf`:

1. Add to HTTP redirect:
```nginx
server_name dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw new-domain.com ...;
```

2. Add new HTTPS server block:
```nginx
server {
    listen 443 ssl;
    server_name new-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem;
    
    include /etc/nginx/ssl_custom/options-ssl-nginx.conf;
    
    location / {
        proxy_pass http://your_upstream;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
    }
}
```

3. Reload nginx:
```bash
docker-compose exec nginx nginx -s reload
```

### Testing Configuration Changes

```bash
# Test nginx configuration without restarting
docker-compose exec nginx nginx -t

# If successful, reload
docker-compose exec nginx nginx -s reload
```

## Performance Considerations

### Caching

For better performance, you can add caching for Django responses:

```nginx
# Add to backend server block
location /api/ {
    proxy_pass http://backend_server;
    proxy_cache my_cache;
    proxy_cache_valid 200 1m;
    # ... other proxy settings
}
```

### Rate Limiting

Add rate limiting to protect against abuse:

```nginx
# Add to http context
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Use in location
location /api/ {
    limit_req zone=api_limit burst=20;
    proxy_pass http://backend_server;
}
```

## Monitoring

### Check nginx status

```bash
# View logs
docker-compose logs -f nginx

# Check processes
docker-compose exec nginx ps aux

# Check listening ports
docker-compose exec nginx netstat -tlnp
```

### Check SSL certificate expiry

```bash
# Check certificate
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -text -noout | grep "Not After"
```

## Summary

After migration:
- ✅ NPM removed, custom nginx in place
- ✅ Three domains configured: dashboard, backend, and hanna.co.zw
- ✅ Django serves its own media files
- ✅ SSL certificates reused from NPM
- ✅ Simplified configuration in version control
- ✅ No admin UI needed (edit nginx.conf directly)

For questions or issues, check:
- `docker-compose logs nginx` - Nginx logs
- `docker-compose logs backend` - Backend logs
- `nginx_proxy/nginx.conf` - Configuration file
- `nginx_proxy/ssl_custom/README.md` - SSL setup guide
