# Certificate Directory Path Fix

## Problem Summary

After obtaining SSL certificates from Let's Encrypt, browsers are showing security warnings. This occurs when nginx is configured to use a certificate directory that differs from where the actual certificates are located.

### Common Scenario

When certificates are obtained multiple times (e.g., using `--staging` flag for testing), Let's Encrypt creates numbered directories:

```
/etc/letsencrypt/live/
├── dashboard.hanna.co.zw/          # First certificate (might be expired or self-signed)
├── dashboard.hanna.co.zw-0001/     # Second certificate
├── dashboard.hanna.co.zw-0002/     # Third certificate
└── dashboard.hanna.co.zw-0003/     # Fourth certificate (latest, might be staging)
```

If nginx configuration points to `dashboard.hanna.co.zw` but the valid certificate is in `dashboard.hanna.co.zw-0003`, browsers will show security warnings because nginx is serving the old, expired, or self-signed certificate.

## Root Causes

1. **Multiple Certificate Attempts**: Running certificate setup scripts multiple times without proper cleanup
2. **Staging vs Production**: Testing with `--staging` flag creates new numbered directories
3. **Rate Limiting**: Hitting Let's Encrypt rate limits forces use of staging certificates
4. **Missing `--cert-name` Flag**: Not specifying explicit certificate name causes Let's Encrypt to auto-number

## Symptoms

- ✗ Browser shows "Your connection is not private"
- ✗ Certificate warnings about "unknown authority" or "expired certificate"
- ✗ SSL/TLS errors in browser console
- ✓ Certificates exist in `/etc/letsencrypt/live/`
- ✓ Nginx starts without errors
- ✓ Port 443 is accessible

## Solution

### Quick Fix (Automated)

Use the new improved fix script that handles this scenario:

```bash
./fix-certificate-directory.sh
```

This script will:
1. Detect all available certificate directories
2. Identify the best certificate to use (newest, valid, production)
3. Warn if certificates are staging certificates
4. Update nginx configuration to use the correct directory
5. Reload nginx with the updated configuration

### Manual Fix

If you prefer to fix it manually:

1. **List all certificate directories:**
   ```bash
   docker-compose exec certbot ls -la /etc/letsencrypt/live/
   ```

2. **Identify the correct certificate directory** (usually the one with the highest number or most recent timestamp)

3. **Update nginx configuration** (`nginx_proxy/nginx.conf`):
   ```nginx
   # Change from:
   ssl_certificate /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem;
   ssl_certificate_key /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem;
   
   # To:
   ssl_certificate /etc/letsencrypt/live/dashboard.hanna.co.zw-0003/fullchain.pem;
   ssl_certificate_key /etc/letsencrypt/live/dashboard.hanna.co.zw-0003/privkey.pem;
   ```

4. **Update ALL server blocks** (there are 3: dashboard, backend, hanna.co.zw)

5. **Test and reload nginx:**
   ```bash
   docker-compose exec nginx nginx -t
   docker-compose exec nginx nginx -s reload
   ```

### Proper Fix (Production Certificates)

If the latest certificate is a staging certificate (which causes browser warnings), the proper solution is to obtain production certificates:

1. **Clean up all existing certificates:**
   ```bash
   docker-compose stop nginx
   docker-compose run --rm --entrypoint sh certbot -c \
     'rm -rf /etc/letsencrypt/live/* /etc/letsencrypt/archive/* /etc/letsencrypt/renewal/*'
   ```

2. **Obtain fresh production certificates:**
   ```bash
   ./setup-ssl-certificates.sh --email your-email@example.com
   ```

3. **Verify nginx configuration points to the correct path:**
   ```bash
   docker-compose exec nginx grep ssl_certificate /etc/nginx/conf.d/default.conf
   ```

   Should show: `/etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem`

## Prevention

To avoid this issue in the future:

### 1. Always Use `--cert-name` Flag

When obtaining certificates, always specify the certificate name explicitly:

```bash
certbot certonly ... --cert-name dashboard.hanna.co.zw
```

This prevents Let's Encrypt from creating numbered directories.

### 2. Clean Up Before Re-issuing

If you need to obtain new certificates, clean up the old ones first:

```bash
docker-compose run --rm --entrypoint sh certbot -c \
  'rm -rf /etc/letsencrypt/live/dashboard.hanna.co.zw* /etc/letsencrypt/archive/dashboard.hanna.co.zw* /etc/letsencrypt/renewal/dashboard.hanna.co.zw*'
```

### 3. Avoid Staging in Production

Only use `--staging` flag for testing, never in production:

```bash
# Testing:
./setup-ssl-certificates.sh --email your-email@example.com --staging

# Production:
./setup-ssl-certificates.sh --email your-email@example.com
```

### 4. Monitor Rate Limits

Let's Encrypt has rate limits:
- **5 certificates** per exact domain set per week
- **50 certificates** per registered domain per week

If you hit the limit, you must wait or use staging certificates temporarily.

Check current rate limit status at: https://crt.sh (search for your domain)

## Technical Details

### Why Numbered Directories Exist

Let's Encrypt creates numbered directories (`-0001`, `-0002`, etc.) when:
- A certificate already exists and you request a new one without `--cert-name`
- The primary domain in the new certificate request differs from existing ones
- You use different domain orders in certificate requests

### Certificate Name Resolution

The certificate name (directory name) is determined by:
1. The `--cert-name` flag if provided
2. The first domain in the `-d` flag list
3. Auto-incrementing if the name already exists

### Updated Scripts

The following scripts have been updated to work without requiring openssl in the nginx container:

- ✓ `fix-certificate-directory.sh` (new) - Comprehensive fix for directory mismatches
- ✓ `fix-certificate-paths.sh` (updated) - Now uses certbot container for openssl
- ✓ `check-certificate-paths.sh` (updated) - Now uses certbot container for openssl
- ✓ `setup-ssl-certificates.sh` (updated) - Now uses certbot container for verification

### Why OpenSSL in Certbot Container?

The nginx container uses `nginx:1.25-alpine` which doesn't include openssl by default to keep the image small. The certbot container has openssl and can access the same certificate files via the shared `npm_letsencrypt` volume.

## Verification

After applying the fix, verify everything is working:

```bash
# 1. Check nginx is using correct certificate directory
docker-compose exec nginx grep ssl_certificate /etc/nginx/conf.d/default.conf

# 2. Verify certificate details
docker-compose exec certbot openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw-0003/fullchain.pem -noout -subject -issuer -dates

# 3. Test HTTPS endpoints
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw
curl -I https://hanna.co.zw

# 4. Check in browser (clear cache first!)
```

## Related Documentation

- [CERTIFICATE_DIRECTORY_FIX.md](./CERTIFICATE_DIRECTORY_FIX.md) - Original diagnosis
- [CERTIFICATE_ISSUE_RESOLUTION.md](./CERTIFICATE_ISSUE_RESOLUTION.md) - Resolution summary
- [QUICK_CERTIFICATE_FIX.md](./QUICK_CERTIFICATE_FIX.md) - Quick reference guide
- [SSL_BROWSER_WARNING_FIX.md](./SSL_BROWSER_WARNING_FIX.md) - Browser-specific fixes
- [SSL_SETUP_GUIDE.md](./SSL_SETUP_GUIDE.md) - Complete SSL setup guide

## Summary

The certificate directory mismatch occurs when nginx configuration points to an old certificate directory while newer certificates exist in numbered directories. This is fixed by either:
1. Updating nginx configuration to use the correct numbered directory, or
2. Cleaning up and obtaining fresh certificates with proper naming

The `fix-certificate-directory.sh` script automates this process and provides guidance on whether you should update the configuration or obtain new production certificates.
