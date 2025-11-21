# SSL Certificate Bootstrap Fix

## Problem Summary

The SSL certificate bootstrap process was failing with the following issues:

1. **nginx container in restart loop** - When trying to obtain SSL certificates, nginx would enter a restart loop, preventing the certificate acquisition process from completing.

2. **"live directory exists" error** - Certbot would fail with an error message stating that the live directory already exists for the domain, preventing it from replacing temporary certificates with real ones.

3. **Permission issues** - The ACME challenge directory (`/var/www/letsencrypt`) had incorrect permissions, preventing Let's Encrypt from validating domain ownership.

## Root Cause

The issue occurred in the SSL bootstrap workflow:

1. The `bootstrap-ssl.sh` script creates temporary self-signed certificates in `/etc/letsencrypt/live/dashboard.hanna.co.zw/`
2. Nginx starts successfully with these temporary certificates
3. When attempting to obtain real Let's Encrypt certificates, certbot detects the existing "live" directory
4. Without the `--force-renewal` flag, certbot refuses to replace the existing certificates
5. The bootstrap process fails, leaving the system with only temporary self-signed certificates

## Solution Implemented

### 1. Added `--cert-name` Parameter (Latest Fix)

Updated both `bootstrap-ssl.sh` and `setup-ssl-certificates.sh` to use the `--cert-name` parameter with certbot. This explicitly tells certbot which certificate to replace, preventing the "live directory exists" error.

**Previous approach (had issues):**
```bash
CERTBOT_CMD="certonly --webroot -w /var/www/letsencrypt --email $EMAIL --agree-tos --no-eff-email --force-renewal --expand"
```

**Current approach (fixed):**
```bash
CERTBOT_CMD="certonly --webroot -w /var/www/letsencrypt --email $EMAIL --agree-tos --no-eff-email --force-renewal --cert-name $FIRST_DOMAIN"
```

The key change is replacing `--expand` with `--cert-name $FIRST_DOMAIN`. This:
- Explicitly specifies the certificate name to use
- Prevents the "live directory exists" error even when temporary certificates exist
- Works seamlessly with `--force-renewal` to replace existing certificates

### 2. Improved Directory Permissions

Updated all scripts (`bootstrap-ssl.sh`, `setup-ssl-certificates.sh`, and `init-ssl.sh`) to set proper permissions on the ACME challenge directory and certificate files:

```bash
# Set proper permissions for ACME challenge directory
chmod -R 755 /var/www/letsencrypt

# Ensure certificate files have proper permissions
chmod 644 $CERT_DIR/fullchain.pem
chmod 600 $CERT_DIR/privkey.pem
```

### 3. Enhanced Nginx Startup Checks

Added retry logic to handle transient nginx restart issues during startup:

```bash
NGINX_RETRIES=0
MAX_NGINX_RETRIES=12  # 12 retries * 5 seconds = 60 seconds max wait
while [ $NGINX_RETRIES -lt $MAX_NGINX_RETRIES ]; do
    if docker-compose ps nginx | grep -q "Up"; then
        echo "✓ nginx is running"
        break
    elif docker-compose ps nginx | grep -q "Restarting"; then
        echo "⚠ nginx is restarting (attempt $((NGINX_RETRIES + 1))/$MAX_NGINX_RETRIES)..."
        sleep 5
        NGINX_RETRIES=$((NGINX_RETRIES + 1))
    else
        # Handle error...
    fi
done
```

### 4. Improved Certificate Detection in Renewal Script

Updated `certbot-renew.sh` to better distinguish between temporary self-signed certificates and real Let's Encrypt certificates, increasing the wait time to 10 minutes to allow for slower networks.

## How to Apply the Fix

If you're experiencing SSL certificate issues, follow these steps:

### Option 1: Fresh Start (Recommended)

1. **Stop all containers and remove volumes:**
   ```bash
   docker-compose down -v
   ```

2. **Run the bootstrap script with your email:**
   ```bash
   ./bootstrap-ssl.sh --email your-email@example.com
   ```

3. **Wait for the process to complete.** The script will:
   - Create temporary self-signed certificates
   - Start all services including nginx
   - Obtain real Let's Encrypt certificates (replacing the temporary ones)
   - Restart nginx with the real certificates

### Option 2: If Containers Are Already Running

1. **Just run the bootstrap script:**
   ```bash
   ./bootstrap-ssl.sh --email your-email@example.com
   ```

   The script will handle stopping and restarting services as needed.

### Option 3: Manual Certificate Acquisition

If you prefer manual control:

1. **Ensure nginx is running:**
   ```bash
   docker-compose up -d nginx
   ```

2. **Run the setup script:**
   ```bash
   ./setup-ssl-certificates.sh --email your-email@example.com
   ```

## Testing with Staging Server

To test the SSL setup without hitting Let's Encrypt rate limits, use the staging server:

```bash
./bootstrap-ssl.sh --email your-email@example.com --staging
```

**Note:** Staging certificates will show browser warnings but allow you to verify the process works.

## Verification

After running the bootstrap script, verify your SSL setup:

1. **Check certificate status:**
   ```bash
   docker-compose exec certbot certbot certificates
   ```

2. **Run diagnostics:**
   ```bash
   ./diagnose-ssl.sh
   ```

3. **Visit your domains in a browser:**
   - https://dashboard.hanna.co.zw
   - https://backend.hanna.co.zw
   - https://hanna.co.zw

4. **Check nginx logs if issues persist:**
   ```bash
   docker-compose logs nginx
   ```

## Common Issues and Solutions

### Issue: nginx still in restart loop

**Cause:** Certificate files might be corrupted or missing.

**Solution:**
```bash
docker-compose down -v
./bootstrap-ssl.sh --email your-email@example.com
```

### Issue: "live directory exists" error persists

**Cause:** Old version of the scripts without `--force-renewal` flag.

**Solution:** Ensure you're using the updated scripts (check that the certbot command includes `--force-renewal`).

### Issue: ACME challenge fails

**Causes:**
- DNS records not pointing to the server
- Firewall blocking port 80
- nginx not properly serving the ACME challenge directory

**Solution:**
```bash
# Check DNS
dig dashboard.hanna.co.zw

# Test ACME challenge directory accessibility
curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test

# Check nginx logs
docker-compose logs nginx
```

## Files Modified

- `bootstrap-ssl.sh` - Added `--cert-name` parameter, replaced `--expand` flag
- `setup-ssl-certificates.sh` - Added `--cert-name` parameter, replaced `--expand` flag
- `init-ssl.sh` - Improved permissions for ACME directory and certificates (no changes in latest fix)
- `certbot-renew.sh` - Better certificate detection, longer wait time (no changes in latest fix)

## Technical Details

### Why `--force-renewal`?

The `--force-renewal` flag tells certbot to obtain a new certificate even if one already exists. This is essential when replacing temporary self-signed certificates with real Let's Encrypt certificates during the bootstrap process.

### Why `--cert-name` instead of `--expand`?

The `--cert-name` parameter explicitly specifies the certificate name to use. This is crucial because:

1. **Prevents "live directory exists" error**: When certbot finds an existing certificate directory (even if it contains temporary self-signed certificates), it needs explicit instruction on what to do. The `--cert-name` parameter tells certbot to use and replace that specific certificate.

2. **Works with `--force-renewal`**: Together, these flags instruct certbot to:
   - Find the certificate named `dashboard.hanna.co.zw` (via `--cert-name`)
   - Replace it regardless of expiry date (via `--force-renewal`)
   - Use the new list of domains provided with `-d` flags

3. **Simpler than `--expand`**: The `--expand` flag was designed for adding domains to existing certificates, but it doesn't handle the case where the existing certificate was created outside certbot's normal flow. The `--cert-name` approach is more direct and reliable.

### Directory Permissions

- `/var/www/letsencrypt`: 755 (read + execute for all, write for owner)
- `fullchain.pem`: 644 (read for all, write for owner)
- `privkey.pem`: 600 (read + write for owner only)

These permissions ensure:
- Let's Encrypt can write ACME challenge files
- Nginx can read the challenge files and certificates
- Private keys are protected from unauthorized access

## Support

If you continue experiencing issues:

1. Check the [SSL_SETUP_GUIDE.md](./SSL_SETUP_GUIDE.md) for comprehensive documentation
2. Run the diagnostic tool: `./diagnose-ssl.sh`
3. Review logs: `docker-compose logs nginx` and `docker-compose logs certbot`
4. Open an issue with the output of the diagnostic tool
