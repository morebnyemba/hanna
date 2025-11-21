# How to Fix Certificate Directory Issues - Simple Guide

## Problem
Browser shows certificate warnings even though certificates were issued successfully.

## Quick Diagnosis

Run this command first to see what's wrong:

```bash
./check-certificate-paths.sh
```

Look for these key indicators:

### 1. Certificate Directory Mismatch
```
Current nginx config points to: dashboard.hanna.co.zw
But certificates are in: dashboard.hanna.co.zw-0003
```

**Fix:** Run `./fix-certificate-directory.sh`

### 2. Staging Certificate Warning
```
⚠ Using STAGING certificate
```

**Fix:** Get production certificates (see below)

### 3. OpenSSL Not Available
```
OCI runtime exec failed: exec: "openssl": executable file not found
```

**Fix:** Scripts now automatically use certbot container instead

## The Fix

### Option 1: Automated Fix (Recommended)

Simply run:

```bash
./fix-certificate-directory.sh
```

The script will:
1. ✓ Find all certificate directories
2. ✓ Identify the best certificate to use
3. ✓ Warn you if it's a staging certificate
4. ✓ Update nginx configuration if needed
5. ✓ Reload nginx

**If the script finds staging certificates**, it will recommend getting production certificates instead.

### Option 2: Get Fresh Production Certificates

If you're using staging certificates or want to start fresh:

```bash
# 1. Stop nginx
docker-compose stop nginx

# 2. Clean up old certificates
docker-compose run --rm --entrypoint sh certbot -c \
  'rm -rf /etc/letsencrypt/live/* /etc/letsencrypt/archive/* /etc/letsencrypt/renewal/*'

# 3. Get new production certificates
./setup-ssl-certificates.sh --email your-email@example.com

# 4. Start nginx (happens automatically in step 3)
```

**Note:** Let's Encrypt allows 5 certificates per domain set per week. If you've hit this limit, wait or use staging temporarily.

## Verify the Fix

After running the fix:

### 1. Check nginx is using correct certificate
```bash
docker-compose exec nginx grep ssl_certificate /etc/nginx/conf.d/default.conf
```

Should show a valid path like `/etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem` or `/etc/letsencrypt/live/dashboard.hanna.co.zw-0003/fullchain.pem`

### 2. Verify certificate details
```bash
docker-compose exec certbot openssl x509 \
  -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem \
  -noout -subject -issuer
```

Should show:
- Subject: `CN = dashboard.hanna.co.zw`
- Issuer: `CN = R3, O = Let's Encrypt` (NOT "Staging")

### 3. Test in browser
Clear browser cache, then visit:
- https://dashboard.hanna.co.zw
- https://backend.hanna.co.zw
- https://hanna.co.zw

Click the padlock icon to verify the certificate is from "Let's Encrypt" (not "Staging")

## Common Questions

### Q: Why do I have numbered directories (dashboard.hanna.co.zw-0001, -0002, etc.)?

**A:** This happens when you run certificate setup multiple times. Let's Encrypt creates new numbered directories to avoid overwriting existing certificates.

### Q: Why does the script say "openssl not available"?

**A:** The nginx container uses Alpine Linux which doesn't include openssl by default. The updated scripts now use the certbot container which has openssl.

### Q: What's the difference between staging and production certificates?

**A:** 
- **Staging**: Test certificates, NOT trusted by browsers, causes warnings
- **Production**: Real certificates, trusted by all browsers

Always use production for live sites. Only use staging for testing.

### Q: Can I just delete the numbered directories?

**A:** Yes, but it's safer to let the script handle it. If you want to manually clean up:

```bash
# See what directories exist
docker-compose exec certbot ls -la /etc/letsencrypt/live/

# Delete specific numbered directory (be careful!)
docker-compose run --rm --entrypoint sh certbot -c \
  'rm -rf /etc/letsencrypt/live/dashboard.hanna.co.zw-0002'
```

### Q: What if I hit Let's Encrypt rate limits?

**A:** Let's Encrypt limits:
- 5 certificates per exact domain set per week
- 50 certificates per registered domain per week

If you hit the limit:
1. Wait for the limit to reset (1 week)
2. Use staging certificates temporarily
3. Check your certificate history at https://crt.sh

### Q: How do I know which certificate directory to use?

**A:** Use `./fix-certificate-directory.sh` - it automatically:
1. Finds all certificate directories
2. Checks which are valid vs expired
3. Identifies staging vs production
4. Picks the best one
5. Warns you about any issues

## Still Having Problems?

### 1. Collect diagnostics
```bash
./check-certificate-paths.sh > diagnostics.txt
docker-compose logs nginx > nginx-logs.txt
docker-compose logs certbot > certbot-logs.txt
```

### 2. Check container status
```bash
docker-compose ps
```

All containers should show "Up"

### 3. Check nginx logs for errors
```bash
docker-compose logs nginx | tail -50
```

### 4. Restart services
```bash
docker-compose restart nginx
```

### 5. Read detailed documentation
- [CERTIFICATE_DIRECTORY_PATH_FIX.md](CERTIFICATE_DIRECTORY_PATH_FIX.md) - Detailed technical explanation
- [SSL_BROWSER_WARNING_FIX.md](SSL_BROWSER_WARNING_FIX.md) - Browser-specific fixes

## Summary

**The simplest solution:**

```bash
# Diagnose the issue
./check-certificate-paths.sh

# Fix it automatically
./fix-certificate-directory.sh

# If staging certificates found, get production ones
./setup-ssl-certificates.sh --email your-email@example.com
```

That's it! The scripts handle all the complexity for you.
