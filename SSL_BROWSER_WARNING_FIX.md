# SSL Browser Warning Fix Guide

## Problem

After successfully obtaining SSL certificates using `bootstrap-ssl.sh`, the browser still shows security warnings when accessing the domains. This guide explains why this happens and how to fix it.

## Common Causes of Browser SSL Warnings

### 1. Staging Certificates (Most Common)

**Symptom:** Browser shows "Not Secure" or "Certificate issued by unknown authority"

**Cause:** The `--staging` flag was used when obtaining certificates. Let's Encrypt staging certificates are for testing only and are not trusted by browsers.

**Fix:**
```bash
# Remove all containers and volumes to clean up
docker-compose down -v

# Obtain production certificates (without --staging)
./bootstrap-ssl.sh --email your-email@example.com
```

**How to Check:**
```bash
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -noout -issuer

# Production certificate will show:
# issuer=C = US, O = Let's Encrypt, CN = R3

# Staging certificate will show:
# issuer=C = US, O = (STAGING) Let's Encrypt, CN = (STAGING) ...
```

### 2. Self-Signed Certificates

**Symptom:** Browser shows "Self-signed certificate" warning

**Cause:** The temporary self-signed certificates created during initialization were not replaced with real Let's Encrypt certificates.

**Fix:**
```bash
# Obtain real certificates
./setup-ssl-certificates.sh --email your-email@example.com
```

### 3. Expired Certificates

**Symptom:** Browser shows "Certificate expired"

**Cause:** Certificate has passed its expiration date.

**Fix:**
```bash
# Force renewal of certificates
docker-compose down
./bootstrap-ssl.sh --email your-email@example.com
```

### 4. Nginx Not Reloaded

**Symptom:** Certificates are valid but browser still shows old/invalid certificate

**Cause:** Nginx hasn't reloaded the new certificates after they were obtained.

**Fix:**
```bash
# Reload nginx to load new certificates
docker-compose exec nginx nginx -s reload

# Or restart nginx completely
docker-compose restart nginx
```

### 5. Browser Cache Issues

**Symptom:** Everything checks out but browser still shows warnings

**Cause:** Browser has cached the old certificate or HSTS settings.

**Fix:**
- **Chrome:** Settings → Privacy and Security → Clear browsing data → Cached images and files
- **Firefox:** Settings → Privacy & Security → Clear Data → Cached Web Content
- **Alternative:** Try accessing in a private/incognito window or different browser

### 6. Domain Mismatch

**Symptom:** Browser shows "Certificate name mismatch"

**Cause:** Accessing the site via an IP address or domain not covered by the certificate.

**Fix:**
- Always use one of these domains:
  - `https://dashboard.hanna.co.zw`
  - `https://backend.hanna.co.zw`
  - `https://hanna.co.zw`
- Don't access via IP address or localhost

### 7. Incomplete Certificate Chain

**Symptom:** Browser shows "Unable to verify certificate issuer"

**Cause:** Let's Encrypt's intermediate certificates are missing.

**Note:** This should not happen with Let's Encrypt, as they provide the full chain automatically. If you see this, it indicates a deeper issue.

**Fix:**
```bash
docker-compose down -v
./bootstrap-ssl.sh --email your-email@example.com
```

### 8. OCSP Issues

**Symptom:** Certificate validation takes a long time or fails

**Cause:** OCSP (Online Certificate Status Protocol) requests are failing.

**Fix:** The nginx configuration has been updated to include proper DNS resolvers for OCSP. If you're using an old configuration:

```bash
# Update nginx configuration
git pull origin main

# Restart nginx
docker-compose restart nginx
```

## Quick Troubleshooting Steps

### Step 1: Run the Troubleshooting Script

```bash
./troubleshoot-ssl-warnings.sh
```

This script will automatically check for common issues and provide specific fix instructions.

### Step 2: Verify Certificate Details

```bash
# Check certificate issuer and expiration
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -noout -issuer -dates -subject

# Expected output for valid certificate:
# issuer=C = US, O = Let's Encrypt, CN = R3
# notBefore=...
# notAfter=... (should be in the future)
# subject=CN = dashboard.hanna.co.zw
```

### Step 3: Check Certbot Managed Certificates

```bash
docker-compose exec certbot certbot certificates

# Should show:
# Certificate Name: dashboard.hanna.co.zw
#   Domains: dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw
#   Expiry Date: ...
#   Certificate Path: /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem
```

### Step 4: Test HTTPS Connection

```bash
# Test from command line (should succeed without warnings)
curl -v https://dashboard.hanna.co.zw

# Or test with openssl
openssl s_client -connect dashboard.hanna.co.zw:443 -servername dashboard.hanna.co.zw
```

### Step 5: Check Nginx Configuration

```bash
# Verify nginx configuration is valid
docker-compose exec nginx nginx -t

# Check if nginx is using the correct certificate paths
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf | grep ssl_certificate
```

## Complete Fix Procedure

If you're still experiencing issues after trying the above steps, follow this complete reset procedure:

### 1. Clean Slate Approach

```bash
# Stop all services and remove volumes
docker-compose down -v

# Verify no old containers are running
docker ps -a | grep hanna

# Remove any old SSL files if needed
# (Only if you have access to the host's Docker volumes)
```

### 2. Fresh Certificate Setup

```bash
# Run bootstrap script with your email
./bootstrap-ssl.sh --email your-email@example.com

# Wait for it to complete (may take 5-10 minutes)
```

### 3. Verify the Setup

```bash
# Run diagnostics
./diagnose-ssl.sh

# Check specific issues
./troubleshoot-ssl-warnings.sh
```

### 4. Test in Browser

1. Clear browser cache completely
2. Close and reopen browser
3. Visit `https://dashboard.hanna.co.zw`
4. Check the certificate by clicking the padlock icon

Expected result:
- Padlock icon shows secure connection
- Certificate issued by "R3" (Let's Encrypt)
- Valid until approximately 90 days from issuance

## Prevention

### Automatic Certificate Renewal

The `certbot` container automatically checks for certificate renewals every 12 hours. Certificates are renewed when they have less than 30 days remaining.

**Note:** Currently, nginx needs to be manually reloaded after renewal. We recommend setting up a cron job:

```bash
# Add to crontab (run every day at 3 AM)
0 3 * * * cd /path/to/hanna && docker-compose exec nginx nginx -s reload
```

### Monitoring Certificate Expiration

Set up monitoring to alert you before certificates expire:

```bash
# Check expiration date
docker-compose exec certbot certbot certificates

# Add to monitoring system or set up a reminder 30 days before expiration
```

## Changes Made to Fix Browser Warnings

### 1. Updated Nginx Configuration

- Added external DNS resolvers (8.8.8.8, 8.8.4.4, 1.1.1.1) for OCSP stapling
- Ensures OCSP requests can reach Let's Encrypt's OCSP responders

**File:** `nginx_proxy/nginx.conf`

```nginx
# DNS Resolvers Configuration
resolver 127.0.0.11 8.8.8.8 8.8.4.4 1.1.1.1 valid=30s ipv6=off;
resolver_timeout 5s;
```

### 2. Improved Certificate Reload

- Changed from `docker-compose restart nginx` to `nginx -s reload`
- Graceful reload without dropping active connections
- Falls back to full restart if graceful reload fails

**Files:** `bootstrap-ssl.sh`, `setup-ssl-certificates.sh`

### 3. Enhanced Certificate Verification

- Added automatic detection of certificate type (production vs staging vs self-signed)
- Provides specific warnings and fix instructions for each case
- Verifies certificate issuer after obtaining certificates

**Files:** `bootstrap-ssl.sh`, `setup-ssl-certificates.sh`

### 4. New Troubleshooting Script

- Created dedicated script to diagnose SSL browser warnings
- Automatically detects common issues
- Provides specific fix instructions for each problem

**File:** `troubleshoot-ssl-warnings.sh`

### 5. Updated Certbot Renewal Script

- Added note about manual nginx reload after renewal
- Improved logging for renewal events

**File:** `certbot-renew.sh`

## Technical Details

### Why Browser Warnings Occur

1. **Certificate Chain Verification:** Browsers verify that a certificate is signed by a trusted Certificate Authority (CA). Staging or self-signed certificates don't have this chain of trust.

2. **OCSP Stapling:** Browsers check if a certificate has been revoked using OCSP. If nginx can't reach OCSP servers (due to DNS issues), browsers may show warnings.

3. **Certificate Caching:** Browsers cache certificates and HSTS policies. Old cached data can cause warnings even after fixing the issue.

4. **Domain Validation:** Browsers ensure the certificate's CN (Common Name) or SAN (Subject Alternative Name) matches the domain being accessed.

### Let's Encrypt Certificate Details

- **Issuer:** Let's Encrypt Authority X3 or R3
- **Validity:** 90 days
- **Renewal:** Recommended at 30 days before expiry
- **Type:** Domain Validated (DV)
- **Algorithm:** RSA 2048-bit or ECDSA P-256

### OCSP Stapling Benefits

- Improves SSL/TLS performance
- Enhances privacy (browser doesn't contact OCSP server directly)
- Reduces load on Let's Encrypt's OCSP responders

## Getting Help

If you're still experiencing issues:

1. Run diagnostics: `./diagnose-ssl.sh`
2. Run troubleshooting: `./troubleshoot-ssl-warnings.sh`
3. Check nginx logs: `docker-compose logs nginx`
4. Check certbot logs: `docker-compose logs certbot`
5. Open an issue with the output of the above commands

## Related Documentation

- [SSL_SETUP_GUIDE.md](./SSL_SETUP_GUIDE.md) - Complete SSL setup guide
- [SSL_BOOTSTRAP_FIX.md](./SSL_BOOTSTRAP_FIX.md) - Bootstrap script fixes
- [README_SSL.md](./README_SSL.md) - SSL configuration overview
