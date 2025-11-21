# SSL Certificate Setup Issue - Fix Documentation

## Problem Description

When running `./bootstrap-ssl.sh` or `./setup-ssl-certificates.sh`, the following issues occur:
- nginx container enters a restart loop
- SSL certificates fail to be issued
- ACME challenge directory cannot be created
- Domains are not accessible

## Root Causes Identified

### 1. Read-Only ACME Challenge Directory
**Problem:** The `letsencrypt_webroot` volume was mounted as read-only (`:ro`) in the nginx container.

**Impact:** Let's Encrypt needs to write challenge files to `/var/www/letsencrypt/.well-known/acme-challenge/` during the HTTP-01 challenge validation. The read-only mount prevented this.

**Fix:** Removed the `:ro` flag from the volume mount in `docker-compose.yml`:
```yaml
# Before:
- letsencrypt_webroot:/var/www/letsencrypt:ro

# After:
- letsencrypt_webroot:/var/www/letsencrypt  # read-write needed for ACME challenges
```

### 2. Certbot Renewal Service Interfering with Initial Setup
**Problem:** The `certbot` container runs `certbot-renew.sh` as its entrypoint, which immediately starts checking for certificate renewals in a loop.

**Impact:** When running `docker-compose run --rm certbot certonly ...`, the script was trying to run within the context of the renewal service, causing confusion and blocking.

**Fix:** Updated the bootstrap and setup scripts to use `--entrypoint certbot` to override the renewal script:
```bash
# Before:
docker-compose run --rm certbot certonly --webroot ...

# After:
docker-compose run --rm --entrypoint certbot certbot certonly --webroot ...
```

### 3. Renewal Script Starts Too Early
**Problem:** The `certbot-renew.sh` script starts checking for renewals immediately when the container starts, before initial certificates are created.

**Impact:** This caused confusion and potential conflicts during initial setup.

**Fix:** Added a waiting period in `certbot-renew.sh` to check for existing certificates before starting the renewal loop:
```bash
# Wait for initial certificates to be created (up to 5 minutes)
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if certbot certificates 2>/dev/null | grep -q "Certificate Name"; then
        echo "$(date): Found existing certificates, starting renewal monitoring"
        break
    fi
    sleep 30
    WAIT_TIME=$((WAIT_TIME + 30))
done
```

## Solution Steps

### For Fresh Installation

If you're setting up SSL certificates for the first time:

1. **Stop all containers** (to start fresh):
   ```bash
   docker-compose down
   ```

2. **Run the bootstrap script**:
   ```bash
   ./bootstrap-ssl.sh --email your-email@example.com
   ```

   This will:
   - Create temporary self-signed certificates
   - Start all services including nginx
   - Obtain real Let's Encrypt certificates
   - Replace temporary certificates with real ones

3. **Verify the setup**:
   ```bash
   ./diagnose-ssl.sh
   ```

### For Existing Installation with Issues

If nginx is already in a restart loop or certificates are failing:

1. **Stop the problematic nginx container**:
   ```bash
   docker-compose stop nginx
   ```

2. **Pull the latest changes**:
   ```bash
   git pull origin main  # or your branch name
   ```

3. **Recreate containers with updated configuration**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Check if nginx started successfully**:
   ```bash
   docker-compose ps nginx
   ```

5. **If nginx is still failing**, run the bootstrap script:
   ```bash
   ./bootstrap-ssl.sh --email your-email@example.com
   ```

## Testing the Fix

### 1. Test ACME Challenge Directory
```bash
# Create a test file in the ACME challenge directory
docker-compose exec nginx sh -c 'echo "test" > /var/www/letsencrypt/.well-known/acme-challenge/test'

# Verify it's accessible via HTTP
curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test

# Clean up
docker-compose exec nginx rm /var/www/letsencrypt/.well-known/acme-challenge/test
```

### 2. Test Certificate Issuance (Staging)
For testing without hitting Let's Encrypt rate limits:
```bash
./bootstrap-ssl.sh --email your-email@example.com --staging
```

### 3. Verify Certificate Installation
```bash
# Check if certificates exist
docker-compose exec nginx ls -la /etc/letsencrypt/live/dashboard.hanna.co.zw/

# Check certificate details
docker-compose exec certbot certbot certificates

# Test HTTPS access
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw
curl -I https://hanna.co.zw
```

## Common Issues After Fix

### Issue: "Error response from daemon: Container is restarting"
**Cause:** nginx is still in a restart loop from previous failures.

**Solution:**
```bash
docker-compose stop nginx
docker-compose rm -f nginx
docker-compose up -d nginx
```

### Issue: "No certificates found after waiting"
**Cause:** Certificate issuance failed during bootstrap.

**Solution:**
1. Check DNS resolution: `dig dashboard.hanna.co.zw`
2. Check port 80 accessibility: `telnet your-server-ip 80`
3. Check nginx logs: `docker-compose logs nginx`
4. Try with staging: `./bootstrap-ssl.sh --email your-email@example.com --staging`

### Issue: "Permission denied" when creating ACME challenge files
**Cause:** Volume permissions issue.

**Solution:**
```bash
# Recreate the volume
docker-compose down -v
docker-compose up -d
```

## Verification Checklist

After applying the fix, verify:

- [ ] nginx container is running (not restarting): `docker-compose ps nginx`
- [ ] certbot container is running: `docker-compose ps certbot`
- [ ] ACME challenge directory is writable: `docker-compose exec nginx touch /var/www/letsencrypt/test && docker-compose exec nginx rm /var/www/letsencrypt/test`
- [ ] Certificates exist: `docker-compose exec certbot certbot certificates`
- [ ] Domains are accessible via HTTPS:
  - [ ] https://dashboard.hanna.co.zw
  - [ ] https://backend.hanna.co.zw
  - [ ] https://hanna.co.zw
- [ ] Certificate auto-renewal is configured: `docker-compose logs certbot | grep "renewal"`

## Files Changed

1. **docker-compose.yml**
   - Removed `:ro` flag from `letsencrypt_webroot` mount in nginx service

2. **certbot-renew.sh**
   - Added waiting logic for initial certificates

3. **bootstrap-ssl.sh**
   - Changed certbot invocation to use `--entrypoint certbot`

4. **setup-ssl-certificates.sh**
   - Changed certbot invocation to use `--entrypoint certbot`

5. **README_SSL.md**
   - Updated documentation to reflect recent fixes

## Support

If you still encounter issues after applying these fixes:

1. Run the diagnostic script: `./diagnose-ssl.sh`
2. Check nginx logs: `docker-compose logs --tail=50 nginx`
3. Check certbot logs: `docker-compose logs --tail=50 certbot`
4. Verify DNS: `dig dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw`
5. Test port accessibility:
   ```bash
   telnet your-server-ip 80
   telnet your-server-ip 443
   ```

## References

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [ACME Challenge Types](https://letsencrypt.org/docs/challenge-types/)
