# Quick Fix: nginx Container Restart Loop Due to Missing SSL Certificates

## Problem

The nginx container is in a restart loop because it's configured to use SSL certificates that don't exist yet. This creates a chicken-and-egg problem:
- nginx needs to be running to complete the ACME challenge for Let's Encrypt
- But nginx won't start without the certificate files

## Quick Solution

Run the bootstrap script - it handles everything automatically:

```bash
./bootstrap-ssl.sh --email admin@example.com
```

This will:
1. Stop any running containers
2. Create temporary self-signed certificates
3. Start all services (nginx will now start successfully)
4. Obtain real Let's Encrypt certificates
5. Replace temporary certificates with real ones

## Alternative: Manual Fix

If you prefer to do it step by step:

### Step 1: Create temporary certificates
```bash
./init-ssl.sh
```

### Step 2: Start nginx
```bash
docker-compose up -d nginx
```

### Step 3: Get real certificates
```bash
./setup-ssl-certificates.sh --email admin@example.com
```

## Verification

After running the fix, verify everything is working:

```bash
# Check container status
docker-compose ps

# nginx should show "Up" not "Restarting"

# Run diagnostics
./diagnose-ssl.sh

# Test HTTPS access
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw
curl -I https://hanna.co.zw
```

## What Changed

### New Scripts

1. **`bootstrap-ssl.sh`** - Complete SSL setup from scratch
   - Handles the entire process automatically
   - Creates temp certificates, starts services, gets real certificates

2. **`init-ssl.sh`** - Initialize SSL with temporary certificates
   - Creates self-signed certificates
   - Allows nginx to start before obtaining real certificates

3. **Updated `setup-ssl-certificates.sh`**
   - Now automatically creates temporary certificates if needed
   - Can start nginx if it's not running
   - More intelligent error handling

4. **Updated `diagnose-ssl.sh`**
   - Detects restart loops
   - Provides specific fix instructions
   - More resilient when nginx is down

### How It Works

The solution uses a two-phase approach:

**Phase 1: Bootstrap**
- Generate temporary self-signed SSL certificates
- These certificates are not trusted by browsers but allow nginx to start
- nginx can now serve the ACME challenge endpoint

**Phase 2: Real Certificates**
- With nginx running, Let's Encrypt can verify domain ownership
- Real certificates are obtained via ACME HTTP-01 challenge
- Temporary certificates are replaced with real ones
- nginx is restarted to load the new certificates

## Technical Details

### Certificate Paths

All certificates are stored in the `npm_letsencrypt` Docker volume at:
```
/etc/letsencrypt/live/dashboard.hanna.co.zw/
  ├── fullchain.pem  (certificate)
  └── privkey.pem    (private key)
```

### Nginx Configuration

The nginx configuration in `nginx_proxy/nginx.conf` references certificates at:
```nginx
ssl_certificate /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem;
```

These paths must exist for nginx to start, which is why temporary certificates are necessary.

### ACME Challenge

Let's Encrypt validates domain ownership via HTTP-01 challenge:
1. Let's Encrypt sends a challenge file
2. Challenge file must be accessible at: `http://domain/.well-known/acme-challenge/{token}`
3. nginx serves files from `/var/www/letsencrypt/` directory
4. This directory is shared between nginx and certbot containers via `letsencrypt_webroot` volume

## Prevention

To avoid this issue in future deployments:

1. **Always use the bootstrap script for new deployments:**
   ```bash
   ./bootstrap-ssl.sh --email your-email@example.com
   ```

2. **For testing, use staging mode first:**
   ```bash
   ./bootstrap-ssl.sh --staging --email test@example.com
   ```

3. **Keep the temporary certificate fallback in place** - don't remove the init script or bootstrap script

## Common Errors and Solutions

### Error: "certbot container not found"
```bash
# Pull the certbot image first
docker-compose pull certbot
```

### Error: "DNS resolution failed"
```bash
# Verify DNS records point to your server
dig dashboard.hanna.co.zw +short

# Should return your server's IP address
```

### Error: "Port 80 not accessible"
```bash
# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Test accessibility from outside
curl http://your-server-ip/
```

### Error: "Rate limit exceeded"
```bash
# Use staging mode for testing
./bootstrap-ssl.sh --staging --email test@example.com

# Wait for rate limit to reset (1 week for production)
```

## Support

If you still have issues:

1. Run diagnostics:
   ```bash
   ./diagnose-ssl.sh
   ```

2. Check logs:
   ```bash
   docker-compose logs nginx
   docker-compose logs certbot
   ```

3. View full documentation:
   - `SSL_SETUP_GUIDE.md` - Complete SSL setup guide
   - `README_SSL.md` - Quick start guide
   - `DEPLOYMENT_INSTRUCTIONS.md` - General deployment

## Related Files

- `bootstrap-ssl.sh` - Complete bootstrap script (NEW)
- `init-ssl.sh` - Initialize with temp certificates (NEW)
- `setup-ssl-certificates.sh` - Get Let's Encrypt certificates (UPDATED)
- `diagnose-ssl.sh` - Diagnostic tool (UPDATED)
- `certbot-renew.sh` - Automatic renewal script
- `nginx_proxy/nginx.conf` - nginx configuration
- `docker-compose.yml` - Service definitions
