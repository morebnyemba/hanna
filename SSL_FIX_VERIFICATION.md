# SSL Fix Verification Guide

This document provides steps to verify that the SSL certificate bootstrap fix works correctly.

## Problem Being Fixed

**Issue:** nginx container stuck in restart loop because SSL certificates don't exist
- nginx.conf references certificate files that haven't been created yet
- nginx fails to start with exit code 1
- Can't obtain certificates because nginx needs to be running for ACME challenge
- Classic chicken-and-egg problem

## Solution Overview

Three new/updated scripts that work together:

1. **`bootstrap-ssl.sh`** - Complete automated setup
2. **`init-ssl.sh`** - Create temporary certificates only
3. **`setup-ssl-certificates.sh`** - Updated to handle bootstrap scenarios

## Manual Verification Steps

### Test 1: Bootstrap Script (Fresh Installation)

Simulates a completely fresh installation with no certificates.

```bash
# Start from clean state
docker-compose down -v  # Warning: This removes volumes!

# Run bootstrap
./bootstrap-ssl.sh --email admin@example.com

# Expected: All steps should complete successfully
# - Temporary certificates created
# - All services start (nginx should be "Up")
# - Real certificates obtained
# - nginx restarted

# Verify
docker-compose ps  # nginx should show "Up", not "Restarting"
curl -I https://dashboard.hanna.co.zw  # Should return 200
./diagnose-ssl.sh  # Should show all checks passing
```

### Test 2: Bootstrap Script with Staging

Test with Let's Encrypt staging server (won't use up rate limits).

```bash
# Start from clean state
docker-compose down -v

# Run bootstrap with staging
./bootstrap-ssl.sh --staging --email test@example.com

# Expected: Same as Test 1 but certificates will be from staging CA
# Browsers will show "not trusted" but that's expected for staging

# Verify
docker-compose exec certbot certbot certificates
# Should show certificates from "(STAGING) Let's Encrypt"
```

### Test 3: Init Script Only

Test the init script in isolation.

```bash
# Start from clean state
docker-compose down -v

# Run init script
./init-ssl.sh

# Expected: 
# - Creates ACME challenge directory
# - Creates temporary self-signed certificates
# - Does NOT start nginx or other services

# Verify temp certs exist
docker-compose run --rm certbot ls -la /etc/letsencrypt/live/dashboard.hanna.co.zw/
# Should show privkey.pem and fullchain.pem

# Now start nginx
docker-compose up -d nginx

# Verify nginx starts
docker-compose ps nginx
# Should show "Up", not "Restarting"

# Check nginx serves temp certs (will show self-signed warning)
curl -k -I https://dashboard.hanna.co.zw
# Should return response (certificate will be untrusted)
```

### Test 4: Setup Script with Auto-Init

Test that setup script automatically creates temp certs if needed.

```bash
# Start from clean state
docker-compose down -v

# Try to run setup without init
./setup-ssl-certificates.sh --email admin@example.com

# Expected:
# - Script detects no certificates
# - Automatically creates temporary certificates
# - Starts nginx
# - Obtains real certificates
# - nginx restarted

# Verify
docker-compose ps nginx  # Should be "Up"
curl -I https://dashboard.hanna.co.zw  # Should return 200
```

### Test 5: Restart Loop Detection

Test that diagnostic script detects and provides guidance for restart loops.

```bash
# Start from clean state (no volumes to simulate missing certs)
docker-compose down -v

# Try to start nginx without certificates
docker-compose up -d nginx

# Wait a few seconds for restart loop to be evident
sleep 10

# Run diagnostic
./diagnose-ssl.sh

# Expected output should include:
# - "nginx container is in a restart loop"
# - Specific instructions to fix with init-ssl.sh
# - Cannot perform checks that require nginx to be running
```

### Test 6: Certificate Renewal Path

Verify existing setup doesn't break the renewal process.

```bash
# Assume you have working certificates already
# (from Test 1 or Test 4)

# Verify certbot container is running
docker-compose ps certbot  # Should be "Up"

# Check certbot can see the certificates
docker-compose exec certbot certbot certificates

# Manually trigger renewal (will only renew if < 30 days left)
docker-compose exec certbot certbot renew --webroot -w /var/www/letsencrypt --dry-run

# Expected: Renewal simulation should succeed
```

### Test 7: Documentation Accuracy

Verify documentation matches actual behavior.

```bash
# Check that README_SSL.md instructions work
cat README_SSL.md

# Try the "Quick Start" instructions
# They should match what bootstrap-ssl.sh does

# Check that QUICK_FIX_SSL.md instructions work
cat QUICK_FIX_SSL.md

# Try the troubleshooting steps
# They should resolve the issue
```

## Automated Verification Checklist

For each test scenario, verify:

- [ ] Scripts run without syntax errors
- [ ] Scripts provide clear output about what they're doing
- [ ] Error messages are helpful and actionable
- [ ] nginx starts successfully after script runs
- [ ] nginx stays running (not in restart loop)
- [ ] Certificates are created in correct location
- [ ] ACME challenge directory exists and is accessible
- [ ] HTTP redirects to HTTPS work
- [ ] HTTPS connections work (ignoring trust for self-signed)
- [ ] Diagnostic script provides accurate status
- [ ] Documentation matches actual behavior

## Expected Script Behaviors

### bootstrap-ssl.sh

**Input:** `--email`, optional `--staging`, optional `--domains`

**Steps:**
1. Checks prerequisites (docker, docker-compose)
2. Stops any running containers
3. Creates temporary certificates via certbot container
4. Starts all services
5. Waits for nginx to be healthy
6. Obtains real certificates from Let's Encrypt
7. Restarts nginx with new certificates
8. Displays success message with verification steps

**Success Criteria:**
- Exit code 0
- All docker-compose services showing "Up"
- Real certificates present in certbot container
- nginx responding to HTTPS requests

### init-ssl.sh

**Input:** None (uses defaults)

**Steps:**
1. Creates ACME challenge directory in volume
2. Checks if certificates already exist (skip if yes)
3. Creates temporary self-signed certificate
4. Does NOT start any services

**Success Criteria:**
- Exit code 0
- Certificate files created in /etc/letsencrypt/live/dashboard.hanna.co.zw/
- ACME directory exists at /var/www/letsencrypt/.well-known/acme-challenge/
- No services started

### setup-ssl-certificates.sh (updated)

**Input:** Optional `--email`, `--staging`, `--domains`

**Steps:**
1. Checks if nginx is running
2. If not running and no certs exist: creates temp certs
3. Starts nginx if needed
4. Creates ACME webroot directory
5. Runs certbot to obtain certificates
6. Restarts nginx with new certificates

**Success Criteria:**
- Exit code 0 on success
- Real certificates obtained and installed
- nginx running and responding to HTTPS

### diagnose-ssl.sh (updated)

**Input:** None

**Steps:**
1. Checks docker services status
2. Specifically detects "Restarting" state for nginx
3. Checks DNS resolution
4. Checks SSL certificates (if nginx is running)
5. Checks ACME challenge configuration
6. Tests nginx configuration (if running)
7. Tests port accessibility (if running)
8. Provides summary and recommendations

**Success Criteria:**
- Runs without errors regardless of system state
- Accurately reports nginx restart loop
- Provides specific fix instructions for detected issues
- Doesn't fail when nginx is down

## Common Issues to Test For

### Issue: Script fails due to missing docker-compose
```bash
# Simulate: rename docker-compose temporarily
# Expected: Script should show clear error message about missing docker-compose
```

### Issue: DNS not configured
```bash
# Can't simulate without changing actual DNS
# But scripts should detect and report this clearly
```

### Issue: Port 80 blocked
```bash
# Would need to modify firewall to test
# Scripts should detect and report when ACME challenge fails
```

### Issue: Let's Encrypt rate limit hit
```bash
# Use staging mode to avoid this during testing
./bootstrap-ssl.sh --staging --email test@example.com
```

## Performance Metrics

Expected execution times (approximate):

- `init-ssl.sh`: 5-10 seconds
- `bootstrap-ssl.sh`: 2-5 minutes (depends on Let's Encrypt response)
- `setup-ssl-certificates.sh`: 1-3 minutes
- `diagnose-ssl.sh`: 10-30 seconds

## Security Considerations

Things to verify:

- [ ] Temporary certificates are replaced, not kept permanently
- [ ] Private keys have appropriate permissions
- [ ] Scripts don't log sensitive information
- [ ] Scripts don't expose email or domain info unnecessarily
- [ ] Temporary certificates expire in 1 day (as configured)

## Integration Testing

After deployment to production:

```bash
# 1. Run bootstrap
./bootstrap-ssl.sh --email your-production-email@example.com

# 2. Verify all domains
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw
curl -I https://hanna.co.zw

# 3. Check certificate details
openssl s_client -connect dashboard.hanna.co.zw:443 -servername dashboard.hanna.co.zw < /dev/null 2>/dev/null | openssl x509 -noout -text

# 4. Verify auto-renewal is set up
docker-compose logs certbot

# 5. Test renewal process
docker-compose exec certbot certbot renew --dry-run
```

## Rollback Procedure

If something goes wrong:

```bash
# 1. Stop all services
docker-compose down

# 2. Remove certificate volumes if needed
docker volume rm hanna_npm_letsencrypt
docker volume rm hanna_letsencrypt_webroot

# 3. Start with original method (if there was one)
# Or start fresh with new bootstrap script

# 4. Check logs for errors
docker-compose logs nginx
docker-compose logs certbot
```

## Success Indicators

The fix is successful if:

1. ✅ nginx starts successfully on fresh installation
2. ✅ nginx never enters restart loop due to missing certificates
3. ✅ SSL certificates are obtained automatically
4. ✅ Scripts provide clear progress and error messages
5. ✅ Documentation accurately describes the process
6. ✅ Diagnostic tool correctly identifies issues
7. ✅ All domains are accessible via HTTPS
8. ✅ Certificate renewal works automatically

## Failure Indicators

The fix has issues if:

1. ❌ nginx still enters restart loop
2. ❌ Scripts fail with unclear error messages
3. ❌ Temporary certificates are not created
4. ❌ Real certificates cannot be obtained
5. ❌ ACME challenge fails
6. ❌ nginx won't restart after certificate installation
7. ❌ Diagnostic tool gives wrong guidance

## Post-Fix Monitoring

After deploying the fix, monitor:

```bash
# Check nginx is stable
watch -n 5 'docker-compose ps nginx'

# Monitor certbot renewal attempts
docker-compose logs -f certbot

# Check certificate expiry regularly
docker-compose exec certbot certbot certificates

# Ensure no restart loops
docker-compose ps | grep Restarting
```

## Documentation Verification

Ensure these files are updated and accurate:

- [ ] README_SSL.md - Quick start guide updated
- [ ] SSL_SETUP_GUIDE.md - Comprehensive guide updated
- [ ] QUICK_FIX_SSL.md - Created and accurate
- [ ] SSL_FIX_VERIFICATION.md - This file is complete
- [ ] Scripts have help messages (--help flag)
- [ ] Error messages are helpful

## Notes for Production Use

**Before running in production:**

1. Verify DNS records are correct
2. Ensure firewall allows ports 80 and 443
3. Use real email address for Let's Encrypt notifications
4. Test with `--staging` flag first
5. Backup existing certificates if any
6. Plan for downtime during bootstrap
7. Have rollback plan ready

**Production deployment command:**

```bash
./bootstrap-ssl.sh --email your-production-email@company.com
```

**DO NOT use staging flag in production unless testing!**
