# Certificate Directory Update

## Issue
Browser was showing SSL warnings despite valid certificates being issued by Let's Encrypt.

## Root Cause
Nginx was configured to use the wrong certificate directory:
- Old (incorrect): `/etc/letsencrypt/live/dashboard.hanna.co.zw/`
- This directory contained self-signed or invalid certificates

## Solution
Updated nginx configuration to use the correct certificate directory:
- New (correct): `/etc/letsencrypt/live/dashboard.hanna.co.zw-0001/`
- This directory contains valid Let's Encrypt certificates issued by E7
- These are production certificates (not staging)

## Changes Made
Updated all three SSL server blocks in `nginx_proxy/nginx.conf`:
1. Frontend (dashboard.hanna.co.zw)
2. Backend (backend.hanna.co.zw)
3. Management Frontend (hanna.co.zw)

All now point to: `/etc/letsencrypt/live/dashboard.hanna.co.zw-0001/`

## Applying Changes
After deploying these changes, the nginx container needs to reload the configuration:

```bash
# Option 1: Reload nginx configuration (no downtime)
docker-compose exec nginx nginx -s reload

# Option 2: Restart nginx container (brief downtime)
docker-compose restart nginx
```

## Verification
After applying changes, verify the certificates are being served correctly:

```bash
# Check which certificate nginx is serving
curl -vI https://dashboard.hanna.co.zw 2>&1 | grep -i "subject\|issuer"

# Run the certificate path checker
./check-certificate-paths.sh

# Run the fix script to verify configuration
./fix-certificate-directory.sh
```

## Expected Results
- ✓ No browser SSL warnings
- ✓ Valid Let's Encrypt certificate shown
- ✓ Certificate issued by Let's Encrypt E7
- ✓ All three domains using the same valid certificate
