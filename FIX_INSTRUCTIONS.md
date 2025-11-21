# SSL Certificate Issue - Fix Instructions

## Your Current Issue

Based on your error output, your nginx container is stuck in a restart loop:

```
whatsappcrm_nginx    nginx:1.25-alpine    "/docker-entrypoint.…"   nginx    19 seconds ago   Restarting (1) 3 seconds ago
```

**Root Cause:** nginx is configured to use SSL certificates that don't exist yet, causing it to fail to start with exit code 1.

## Solution

I've created automated scripts to fix this issue. You have two options:

### Option 1: One-Command Fix (RECOMMENDED)

Run the bootstrap script which handles everything automatically:

```bash
cd ~/HANNA
./bootstrap-ssl.sh --email admin@example.com
```

Replace `admin@example.com` with your actual email address (required for Let's Encrypt notifications).

**What this does:**
1. Stops all containers (including the restarting nginx)
2. Creates temporary self-signed certificates
3. Starts all services (nginx will now start successfully)
4. Obtains real Let's Encrypt certificates for all domains
5. Replaces temporary certificates with real ones
6. Restarts nginx with trusted certificates

**Time:** 2-5 minutes

### Option 2: Step-by-Step Fix

If you prefer more control:

```bash
cd ~/HANNA

# Step 1: Create temporary certificates
./init-ssl.sh

# Step 2: Start nginx (it will work now with temp certificates)
docker-compose up -d nginx

# Step 3: Get real Let's Encrypt certificates
./setup-ssl-certificates.sh --email admin@example.com
```

**Time:** 3-7 minutes (includes manual verification between steps)

## Verification

After running either option, verify everything is working:

```bash
# Check all containers are running properly
docker-compose ps

# nginx should show "Up" not "Restarting"
# All other services should also show "Up"

# Run the diagnostic tool
./diagnose-ssl.sh

# Test your domains
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw
curl -I https://hanna.co.zw

# All should return HTTP 200 OK or similar
```

## What's Changed

### New Files Added:

1. **`bootstrap-ssl.sh`** - Complete automated SSL setup
2. **`init-ssl.sh`** - Creates temporary certificates
3. **`QUICK_FIX_SSL.md`** - Detailed explanation of the issue
4. **`SSL_FIX_VERIFICATION.md`** - Testing guide
5. **`FIX_INSTRUCTIONS.md`** - This file

### Updated Files:

1. **`setup-ssl-certificates.sh`** - Now handles bootstrap scenarios automatically
2. **`diagnose-ssl.sh`** - Better detection of restart loops
3. **`README_SSL.md`** - Updated with bootstrap method
4. **`SSL_SETUP_GUIDE.md`** - Enhanced troubleshooting

## Understanding the Fix

### The Problem (Chicken-and-Egg)

1. nginx needs SSL certificates to start
2. But SSL certificates require nginx to be running (for ACME challenge)
3. This creates a loop where neither can work

### The Solution (Two-Phase Approach)

**Phase 1: Temporary Certificates**
- Create self-signed certificates (browsers show warning, but server works)
- nginx can now start successfully
- ACME challenge endpoint is now accessible

**Phase 2: Real Certificates**
- Let's Encrypt verifies domain ownership via HTTP challenge
- Real trusted certificates obtained
- Temporary certificates replaced
- nginx restarted with trusted certificates

## Certificate Renewal

After the fix, certificates will automatically renew:
- The `certbot` container checks for renewal every 12 hours
- Certificates are renewed when they have less than 30 days remaining
- No manual intervention needed

To check renewal status:
```bash
docker-compose logs certbot
```

## Testing First (Optional but Recommended)

If you want to test without using up Let's Encrypt rate limits:

```bash
# Use staging server (certificates won't be trusted by browsers)
./bootstrap-ssl.sh --staging --email test@example.com

# If everything works, run again without --staging for real certificates
./bootstrap-ssl.sh --email admin@example.com
```

## Troubleshooting

### If bootstrap script fails:

1. **Check DNS records:**
   ```bash
   dig dashboard.hanna.co.zw +short
   dig backend.hanna.co.zw +short
   dig hanna.co.zw +short
   ```
   All should return `72.60.91.41` (your server IP from the error output)

2. **Check firewall:**
   ```bash
   sudo ufw status
   # Ports 80 and 443 should be allowed
   ```

3. **Check nginx logs:**
   ```bash
   docker-compose logs nginx
   ```

4. **Check certbot logs:**
   ```bash
   docker-compose logs certbot
   ```

5. **Run diagnostics:**
   ```bash
   ./diagnose-ssl.sh
   ```

### If you get "rate limit exceeded":

Use staging mode or wait for the rate limit to reset (1 week).

### If nginx still won't start after temp certificates:

```bash
# Check nginx configuration
docker-compose exec nginx nginx -t

# View nginx error logs
docker-compose logs --tail=50 nginx

# Verify temp certificates exist
docker-compose run --rm certbot ls -la /etc/letsencrypt/live/dashboard.hanna.co.zw/
```

## Need More Help?

1. Check the detailed guides:
   - `QUICK_FIX_SSL.md` - Comprehensive explanation
   - `SSL_SETUP_GUIDE.md` - Full setup guide
   - `README_SSL.md` - Quick reference

2. Run diagnostics:
   ```bash
   ./diagnose-ssl.sh
   ```

3. Check the verification guide:
   ```bash
   cat SSL_FIX_VERIFICATION.md
   ```

## Summary

**Before:** nginx in restart loop, domains inaccessible, no SSL certificates

**After:** All services running, domains accessible via HTTPS, auto-renewing certificates

**Command to run:**
```bash
./bootstrap-ssl.sh --email admin@example.com
```

That's it! This should resolve your issue completely.
