# HANNA - WhatsApp CRM SSL Setup

## Quick Start for SSL Certificate Setup

### Prerequisites
- Docker and docker-compose installed
- DNS records pointing to your server for:
  - `dashboard.hanna.co.zw`
  - `backend.hanna.co.zw`
  - `hanna.co.zw`
- Ports 80 and 443 accessible from the internet

### Step 1: Start the Application

```bash
docker-compose up -d
```

### Step 2: Obtain SSL Certificates

```bash
# Run the SSL setup script
./setup-ssl-certificates.sh
```

The script will:
1. Create the ACME challenge directory
2. Obtain SSL certificates from Let's Encrypt for all domains
3. Restart nginx to load the new certificates

### Step 3: Verify Setup

```bash
# Run diagnostics
./diagnose-ssl.sh

# Test HTTPS access
curl -I https://dashboard.hanna.co.zw
curl -I https://backend.hanna.co.zw
curl -I https://hanna.co.zw
```

## Automatic Certificate Renewal

SSL certificates are automatically renewed by the `certbot` container every 12 hours. The container runs in the background and checks if certificates need renewal (Let's Encrypt certificates expire after 90 days).

To check the renewal status:

```bash
# View certbot logs
docker-compose logs certbot

# Manually trigger renewal
docker-compose exec certbot certbot renew --webroot -w /var/www/letsencrypt
docker-compose restart nginx
```

## Troubleshooting

### Issue: Certificate files not found

**Solution:** Run the SSL setup script:
```bash
./setup-ssl-certificates.sh
```

### Issue: Domains not accessible

**Solution:** Check DNS and firewall:
```bash
# Check DNS
dig dashboard.hanna.co.zw

# Check if nginx is running
docker-compose ps nginx

# View nginx logs
docker-compose logs nginx
```

### Issue: ACME challenge failed

**Solution:** Ensure port 80 is accessible and the ACME directory is mounted:
```bash
# Test HTTP access
curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test

# Check if ACME directory exists
docker-compose exec nginx ls -la /var/www/letsencrypt/
```

For more detailed troubleshooting, run:
```bash
./diagnose-ssl.sh
```

## Documentation

- **[SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md)** - Complete SSL certificate setup and management guide
- **[DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md)** - General deployment instructions
- **[CUSTOM_NGINX_MIGRATION_GUIDE.md](CUSTOM_NGINX_MIGRATION_GUIDE.md)** - Migration guide from NPM to custom nginx

## What Changed

### Docker Compose
- Added `letsencrypt_webroot` volume for ACME challenge files
- Added volume mount in nginx service: `letsencrypt_webroot:/var/www/letsencrypt:ro`
- Added `certbot` service for automatic certificate renewal

### New Files
- `setup-ssl-certificates.sh` - Script to obtain initial SSL certificates
- `diagnose-ssl.sh` - Diagnostic tool for SSL and domain issues
- `SSL_SETUP_GUIDE.md` - Comprehensive SSL setup guide

## Security Features

- ✅ TLS 1.2 and 1.3 only
- ✅ Strong cipher suites
- ✅ HSTS enabled
- ✅ OCSP stapling
- ✅ Automatic certificate renewal
- ✅ Perfect forward secrecy

## Support

If you encounter issues:
1. Run the diagnostic script: `./diagnose-ssl.sh`
2. Check the SSL setup guide: `SSL_SETUP_GUIDE.md`
3. View container logs: `docker-compose logs nginx` or `docker-compose logs certbot`
