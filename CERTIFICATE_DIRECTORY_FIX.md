# Certificate Directory Issue - Diagnosis and Fix

## Problem Statement

Browser shows security warnings despite SSL certificates being successfully issued. This typically manifests as:
- "Your connection is not private" warning
- "Certificate issued by unknown authority"  
- "NET::ERR_CERT_AUTHORITY_INVALID"

## Root Causes

After investigating the nginx configuration and certificate setup, the most common causes are:

### 1. Using Staging Certificates (Most Common)

**Symptom:** Browser shows "Certificate issued by unknown authority"

**Cause:** Certificates were obtained using Let's Encrypt staging environment (`--staging` flag), which issues certificates not trusted by browsers. This is meant for testing only.

**How to check:**
```bash
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -noout -issuer
```

Look for "(STAGING)" in the issuer field.

**Fix:**
```bash
# Remove staging certificates
docker-compose down

# Obtain production certificates
./bootstrap-ssl.sh --email your-email@example.com
```

### 2. Incorrect Certificate Directory Name

**Symptom:** Nginx fails to find certificates or uses wrong certificate

**Cause:** Certificates were created with a different primary domain than expected. For example:
- Nginx expects: `/etc/letsencrypt/live/dashboard.hanna.co.zw/`
- But certificates are in: `/etc/letsencrypt/live/backend.hanna.co.zw/` or `/etc/letsencrypt/live/hanna.co.zw/`

This happens when certbot uses a different domain as the certificate name.

**How to check:**
```bash
# List certificate directories
docker-compose exec nginx ls -la /etc/letsencrypt/live/

# Check what nginx configuration expects
docker-compose exec nginx grep ssl_certificate /etc/nginx/conf.d/default.conf
```

**Fix:**
Use the automated fix script:
```bash
./fix-certificate-paths.sh
```

Or manually update `nginx_proxy/nginx.conf` to use the correct path.

### 3. Expired Certificates

**Symptom:** Browser shows "Certificate expired" or "ERR_CERT_DATE_INVALID"

**Cause:** Certificate has passed its 90-day validity period.

**How to check:**
```bash
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -noout -dates
```

**Fix:**
```bash
# Force certificate renewal
./setup-ssl-certificates.sh --email your-email@example.com

# Reload nginx
docker-compose exec nginx nginx -s reload
```

### 4. Nginx Not Reloaded After Certificate Update

**Symptom:** New certificates exist but nginx still serves old ones

**Cause:** Nginx caches certificates in memory and doesn't automatically reload them.

**How to check:**
```bash
# Check certificate file modification time
docker-compose exec nginx ls -l /etc/letsencrypt/live/dashboard.hanna.co.zw/

# Check when nginx was last restarted
docker-compose ps nginx
```

**Fix:**
```bash
# Reload nginx (graceful, no downtime)
docker-compose exec nginx nginx -s reload

# OR restart nginx (if reload doesn't work)
docker-compose restart nginx
```

### 5. Self-Signed Temporary Certificates Still in Use

**Symptom:** Browser shows self-signed certificate warning

**Cause:** Bootstrap process created temporary self-signed certificates, but real Let's Encrypt certificates were never obtained or failed to replace them.

**How to check:**
```bash
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -noout -issuer -subject
```

If issuer equals subject, it's self-signed.

**Fix:**
```bash
./setup-ssl-certificates.sh --email your-email@example.com
```

### 6. Incomplete Domain Coverage (SAN Certificate Issue)

**Symptom:** Some domains work, others show certificate errors

**Cause:** Certificate doesn't include all required domains in its Subject Alternative Names (SAN).

**How to check:**
```bash
# View domains covered by certificate
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -noout -text | grep -A1 "Subject Alternative Name"
```

Expected to see:
- dashboard.hanna.co.zw
- backend.hanna.co.zw
- hanna.co.zw

**Fix:**
```bash
# Obtain new certificate with all domains
docker-compose down
./bootstrap-ssl.sh --email your-email@example.com --domains "dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
```

## Nginx Configuration Verification

The current nginx configuration uses the same certificate for all three server blocks:

```nginx
# Frontend server block
server {
    listen 443 ssl;
    server_name dashboard.hanna.co.zw;
    ssl_certificate /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem;
    # ...
}

# Backend server block
server {
    listen 443 ssl;
    server_name backend.hanna.co.zw;
    ssl_certificate /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem;  # Same cert
    ssl_certificate_key /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem;
    # ...
}

# Management frontend server block
server {
    listen 443 ssl;
    server_name hanna.co.zw;
    ssl_certificate /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem;  # Same cert
    ssl_certificate_key /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem;
    # ...
}
```

**This is correct!** All three server blocks should use the same certificate because:
1. Let's Encrypt issues one multi-domain (SAN) certificate
2. The certificate covers all three domains
3. Using one certificate simplifies management

## Volume Configuration

The docker-compose.yml correctly mounts certificates:

```yaml
nginx:
  volumes:
    - npm_letsencrypt:/etc/letsencrypt:ro  # SSL certificates (read-only)
    - letsencrypt_webroot:/var/www/letsencrypt  # ACME challenge directory

certbot:
  volumes:
    - npm_letsencrypt:/etc/letsencrypt  # Same volume for certificate management
    - letsencrypt_webroot:/var/www/letsencrypt
```

**Note:** The volume name `npm_letsencrypt` is from the Nginx Proxy Manager migration and is kept for compatibility. This is fine and not an issue.

## Diagnostic Tools

Three diagnostic scripts are available:

### 1. check-certificate-paths.sh
Comprehensive check of certificate configuration:
```bash
./check-certificate-paths.sh
```

**Checks:**
- Container status
- Certificate file existence
- Certificate details (issuer, expiry, SAN domains)
- Nginx configuration paths
- Volume mounts
- Live HTTPS connectivity

### 2. diagnose-ssl.sh
General SSL diagnostics:
```bash
./diagnose-ssl.sh
```

**Checks:**
- Docker services status
- DNS resolution
- Certificate validity
- ACME challenge configuration
- Port accessibility

### 3. fix-certificate-paths.sh
Automated fix for certificate path mismatches:
```bash
./fix-certificate-paths.sh
```

**Actions:**
- Detects actual certificate location
- Verifies certificate coverage
- Updates nginx config if needed
- Reloads nginx

## Troubleshooting Workflow

Follow this step-by-step process to diagnose and fix certificate issues:

### Step 1: Run Diagnostic
```bash
./check-certificate-paths.sh
```

This will identify the specific issue.

### Step 2: Apply Appropriate Fix

Based on the diagnostic output:

**If using staging certificates:**
```bash
docker-compose down
./bootstrap-ssl.sh --email your-email@example.com
```

**If certificate path is wrong:**
```bash
./fix-certificate-paths.sh
```

**If certificate expired:**
```bash
./setup-ssl-certificates.sh --email your-email@example.com
docker-compose exec nginx nginx -s reload
```

**If nginx not reloaded:**
```bash
docker-compose exec nginx nginx -s reload
```

**If no certificates found:**
```bash
./bootstrap-ssl.sh --email your-email@example.com
```

### Step 3: Verify Fix

After applying the fix:

```bash
# Check certificate details
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -noout -text

# Test HTTPS
curl -v https://dashboard.hanna.co.zw 2>&1 | grep -E "(subject|issuer|expire)"

# Test in browser
# Visit: https://dashboard.hanna.co.zw
#        https://backend.hanna.co.zw
#        https://hanna.co.zw
```

### Step 4: Clear Browser Cache

If certificates are valid but browser still shows warnings:

1. **Chrome/Edge:**
   - Settings → Privacy and Security → Clear browsing data
   - Select "Cached images and files"
   - Click "Clear data"

2. **Firefox:**
   - Settings → Privacy & Security → Clear Data
   - Select "Cached Web Content"
   - Click "Clear"

3. **Alternative:**
   - Open private/incognito window
   - Try different browser

## Prevention and Maintenance

### Automatic Certificate Renewal

The certbot container automatically checks for renewals every 12 hours. Certificates are renewed when they have less than 30 days remaining.

**Note:** After renewal, nginx needs to be reloaded manually. Consider setting up a cron job:

```bash
# Add to server crontab
0 3 * * * cd /path/to/hanna && docker-compose exec nginx nginx -s reload
```

### Monitoring Certificate Expiration

Check certificate expiry regularly:

```bash
# View certificate details
docker-compose exec certbot certbot certificates

# Quick expiry check
docker-compose exec nginx openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -noout -dates
```

Set up monitoring to alert 30 days before expiration.

### Regular Verification

Run diagnostics periodically:

```bash
# Weekly or after any configuration changes
./check-certificate-paths.sh
```

## Common Mistakes to Avoid

1. **Don't use `--staging` for production** - Only use staging for testing
2. **Don't forget to reload nginx** after certificate updates
3. **Don't create separate certificates** for each domain - Use one SAN certificate
4. **Don't modify certificate files manually** - Let certbot manage them
5. **Don't ignore expiration warnings** - Renew certificates promptly

## Technical Details

### Certificate Structure

The Let's Encrypt certificate for this application:

- **Type:** Domain Validated (DV) with Subject Alternative Names (SAN)
- **Primary domain:** dashboard.hanna.co.zw
- **Additional domains:** backend.hanna.co.zw, hanna.co.zw
- **Validity:** 90 days
- **Algorithm:** RSA 2048-bit or ECDSA P-256
- **Issuer:** Let's Encrypt Authority R3

### File Locations

In nginx container:
- Certificate: `/etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem`
- Private key: `/etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem`
- Optional cert: `/etc/letsencrypt/live/dashboard.hanna.co.zw/cert.pem`
- Optional chain: `/etc/letsencrypt/live/dashboard.hanna.co.zw/chain.pem`

### Volume Persistence

Certificates are stored in Docker volume `npm_letsencrypt`:
- Survives container restarts
- Persists across docker-compose down (unless `-v` flag used)
- Shared between nginx and certbot containers

## Related Documentation

- [SSL_BROWSER_WARNING_FIX.md](./SSL_BROWSER_WARNING_FIX.md) - Detailed browser warning fixes
- [SSL_SETUP_GUIDE.md](./SSL_SETUP_GUIDE.md) - Complete SSL setup guide
- [SSL_BOOTSTRAP_FIX.md](./SSL_BOOTSTRAP_FIX.md) - Bootstrap script documentation
- [CUSTOM_NGINX_MIGRATION_GUIDE.md](./CUSTOM_NGINX_MIGRATION_GUIDE.md) - NPM to custom nginx migration

## Summary

The nginx configuration is **correct** - all three server blocks properly use the same SAN certificate from `/etc/letsencrypt/live/dashboard.hanna.co.zw/`.

Browser warnings after certificate issuance are typically caused by:
1. Using staging instead of production certificates (most common)
2. Certificate in wrong directory name
3. Expired certificates
4. Nginx not reloaded after certificate update

Use the provided diagnostic and fix scripts to identify and resolve the specific issue.
