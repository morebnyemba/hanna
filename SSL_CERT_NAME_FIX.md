# SSL Certificate "live directory exists" Fix

## Problem
When running the SSL bootstrap scripts, certbot fails with the error:
```
live directory exists for dashboard.hanna.co.zw
```

This prevents the system from obtaining real Let's Encrypt certificates, leaving it with only temporary self-signed certificates.

## Root Cause
The bootstrap process:
1. Creates temporary self-signed certificates in `/etc/letsencrypt/live/dashboard.hanna.co.zw/`
2. Starts nginx with these certificates
3. Attempts to obtain real Let's Encrypt certificates
4. **Fails** because certbot sees the existing "live" directory

Even with the `--force-renewal` flag, certbot couldn't proceed because it didn't know which certificate to replace.

## Solution
The fix is simple but crucial: add the `--cert-name` parameter to explicitly tell certbot which certificate to replace.

### Before (failed):
```bash
CERTBOT_CMD="certonly --webroot -w /var/www/letsencrypt \
  --email $EMAIL --agree-tos --no-eff-email \
  --force-renewal --expand"
```

### After (works):
```bash
CERTBOT_CMD="certonly --webroot -w /var/www/letsencrypt \
  --email $EMAIL --agree-tos --no-eff-email \
  --force-renewal --cert-name $FIRST_DOMAIN"
```

## Why This Works

1. **`--cert-name $FIRST_DOMAIN`**: Explicitly tells certbot to use/replace the certificate named "dashboard.hanna.co.zw"
2. **`--force-renewal`**: Forces replacement even if the certificate isn't near expiry
3. **Multiple `-d` flags**: Specifies all domains to include in the certificate

Together, these tell certbot:
- "Find the certificate named dashboard.hanna.co.zw"
- "Replace it with a new one"
- "Include all these domains in the new certificate"

This works even when the existing certificate was created outside certbot (like our self-signed temporary certificates).

## Files Changed
- `bootstrap-ssl.sh` - Line 216
- `setup-ssl-certificates.sh` - Line 165
- `SSL_BOOTSTRAP_FIX.md` - Documentation update

## How to Apply This Fix

If you're experiencing the "live directory exists" error:

1. **Pull the latest code:**
   ```bash
   git pull origin main
   ```

2. **Clean up old certificates:**
   ```bash
   docker-compose down -v
   ```
   
   ⚠️ **Warning**: This removes all volumes including certificates. Only do this if you're setting up fresh SSL certificates.

3. **Run the bootstrap script:**
   ```bash
   ./bootstrap-ssl.sh --email your-email@example.com
   ```

4. **Wait for completion:**
   The script will:
   - Create temporary certificates
   - Start all services
   - **Successfully** obtain real Let's Encrypt certificates
   - Restart nginx with real certificates

## Verification

After running the script, verify your setup:

```bash
# Check certificate status
docker-compose exec certbot certbot certificates

# Run diagnostics
./diagnose-ssl.sh

# Test in browser
# Visit: https://dashboard.hanna.co.zw
```

## Example Command Output

With the fix, the certbot command will be:
```bash
certbot certonly --webroot -w /var/www/letsencrypt \
  --email admin@example.com \
  --agree-tos --no-eff-email \
  --force-renewal \
  --cert-name dashboard.hanna.co.zw \
  -d dashboard.hanna.co.zw \
  -d backend.hanna.co.zw \
  -d hanna.co.zw
```

You should see output like:
```
Requesting a certificate for dashboard.hanna.co.zw and 2 more domains

Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem
This certificate expires on 2026-02-19.
```

## Technical Notes

### Why not `--expand`?
The `--expand` flag is designed for adding domains to existing certificates managed by certbot. It doesn't handle cases where:
- The certificate directory exists but wasn't created by certbot
- The certificate is self-signed or otherwise "unmanaged"

### Why `--cert-name` is better?
The `--cert-name` parameter:
- Works with both new and existing certificates
- Handles certificates created outside certbot
- Provides explicit control over which certificate to replace
- Is more reliable and predictable

## Troubleshooting

If you still have issues after applying this fix:

1. **Check DNS records:**
   ```bash
   dig dashboard.hanna.co.zw
   ```
   Should point to your server's IP.

2. **Check port 80 accessibility:**
   ```bash
   curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test
   ```

3. **Check nginx logs:**
   ```bash
   docker-compose logs nginx
   ```

4. **Try staging first:**
   ```bash
   ./bootstrap-ssl.sh --email your-email@example.com --staging
   ```

## Related Documentation
- [SSL_BOOTSTRAP_FIX.md](./SSL_BOOTSTRAP_FIX.md) - Comprehensive SSL bootstrap documentation
- [SSL_SETUP_GUIDE.md](./SSL_SETUP_GUIDE.md) - General SSL setup guide
- [README_SSL.md](./README_SSL.md) - SSL overview
