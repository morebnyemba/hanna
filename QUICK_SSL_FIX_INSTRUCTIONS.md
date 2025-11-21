# Quick SSL Certificate Fix - Instructions

## What Was Fixed

Three critical issues preventing SSL certificate setup have been fixed:

1. ✅ **ACME Challenge Directory** - Changed from read-only to read-write in docker-compose.yml
2. ✅ **Certbot Invocation** - Fixed bootstrap and setup scripts to avoid renewal service interference  
3. ✅ **Renewal Service** - Added wait logic to prevent conflicts during initial setup

## How to Apply the Fix

### Option 1: Fresh Start (Recommended)

If you're experiencing nginx restart loops or certificate issues:

```bash
# Pull the latest changes
git pull

# Stop all containers and remove volumes (CAUTION: This will reset your setup)
docker-compose down -v

# Run the bootstrap script with your email
./bootstrap-ssl.sh --email your-email@example.com

# Verify the setup
./diagnose-ssl.sh
```

### Option 2: Update Without Downtime

If your services are currently running and you want minimal disruption:

```bash
# Pull the latest changes
git pull

# Recreate only the nginx and certbot containers
docker-compose up -d --force-recreate nginx certbot

# Wait a few minutes for the certbot renewal service to stabilize
sleep 120

# Obtain real certificates (if you don't have them yet)
./setup-ssl-certificates.sh --email your-email@example.com

# Restart nginx to load the certificates
docker-compose restart nginx
```

### Option 3: Testing with Staging (Safe)

To test without hitting Let's Encrypt rate limits:

```bash
# Pull the latest changes
git pull

# Stop all containers
docker-compose down -v

# Run bootstrap with staging flag
./bootstrap-ssl.sh --email your-email@example.com --staging

# Verify (certificates won't be trusted by browsers, but the process should work)
./diagnose-ssl.sh
```

## What to Expect

After applying the fix and running the bootstrap script:

1. **Temporary certificates created** - Self-signed certs allow nginx to start
2. **All services start** - nginx, backend, frontend, certbot, etc.
3. **Real certificates obtained** - Let's Encrypt issues production certificates
4. **nginx restarted** - Loads the real certificates
5. **Domains accessible** - https://dashboard.hanna.co.zw, https://backend.hanna.co.zw, https://hanna.co.zw

## Verification Steps

After applying the fix:

```bash
# 1. Check all containers are running
docker-compose ps

# 2. Verify nginx is NOT restarting
docker-compose ps nginx | grep -v "Restarting"

# 3. Check if certificates exist
docker-compose exec certbot certbot certificates

# 4. Run diagnostic script
./diagnose-ssl.sh

# 5. Test HTTPS access
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw  
curl -I https://hanna.co.zw
```

## Common Questions

### Q: Will this fix work if nginx is in a restart loop?
**A:** Yes! The bootstrap script creates temporary certificates first, allowing nginx to start.

### Q: Do I need to delete existing volumes?
**A:** Only if you want a completely fresh start. The fix works with existing setups too.

### Q: What if I hit Let's Encrypt rate limits?
**A:** Use the `--staging` flag for testing: `./bootstrap-ssl.sh --email your@email.com --staging`

### Q: How long does the process take?
**A:** Usually 2-5 minutes for the entire bootstrap process.

### Q: Can I keep my existing data?
**A:** Yes! If you use Option 2 (Update Without Downtime), your database and other data remain intact.

## Troubleshooting

If you still have issues after applying the fix:

1. **Check DNS records**:
   ```bash
   dig dashboard.hanna.co.zw
   dig backend.hanna.co.zw
   dig hanna.co.zw
   ```
   All should point to your server's IP address.

2. **Check port accessibility**:
   ```bash
   telnet your-server-ip 80
   telnet your-server-ip 443
   ```
   Both ports must be open and accessible.

3. **View logs**:
   ```bash
   # nginx logs
   docker-compose logs --tail=50 nginx
   
   # certbot logs  
   docker-compose logs --tail=50 certbot
   ```

4. **Run diagnostics**:
   ```bash
   ./diagnose-ssl.sh
   ```

## Need Help?

If you encounter issues:

1. Read the comprehensive fix documentation: `SSL_CERTIFICATE_FIX.md`
2. Check the SSL setup guide: `SSL_SETUP_GUIDE.md`
3. Review the troubleshooting section in `README_SSL.md`
4. Check Docker logs: `docker-compose logs`

## Files Modified in This Fix

- `docker-compose.yml` - Fixed ACME directory mount
- `certbot-renew.sh` - Added wait logic for initial setup
- `bootstrap-ssl.sh` - Fixed certbot invocation
- `setup-ssl-certificates.sh` - Fixed certbot invocation  
- `README_SSL.md` - Updated documentation
- `SSL_CERTIFICATE_FIX.md` - Detailed fix explanation

## Success Indicators

You'll know the fix worked when:

- ✅ nginx container status shows "Up" (not "Restarting")
- ✅ certbot container status shows "Up"
- ✅ `docker-compose exec certbot certbot certificates` shows your certificates
- ✅ All three domains are accessible via HTTPS
- ✅ Browser shows secure (🔒) padlock icon
- ✅ No SSL certificate warnings in browser
