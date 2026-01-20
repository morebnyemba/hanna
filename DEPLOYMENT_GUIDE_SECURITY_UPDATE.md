# Quick Deployment Guide - Security Updates

## ⚠️ IMPORTANT: Read Before Deploying

This guide helps you deploy the security fixes to your production server safely.

## Pre-Deployment Checklist

- [ ] **Backup your current deployment**
- [ ] **Generate a strong Redis password** (don't use "kayden" in production)
- [ ] **Have SSH access to your VPS**
- [ ] **Ensure you have sudo privileges**

## Step 1: Generate Strong Passwords

```bash
# Generate a strong Redis password (32 characters)
openssl rand -base64 32

# Generate a strong database password (if needed)
openssl rand -base64 32
```

**Save these passwords securely!** You'll need them in the next steps.

## Step 2: Update Environment Variables on VPS

SSH into your VPS and update the environment files:

```bash
# SSH into your server
ssh your-username@srv967860.hstgr.cloud

# Navigate to your project
cd /path/to/hanna

# Backup current .env files
cp .env .env.backup
cp whatsappcrm_backend/.env.prod whatsappcrm_backend/.env.prod.backup

# Edit .env file
nano .env
```

**In .env file, update:**
```bash
REDIS_PASSWORD=<your-strong-redis-password-here>
```

**In whatsappcrm_backend/.env.prod, update:**
```bash
REDIS_PASSWORD=<your-strong-redis-password-here>
DB_PASSWORD=<your-strong-db-password-here>  # If you're also updating this
DJANGO_SECRET_KEY=<your-strong-django-secret-here>  # If not already set
```

## Step 3: Pull Latest Changes

```bash
# Pull the security updates from GitHub
git pull origin copilot/analyze-cves-and-secure-stacks

# Verify changes were pulled
git log -1
```

## Step 4: Rebuild Docker Containers

```bash
# Stop all running containers
docker-compose down

# Remove old images (optional, but recommended)
docker-compose rm -f

# Rebuild with no cache to ensure fresh builds
docker-compose build --no-cache

# This will take 5-10 minutes
```

## Step 5: Start Services

```bash
# Start all services in detached mode
docker-compose up -d

# Wait 30 seconds for services to initialize
sleep 30

# Check service status
docker-compose ps
```

**Expected output:**
All services should show "Up" status:
- whatsappcrm_db
- whatsappcrm_redis
- whatsappcrm_backend_app
- whatsappcrm_frontend_app
- hanna_management_frontend_nextjs
- whatsappcrm_celery_io_worker
- whatsappcrm_celery_cpu_worker
- whatsappcrm_celery_beat
- whatsappcrm_nginx
- whatsappcrm_certbot

## Step 6: Verify Connectivity

```bash
# Check backend logs
docker-compose logs -f backend --tail=50

# Check Redis connection
docker-compose exec backend python manage.py shell -c "from django.core.cache import cache; cache.set('test', 'success'); print(cache.get('test'))"

# Expected output: "success"

# Check Celery workers
docker-compose logs celery_io_worker --tail=20
```

## Step 7: Test Critical Functionality

Open your browser and test:

1. **Next.js Management Frontend**: https://hanna.co.zw
   - [ ] Login works
   - [ ] Dashboard loads
   - [ ] No console errors

2. **Vite Dashboard Frontend**: https://dashboard.hanna.co.zw
   - [ ] Login works
   - [ ] Real-time features work (WebSocket)
   - [ ] No console errors

3. **Backend API**: https://backend.hanna.co.zw/admin/
   - [ ] Admin panel loads
   - [ ] Login works

## Step 8: Clean Server from Malware (Hostinger Requirement)

**Option A: Scan with ClamAV (Recommended)**

```bash
# Install ClamAV
sudo apt-get update
sudo apt-get install -y clamav clamav-daemon

# Update virus definitions (this may take a few minutes)
sudo freshclam

# Scan your application directory
sudo clamscan -r /path/to/hanna --infected --remove --log=/tmp/clamav-scan.log

# Check scan results
cat /tmp/clamav-scan.log | grep "Infected files"
```

**Option B: Manual Security Check**

```bash
# Check for suspicious processes
ps aux | grep -E "(nc|netcat|ncat|/dev/tcp|/dev/udp)"

# Check for recently modified files (last 7 days)
find /path/to/hanna -type f -mtime -7 -ls

# Check for unauthorized cron jobs
crontab -l
sudo crontab -l

# Review nginx access logs for suspicious activity
sudo tail -1000 /var/log/nginx/access.log | grep -E "(\.\.\/|union|select|<script|eval|base64_decode)"

# Check for unauthorized users
sudo cat /etc/passwd | grep "/bin/bash"
```

## Step 9: Monitor After Deployment

For the first 24 hours, monitor:

```bash
# Watch backend logs
docker-compose logs -f backend

# Monitor resource usage
docker stats

# Check for errors
docker-compose logs --tail=100 | grep -i error
```

## Step 10: Contact Hostinger

After completing all steps above:

1. Take screenshots of:
   - `npm list next react` output showing updated versions
   - Docker containers running (`docker-compose ps`)
   - Clean malware scan results

2. Reply to Hostinger support ticket with:
   ```
   Subject: Security Updates Completed - VPS srv967860.hstgr.cloud

   Hi Kodee,

   I have completed all required security updates:

   1. ✅ Updated Next.js from 16.0.1 to 16.1.4
   2. ✅ Updated React to 19.2.0 (already compliant)
   3. ✅ Scanned and cleaned server from malware using ClamAV
   4. ✅ Enhanced Redis security configuration
   5. ✅ Fixed all critical and high-severity vulnerabilities

   The application is now running securely with the latest patched versions.

   Please reactivate the VPS.

   Attached: Screenshots of updated versions and clean scan results.

   Thank you.
   ```

## Troubleshooting

### Issue: Containers won't start

```bash
# Check logs for specific service
docker-compose logs <service-name>

# Common issues:
# - Redis authentication: Check REDIS_PASSWORD in .env files
# - Database connection: Check DB_PASSWORD matches
# - Port conflicts: Check if ports 80/443/5432/6379 are already in use
```

### Issue: "Redis connection failed"

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli -a "your-redis-password" ping
# Expected output: PONG

# Check Redis password in settings
docker-compose exec backend python manage.py shell -c "import os; print(os.getenv('REDIS_PASSWORD'))"
```

### Issue: Frontend shows errors

```bash
# Check nginx configuration
docker-compose exec nginx nginx -t

# Restart nginx
docker-compose restart nginx

# Clear browser cache and cookies
# Try accessing in incognito mode
```

## Rollback Plan (If Something Goes Wrong)

If you encounter critical issues:

```bash
# Stop new containers
docker-compose down

# Restore backup environment files
cp .env.backup .env
cp whatsappcrm_backend/.env.prod.backup whatsappcrm_backend/.env.prod

# Checkout previous version
git checkout HEAD~1

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

## Support

If you need help:
- Check logs: `docker-compose logs <service-name>`
- Review SECURITY_IMPROVEMENTS.md for detailed information
- Contact GitHub Copilot support

---

**Security Update Completed:** ✅
**Next Review:** Schedule for 30 days from now
**Monitoring:** Enable GitHub Dependabot alerts
