# Quick Deployment Guide - SSL Fix

## TL;DR - Get SSL Working in 5 Minutes

This is the fastest way to deploy the SSL certificate fix and get your domains accessible.

## Prerequisites Check (30 seconds)

```bash
# 1. DNS points to your server?
dig dashboard.hanna.co.zw +short
dig backend.hanna.co.zw +short
dig hanna.co.zw +short

# 2. Ports open?
sudo ufw status | grep -E '80|443'

# 3. Docker running?
docker --version && docker-compose --version
```

If all three checks pass, proceed. If not, see [SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md) for details.

## Deployment Steps (4 minutes)

### Step 1: Pull Changes (30 seconds)
```bash
cd ~/HANNA  # or your installation directory
git pull origin main
```

### Step 2: Start Services (1 minute)
```bash
docker-compose up -d
docker-compose ps  # Verify all services are "Up"
```

### Step 3: Get SSL Certificates (2 minutes)
```bash
# Make script executable (if needed)
chmod +x setup-ssl-certificates.sh

# Run setup (replace with your email)
./setup-ssl-certificates.sh --email your-email@example.com
```

**Note:** If you see "Failed to obtain certificates", this is usually because:
- DNS not propagated yet (wait 10-30 minutes)
- Port 80 blocked by firewall (check firewall)
- Domain doesn't point to this server (check DNS)

For testing without hitting rate limits:
```bash
./setup-ssl-certificates.sh --staging --email your-email@example.com
```

### Step 4: Verify (30 seconds)
```bash
# Quick test
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw
curl -I https://hanna.co.zw

# Or run full diagnostics
./diagnose-ssl.sh
```

Expected: HTTP/2 200 responses with no SSL errors

## Done! 🎉

Your domains should now be accessible via HTTPS with valid SSL certificates.

- Dashboard: https://dashboard.hanna.co.zw
- Backend: https://backend.hanna.co.zw
- Management: https://hanna.co.zw

## What Changed?

1. ✅ Added ACME challenge directory for Let's Encrypt verification
2. ✅ Added certbot service for automatic certificate renewal
3. ✅ Created setup script for easy SSL certificate acquisition

## Automatic Renewal

Certificates are automatically renewed every 12 hours by the certbot container. No manual action needed.

Check renewal status:
```bash
docker-compose logs certbot | tail -20
```

## Troubleshooting

### Issue: "Failed to obtain certificates"

**Quick Fix:**
```bash
# 1. Check DNS
dig dashboard.hanna.co.zw

# 2. Check nginx logs
docker-compose logs nginx | tail -50

# 3. Try staging mode
./setup-ssl-certificates.sh --staging
```

### Issue: "nginx fails to start"

**Quick Fix:**
```bash
# Create temporary certificates
docker-compose run --rm certbot sh -c "
  mkdir -p /etc/letsencrypt/live/dashboard.hanna.co.zw && \
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem \
    -out /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem \
    -subj '/CN=dashboard.hanna.co.zw'
"

# Start nginx
docker-compose up -d nginx

# Get real certificates
./setup-ssl-certificates.sh
```

### Issue: "Certificate expired"

**Quick Fix:**
```bash
# Force renewal
docker-compose exec certbot certbot renew --force-renewal
docker-compose restart nginx
```

## Need More Help?

- **Full guide:** [SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md)
- **Testing:** [SSL_TESTING_CHECKLIST.md](SSL_TESTING_CHECKLIST.md)
- **Technical details:** [DOMAIN_SSL_FIX_SUMMARY.md](DOMAIN_SSL_FIX_SUMMARY.md)
- **Diagnostic tool:** `./diagnose-ssl.sh`

## Rollback

If you need to undo these changes:

```bash
git log --oneline  # Find commit before this fix
git checkout <previous-commit>
docker-compose down
docker-compose up -d
```

## Summary

- **Setup time:** ~5 minutes
- **Downtime:** None (nginx restarts only)
- **Certificates:** Valid for 90 days, auto-renewed
- **Maintenance:** Zero (automatic renewal)

---

**Status after deployment:**
- ✅ HTTPS working
- ✅ Valid SSL certificates
- ✅ Automatic renewal configured
- ✅ All domains accessible
