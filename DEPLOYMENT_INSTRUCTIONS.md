# Deployment Instructions - Media Files Fix

## Quick Deployment Guide

This guide explains how to deploy the media files fix to your production server.

## What Was Fixed

Media files were not accessible via HTTPS because Django's `static()` helper doesn't work when `DEBUG=False`. The fix adds explicit URL patterns for media files in production mode.

## Prerequisites

- SSH access to your server
- Docker and docker-compose installed
- Existing HANNA deployment running

## Deployment Steps

### Step 1: Connect to Your Server

```bash
ssh root@your-server-ip
cd ~/HANNA  # or wherever your HANNA directory is located
```

### Step 2: Pull Latest Changes

```bash
git pull origin main
```

This will pull the changes including:
- Fixed `whatsappcrm_backend/whatsappcrm_backend/urls.py`
- Documentation files
- Diagnostic scripts

### Step 3: Restart Backend Container

The backend container needs to be restarted to load the new URL configuration:

```bash
docker-compose restart backend
```

Wait for the container to restart (usually 5-10 seconds).

### Step 4: Verify the Fix

Test that media files are now accessible:

```bash
# Test the docker-test.txt file
curl -v https://backend.hanna.co.zw/media/docker-test.txt

# Expected output:
# HTTP/2 200
# Content-Type: text/plain
# 
# Test media file from Docker
```

If you get a `404` or empty response, proceed to troubleshooting.

### Step 5: Test with Real Product Images

```bash
# List existing product images
docker-compose exec backend ls -la /app/mediafiles/product_images/

# Test accessing a real product image (replace with actual filename)
curl -I https://backend.hanna.co.zw/media/product_images/YOUR_IMAGE.png

# Expected: HTTP/2 200
```

### Step 6: Run Diagnostic Script (Optional)

For comprehensive diagnostic information:

```bash
chmod +x diagnose_npm_media.sh
./diagnose_npm_media.sh
```

This script will check:
- Container status
- File existence in both containers
- Volume mounts
- HTTP accessibility
- NPM configuration

## Troubleshooting

### Issue: Still Getting Empty Response

**Solution 1: Check Backend Logs**
```bash
docker-compose logs backend | tail -50
```
Look for any errors related to media serving or URL configuration.

**Solution 2: Verify DEBUG Setting**
```bash
docker-compose exec backend cat /app/.env.prod | grep DEBUG
```
Should show: `DJANGO_DEBUG=False`

**Solution 3: Restart All Containers**
```bash
docker-compose restart
```

### Issue: File Not Found (404)

**Possible Cause:** File doesn't exist in the container

**Solution:**
```bash
# Check if file exists
docker-compose exec backend ls -la /app/mediafiles/

# Create test file if missing
docker-compose exec backend sh -c "echo 'Test media file' > /app/mediafiles/test.txt"

# Test again
curl https://backend.hanna.co.zw/media/test.txt
```

### Issue: Permission Denied (403)

**Possible Cause:** File permissions too restrictive

**Solution:**
```bash
# Fix permissions
docker-compose exec backend chmod -R 755 /app/mediafiles/
docker-compose exec backend chown -R root:root /app/mediafiles/

# Test again
curl https://backend.hanna.co.zw/media/test.txt
```

### Issue: Connection Error

**Possible Cause:** Backend container not running or not accessible

**Solution:**
```bash
# Check container status
docker-compose ps

# Check if backend is running
docker-compose ps backend

# If not running, start it
docker-compose up -d backend

# Check backend logs
docker-compose logs backend
```

## Verification Checklist

After deployment, verify:

- [ ] Backend container restarted successfully
- [ ] Test file accessible: `curl https://backend.hanna.co.zw/media/docker-test.txt`
- [ ] Product images accessible (if any)
- [ ] No errors in backend logs: `docker-compose logs backend --tail=50`
- [ ] Meta product sync working (if applicable)

## Performance Optimization (Optional)

For better performance, consider configuring NPM to serve media files directly instead of proxying to Django. See `NPM_MEDIA_FIX_GUIDE.md` for detailed instructions.

**Benefits:**
- Faster media file delivery
- Reduced load on Django
- Better caching

**Trade-offs:**
- Requires manual NPM configuration via web UI
- Additional setup step

## Rollback Instructions

If you need to rollback this change:

```bash
# Checkout previous version
git log --oneline  # Find the commit hash before the fix
git checkout <previous-commit-hash>

# Restart backend
docker-compose restart backend
```

Note: Rollback will restore the issue where media files are not accessible in production.

## What to Do Next

1. **Immediate:** Deploy the fix and verify media access
2. **Short-term:** Configure NPM custom location for better performance (see NPM_MEDIA_FIX_GUIDE.md)
3. **Long-term:** Consider cloud storage (S3/Spaces) for scalability

## Support

If you encounter issues:

1. Run the diagnostic script: `./diagnose_npm_media.sh`
2. Check the logs: `docker-compose logs backend`
3. Review documentation:
   - `MEDIA_FIX_SUMMARY.md` - Complete fix explanation
   - `NPM_MEDIA_FIX_GUIDE.md` - NPM configuration guide
   - This file - Deployment instructions

## Summary

This fix ensures media files are accessible in production by:
- Adding explicit URL patterns when DEBUG=False
- Using Django's serve view to handle media requests
- Maintaining backward compatibility with DEBUG=True mode

The deployment is straightforward:
1. Pull changes
2. Restart backend
3. Verify access

Total downtime: ~10 seconds (during backend restart)
