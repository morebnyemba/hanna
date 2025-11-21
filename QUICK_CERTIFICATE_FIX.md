# Quick Certificate Fix Guide

**Problem:** Browser shows security warnings after certificates were issued.

## Quick Diagnosis (30 seconds)

Run this command to identify the issue:

```bash
./check-certificate-paths.sh
```

The script will tell you exactly what's wrong.

## Quick Fixes

Based on the diagnostic output, choose the appropriate fix:

### Fix 1: Staging Certificate (Most Common)

**Symptom:** Script shows "Using STAGING certificate"

**Solution:**
```bash
docker-compose down
./bootstrap-ssl.sh --email your-email@example.com
```

**Time:** 5-10 minutes

---

### Fix 2: Wrong Certificate Path

**Symptom:** Script shows "Certificate is in unexpected location"

**Solution:**
```bash
./fix-certificate-paths.sh
```

Follow the prompts to update nginx configuration.

**Time:** 30 seconds

---

### Fix 3: Expired Certificate

**Symptom:** Script shows "Certificate has EXPIRED"

**Solution:**
```bash
./setup-ssl-certificates.sh --email your-email@example.com
docker-compose exec nginx nginx -s reload
```

**Time:** 2-3 minutes

---

### Fix 4: Nginx Not Reloaded

**Symptom:** Certificate is valid but browser still shows warnings

**Solution:**
```bash
# Try graceful reload first
docker-compose exec nginx nginx -s reload

# If that doesn't work, restart nginx
docker-compose restart nginx

# Clear your browser cache
```

**Time:** 30 seconds

---

### Fix 5: No Certificates Found

**Symptom:** Script shows "Certificate files are MISSING"

**Solution:**
```bash
./bootstrap-ssl.sh --email your-email@example.com
```

**Time:** 5-10 minutes

---

## After Applying Fix

1. **Verify the fix:**
   ```bash
   ./check-certificate-paths.sh
   ```

2. **Test in browser:**
   - Visit: https://dashboard.hanna.co.zw
   - Visit: https://backend.hanna.co.zw
   - Visit: https://hanna.co.zw

3. **Clear browser cache if needed:**
   - Chrome: Settings → Privacy → Clear browsing data → Cached files
   - Firefox: Settings → Privacy → Clear Data → Cached Web Content
   - Or use private/incognito window

## Still Having Issues?

1. **Run full diagnostics:**
   ```bash
   ./diagnose-ssl.sh
   ```

2. **Check nginx logs:**
   ```bash
   docker-compose logs nginx
   ```

3. **Check certbot logs:**
   ```bash
   docker-compose logs certbot
   ```

4. **Read detailed documentation:**
   - [CERTIFICATE_DIRECTORY_FIX.md](./CERTIFICATE_DIRECTORY_FIX.md) - Complete guide
   - [SSL_BROWSER_WARNING_FIX.md](./SSL_BROWSER_WARNING_FIX.md) - Browser warnings

## Prevention

**Set up automatic nginx reload after certificate renewal:**

```bash
# Add to crontab
0 3 * * * cd /path/to/hanna && docker-compose exec nginx nginx -s reload
```

**Check certificate expiry monthly:**

```bash
docker-compose exec certbot certbot certificates
```

## Common Mistakes

❌ **Don't do this:**
- Use `--staging` flag in production
- Forget to reload nginx after getting certificates
- Create separate certificates for each domain
- Ignore certificate expiration warnings

✅ **Do this:**
- Use production certificates (no `--staging` flag)
- Reload nginx after certificate updates
- Use one certificate for all domains
- Monitor certificate expiration dates

## Need Help?

If you've tried all the fixes and still have issues:

1. Run: `./check-certificate-paths.sh > certificate-diagnosis.txt`
2. Run: `docker-compose logs nginx > nginx-logs.txt`
3. Run: `docker-compose logs certbot > certbot-logs.txt`
4. Share these files when requesting help

## Technical Notes

- **Certificate type:** Let's Encrypt SAN (Subject Alternative Name) certificate
- **Covers domains:** dashboard.hanna.co.zw, backend.hanna.co.zw, hanna.co.zw
- **Validity:** 90 days
- **Auto-renewal:** Every 12 hours (when < 30 days remaining)
- **Location:** `/etc/letsencrypt/live/dashboard.hanna.co.zw/`

---

**Quick Links:**
- [Full Documentation](./CERTIFICATE_DIRECTORY_FIX.md)
- [SSL Setup Guide](./SSL_SETUP_GUIDE.md)
- [Browser Warning Fixes](./SSL_BROWSER_WARNING_FIX.md)
