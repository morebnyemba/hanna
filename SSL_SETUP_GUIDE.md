# SSL Certificate Setup Guide

This guide explains how to set up and manage SSL certificates for the HANNA application.

## Overview

The HANNA application uses Let's Encrypt to obtain free SSL certificates for the following domains:
- `dashboard.hanna.co.zw` - React frontend dashboard
- `backend.hanna.co.zw` - Django backend API
- `hanna.co.zw` - Next.js management frontend

## Prerequisites

Before setting up SSL certificates, ensure:

1. **DNS Records**: All domains must point to your server's IP address
   ```bash
   # Verify DNS records
   dig dashboard.hanna.co.zw
   dig backend.hanna.co.zw
   dig hanna.co.zw
   ```

2. **Firewall**: Ports 80 and 443 must be accessible from the internet
   ```bash
   # Check if ports are open
   sudo ufw status
   # or
   sudo iptables -L
   ```

3. **Docker**: Docker and docker-compose must be installed and running
   ```bash
   docker --version
   docker-compose --version
   ```

## Initial SSL Certificate Setup

### Recommended: Bootstrap Method (New!)

For a fresh installation or when nginx fails to start due to missing certificates, use the bootstrap script:

```bash
# Complete SSL setup in one command
./bootstrap-ssl.sh --email your-email@example.com

# For testing with staging server
./bootstrap-ssl.sh --email your-email@example.com --staging
```

The bootstrap script handles the entire process:
1. Stops any running containers
2. Creates temporary self-signed certificates
3. Starts all services (nginx will start successfully with temp certs)
4. Obtains real Let's Encrypt certificates
5. Replaces temporary certificates with real ones

### Alternative: Step-by-Step Method

If you prefer manual control or need to troubleshoot:

#### Step 1: Initialize SSL (if nginx won't start)

If nginx is failing to start due to missing certificates:

```bash
# Create temporary self-signed certificates
./init-ssl.sh
```

#### Step 2: Start the Application

```bash
# Start all services
docker-compose up -d
```

Wait for all containers to be up and running:

```bash
# Check container status
docker-compose ps
```

#### Step 3: Obtain Real SSL Certificates

```bash
# Use the default configuration
./setup-ssl-certificates.sh --email your-email@example.com

# Or specify custom domains
./setup-ssl-certificates.sh --email your-email@example.com --domains "dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
```

The setup script now automatically:
- Creates temporary certificates if needed
- Starts nginx if it's not running
- Obtains real certificates
- Restarts nginx with the new certificates

For testing purposes, you can use the Let's Encrypt staging server:

```bash
# Use staging server (certificates won't be trusted by browsers)
./setup-ssl-certificates.sh --staging --email your-email@example.com
```

### Step 4: Verify SSL Certificates

After the script completes, verify that SSL certificates are working:

```bash
# Run diagnostics
./diagnose-ssl.sh

# Test HTTPS access
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw
curl -I https://hanna.co.zw

# Check certificate details
openssl s_client -connect dashboard.hanna.co.zw:443 -servername dashboard.hanna.co.zw < /dev/null 2>/dev/null | openssl x509 -noout -dates
```

You should see:
- HTTP/2 200 OK responses
- Valid certificate dates

## Automatic Certificate Renewal

The `certbot` container automatically renews certificates every 12 hours. Let's Encrypt certificates are valid for 90 days and are renewed when they have less than 30 days remaining.

### Verify Automatic Renewal

Check the certbot container logs:

```bash
# View certbot logs
docker-compose logs certbot

# Follow certbot logs in real-time
docker-compose logs -f certbot
```

### Manual Certificate Renewal

To manually renew certificates:

```bash
# Renew all certificates
docker-compose exec certbot certbot renew --webroot -w /var/www/letsencrypt

# Force renewal (even if not expiring soon)
docker-compose exec certbot certbot renew --webroot -w /var/www/letsencrypt --force-renewal

# Restart nginx to load new certificates
docker-compose restart nginx
```

## Troubleshooting

### Issue: "Failed to obtain SSL certificates"

**Possible causes:**
1. DNS records not pointing to the server
2. Port 80 blocked by firewall
3. ACME challenge verification failed

**Solutions:**

1. **Check DNS resolution:**
   ```bash
   # Check if domains resolve to your server IP
   dig dashboard.hanna.co.zw +short
   dig backend.hanna.co.zw +short
   dig hanna.co.zw +short
   ```

2. **Check port 80 accessibility:**
   ```bash
   # From another machine, test if port 80 is accessible
   curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test
   ```

3. **Check nginx logs:**
   ```bash
   docker-compose logs nginx
   ```

4. **Test with staging server:**
   ```bash
   ./setup-ssl-certificates.sh --staging
   ```

### Issue: "nginx fails to start - certificate not found" or "nginx in restart loop"

**Cause:** nginx is trying to load SSL certificates that don't exist yet. This is the most common issue on fresh installations.

**Solution 1: Use the bootstrap script (Recommended)**

```bash
# Complete SSL setup from scratch
./bootstrap-ssl.sh --email your-email@example.com
```

**Solution 2: Use the init script**

```bash
# Create temporary self-signed certificates
./init-ssl.sh

# Start nginx
docker-compose up -d nginx

# Now obtain real certificates
./setup-ssl-certificates.sh --email your-email@example.com
```

**Solution 3: Manual certificate creation**

```bash
# Create temporary self-signed certificates manually
docker-compose run --rm certbot sh -c "
  mkdir -p /etc/letsencrypt/live/dashboard.hanna.co.zw && \
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/letsencrypt/live/dashboard.hanna.co.zw/privkey.pem \
    -out /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem \
    -subj '/CN=dashboard.hanna.co.zw'
"

# Start nginx
docker-compose up -d nginx

# Now obtain real certificates
./setup-ssl-certificates.sh --email your-email@example.com
```

**Solution 4: Modify nginx configuration to start without SSL**

Temporarily comment out the SSL server blocks in `nginx_proxy/nginx.conf`, start nginx, obtain certificates, then uncomment and restart. (Not recommended - use bootstrap script instead)

### Issue: "Rate limit exceeded"

**Cause:** Let's Encrypt has rate limits (50 certificates per domain per week).

**Solution:**

1. Use the staging server for testing:
   ```bash
   ./setup-ssl-certificates.sh --staging
   ```

2. Wait for the rate limit to reset (one week)

3. Use DNS validation instead of HTTP validation (requires certbot DNS plugin)

### Issue: "Certificate expired"

**Cause:** Automatic renewal failed or certbot container not running.

**Solution:**

1. **Check certbot container:**
   ```bash
   docker-compose ps certbot
   ```

2. **Restart certbot container:**
   ```bash
   docker-compose restart certbot
   ```

3. **Manually renew:**
   ```bash
   docker-compose exec certbot certbot renew --force-renewal
   docker-compose restart nginx
   ```

### Issue: "ACME challenge verification failed"

**Cause:** nginx cannot serve files from `/var/www/letsencrypt/`

**Solution:**

1. **Check volume mount:**
   ```bash
   docker-compose exec nginx ls -la /var/www/letsencrypt/
   ```

2. **Create test file:**
   ```bash
   docker-compose exec certbot sh -c "echo 'test' > /var/www/letsencrypt/test.txt"
   ```

3. **Test access:**
   ```bash
   curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test.txt
   ```

## Certificate Management

### View Certificate Information

```bash
# List all certificates
docker-compose exec certbot certbot certificates

# View specific certificate details
docker-compose exec certbot openssl x509 -in /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem -text -noout
```

### Revoke Certificate

```bash
# Revoke a certificate
docker-compose exec certbot certbot revoke --cert-path /etc/letsencrypt/live/dashboard.hanna.co.zw/fullchain.pem
```

### Delete Certificate

```bash
# Delete a certificate
docker-compose exec certbot certbot delete --cert-name dashboard.hanna.co.zw
```

## Adding New Domains

To add a new domain to your SSL certificate:

### Step 1: Update nginx configuration

Edit `nginx_proxy/nginx.conf`:

1. Add domain to HTTP redirect:
   ```nginx
   server_name dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw new-domain.com;
   ```

2. Add new HTTPS server block or update existing one

### Step 2: Obtain certificate for new domain

```bash
# Obtain certificate including the new domain
./setup-ssl-certificates.sh --domains "dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw new-domain.com"

# Or expand existing certificate
docker-compose exec certbot certbot certonly --webroot -w /var/www/letsencrypt \
  --cert-name dashboard.hanna.co.zw \
  -d dashboard.hanna.co.zw -d backend.hanna.co.zw -d hanna.co.zw -d new-domain.com \
  --expand
```

### Step 3: Restart nginx

```bash
docker-compose restart nginx
```

## Security Best Practices

### 1. Keep Certificates Up to Date

Ensure the certbot container is always running:

```bash
# Check if certbot is running
docker-compose ps certbot

# If not, start it
docker-compose up -d certbot
```

### 2. Use Strong SSL Configuration

The application uses Mozilla's recommended SSL configuration in `nginx_proxy/ssl_custom/options-ssl-nginx.conf`:
- TLS 1.2 and 1.3 only
- Strong cipher suites
- OCSP stapling enabled
- Perfect forward secrecy

### 3. Enable HSTS

The nginx configuration already includes HSTS headers:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 4. Monitor Certificate Expiry

Set up monitoring to alert you if certificates are about to expire:

```bash
# Check certificate expiry
docker-compose exec certbot certbot certificates | grep "Expiry Date"

# Or use a cron job to check and alert
```

### 5. Backup Certificates

Regularly backup the `npm_letsencrypt` volume:

```bash
# Backup certificates
docker run --rm -v npm_letsencrypt:/etc/letsencrypt -v $(pwd):/backup alpine \
  tar czf /backup/letsencrypt-backup-$(date +%Y%m%d).tar.gz /etc/letsencrypt

# Restore certificates
docker run --rm -v npm_letsencrypt:/etc/letsencrypt -v $(pwd):/backup alpine \
  tar xzf /backup/letsencrypt-backup-YYYYMMDD.tar.gz -C /
```

## Advanced Configuration

### Using DNS-01 Challenge

For wildcard certificates or when port 80 is not accessible, use DNS validation:

```bash
# Install DNS plugin (example for Cloudflare)
docker-compose exec certbot sh -c "pip install certbot-dns-cloudflare"

# Create credentials file
# ...

# Obtain certificate using DNS validation
docker-compose exec certbot certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /path/to/credentials.ini \
  -d dashboard.hanna.co.zw -d backend.hanna.co.zw -d hanna.co.zw
```

### Custom Renewal Hooks

To run custom commands after renewal, modify the certbot container command in `docker-compose.yml`:

```yaml
certbot:
  # ...
  entrypoint: /bin/sh -c "trap exit TERM; while :; do certbot renew --webroot -w /var/www/letsencrypt --quiet --deploy-hook 'nginx -s reload'; sleep 12h & wait $${!}; done;"
```

## Summary

- ✅ SSL certificates obtained from Let's Encrypt
- ✅ Automatic renewal every 12 hours via certbot container
- ✅ ACME challenge directory properly mounted
- ✅ Strong SSL/TLS configuration
- ✅ HSTS enabled for enhanced security

For questions or issues, refer to:
- Let's Encrypt documentation: https://letsencrypt.org/docs/
- Certbot documentation: https://eff-certbot.readthedocs.io/
- This guide: `SSL_SETUP_GUIDE.md`
