# SSL Setup Testing Checklist

This checklist helps verify that the SSL certificate setup is working correctly.

## Pre-Deployment Checklist

Before running the SSL setup on production:

### DNS Configuration
- [ ] Verify DNS records point to your server
  ```bash
  dig dashboard.hanna.co.zw +short
  dig backend.hanna.co.zw +short
  dig hanna.co.zw +short
  ```
- [ ] Confirm all domains resolve to the correct IP address
- [ ] Wait for DNS propagation if records were recently changed (up to 48 hours)

### Firewall Configuration
- [ ] Port 80 (HTTP) is open and accessible from internet
  ```bash
  sudo ufw status | grep 80
  # or
  sudo iptables -L | grep 80
  ```
- [ ] Port 443 (HTTPS) is open and accessible from internet
  ```bash
  sudo ufw status | grep 443
  # or
  sudo iptables -L | grep 443
  ```
- [ ] Test external port accessibility (from another machine)
  ```bash
  telnet YOUR_SERVER_IP 80
  telnet YOUR_SERVER_IP 443
  ```

### Docker Environment
- [ ] Docker is installed and running
  ```bash
  docker --version
  docker ps
  ```
- [ ] docker-compose is installed
  ```bash
  docker-compose --version
  ```
- [ ] No port conflicts on 80 and 443
  ```bash
  sudo netstat -tlnp | grep ':80\|:443'
  ```

## Deployment Testing

### Step 1: Script Validation
- [ ] Scripts have executable permissions
  ```bash
  ls -l setup-ssl-certificates.sh diagnose-ssl.sh certbot-renew.sh
  ```
- [ ] Scripts have valid syntax
  ```bash
  bash -n setup-ssl-certificates.sh
  bash -n diagnose-ssl.sh
  bash -n certbot-renew.sh
  ```
- [ ] Help output displays correctly
  ```bash
  ./setup-ssl-certificates.sh --help
  ```

### Step 2: Service Startup
- [ ] Start all services
  ```bash
  docker-compose up -d
  ```
- [ ] Verify all containers are running
  ```bash
  docker-compose ps
  ```
  Expected: All services showing "Up"
  
- [ ] Check nginx is running
  ```bash
  docker-compose ps nginx | grep Up
  ```
- [ ] Check certbot is running
  ```bash
  docker-compose ps certbot | grep Up
  ```

### Step 3: Pre-SSL Tests
- [ ] HTTP access works (before SSL)
  ```bash
  curl -I http://dashboard.hanna.co.zw
  ```
  Expected: Should connect (may get redirect or error, but connection should work)

- [ ] ACME challenge directory exists
  ```bash
  docker-compose exec nginx ls -la /var/www/letsencrypt/
  ```

### Step 4: SSL Certificate Acquisition (Staging)
**Test with staging first to avoid rate limits:**

- [ ] Run setup script with staging flag
  ```bash
  ./setup-ssl-certificates.sh --staging --email your-email@example.com
  ```
- [ ] Script completes without errors
- [ ] Certificates are created
  ```bash
  docker-compose exec certbot certbot certificates
  ```
- [ ] nginx restarts successfully
  ```bash
  docker-compose ps nginx | grep Up
  ```

### Step 5: SSL Certificate Acquisition (Production)
**Only proceed if staging tests pass:**

- [ ] Delete staging certificates
  ```bash
  docker-compose exec certbot certbot delete --cert-name dashboard.hanna.co.zw
  ```
- [ ] Run setup script for production
  ```bash
  ./setup-ssl-certificates.sh --email your-email@example.com
  ```
- [ ] Script completes without errors
- [ ] Production certificates are created
  ```bash
  docker-compose exec certbot certbot certificates
  ```

### Step 6: HTTPS Access Tests
- [ ] HTTPS access to dashboard works
  ```bash
  curl -I https://dashboard.hanna.co.zw
  ```
  Expected: HTTP/2 200 or valid response

- [ ] HTTPS access to backend works
  ```bash
  curl -I https://backend.hanna.co.zw
  ```
  Expected: HTTP/2 200 or valid response

- [ ] HTTPS access to main site works
  ```bash
  curl -I https://hanna.co.zw
  ```
  Expected: HTTP/2 200 or valid response

- [ ] HTTP redirects to HTTPS
  ```bash
  curl -I http://dashboard.hanna.co.zw
  ```
  Expected: 301 redirect to https://

### Step 7: Certificate Validation
- [ ] Certificate is trusted (not self-signed)
  ```bash
  curl https://dashboard.hanna.co.zw
  ```
  No SSL errors expected

- [ ] Certificate contains correct domains
  ```bash
  openssl s_client -connect dashboard.hanna.co.zw:443 -servername dashboard.hanna.co.zw < /dev/null 2>/dev/null | openssl x509 -noout -text | grep "Subject:"
  ```

- [ ] Certificate is valid (not expired)
  ```bash
  openssl s_client -connect dashboard.hanna.co.zw:443 -servername dashboard.hanna.co.zw < /dev/null 2>/dev/null | openssl x509 -noout -dates
  ```

- [ ] Certificate expiry date is ~90 days in future
  ```bash
  docker-compose exec certbot certbot certificates
  ```

### Step 8: Browser Tests
- [ ] Access https://dashboard.hanna.co.zw in browser
  - [ ] Page loads without SSL warnings
  - [ ] Padlock icon shows secure connection
  - [ ] Certificate details show valid issuer (Let's Encrypt)

- [ ] Access https://backend.hanna.co.zw in browser
  - [ ] API endpoints accessible
  - [ ] No mixed content warnings

- [ ] Access https://hanna.co.zw in browser
  - [ ] Page loads correctly
  - [ ] All resources load over HTTPS

### Step 9: Automatic Renewal Test
- [ ] Certbot container is running
  ```bash
  docker-compose ps certbot
  ```

- [ ] Certbot logs show renewal check activity
  ```bash
  docker-compose logs certbot | tail -20
  ```

- [ ] Test manual renewal (should say not due yet)
  ```bash
  docker-compose exec certbot certbot renew --dry-run
  ```

### Step 10: Diagnostic Tool Test
- [ ] Run diagnostic script
  ```bash
  ./diagnose-ssl.sh
  ```
- [ ] All checks pass with ✓ marks
- [ ] No critical errors reported

## Post-Deployment Monitoring

### Daily (First Week)
- [ ] Check certbot logs for errors
  ```bash
  docker-compose logs certbot | grep -i error
  ```
- [ ] Verify HTTPS access still works
- [ ] Check certificate hasn't expired unexpectedly

### Weekly
- [ ] Review certbot renewal logs
- [ ] Verify all services still running
  ```bash
  docker-compose ps
  ```

### Monthly
- [ ] Check certificate expiry date
  ```bash
  docker-compose exec certbot certbot certificates
  ```
- [ ] Backup certificates
  ```bash
  docker run --rm -v npm_letsencrypt:/etc/letsencrypt -v $(pwd):/backup alpine \
    tar czf /backup/letsencrypt-backup-$(date +%Y%m%d).tar.gz /etc/letsencrypt
  ```

## Troubleshooting Tests

If issues occur, run these tests:

### Certificate Not Found
- [ ] Check if certificates exist in volume
  ```bash
  docker-compose exec certbot ls -la /etc/letsencrypt/live/
  ```
- [ ] Check nginx can access certificates
  ```bash
  docker-compose exec nginx ls -la /etc/letsencrypt/live/
  ```

### ACME Challenge Failed
- [ ] Test ACME directory is accessible
  ```bash
  docker-compose exec certbot sh -c "echo 'test' > /var/www/letsencrypt/test.txt"
  curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test.txt
  ```
- [ ] Check nginx configuration
  ```bash
  docker-compose exec nginx nginx -t
  ```

### Renewal Failed
- [ ] Check certbot can connect to Let's Encrypt
  ```bash
  docker-compose exec certbot curl -I https://acme-v02.api.letsencrypt.org/directory
  ```
- [ ] Test renewal in verbose mode
  ```bash
  docker-compose exec certbot certbot renew --dry-run -v
  ```

## Performance Tests

### Response Time
- [ ] Measure HTTPS response time
  ```bash
  time curl -I https://dashboard.hanna.co.zw
  ```
  Expected: < 1 second

### SSL Handshake Time
- [ ] Test SSL handshake performance
  ```bash
  openssl s_client -connect dashboard.hanna.co.zw:443 -servername dashboard.hanna.co.zw -tls1_2 < /dev/null
  ```

### Load Test
- [ ] Concurrent connections test
  ```bash
  # Using ab (Apache Bench) if available
  ab -n 100 -c 10 https://dashboard.hanna.co.zw/
  ```

## Security Tests

### SSL Configuration
- [ ] Test SSL configuration quality
  ```bash
  # Online test: https://www.ssllabs.com/ssltest/
  # or use testssl.sh
  ```

### HSTS Header
- [ ] Verify HSTS header is present
  ```bash
  curl -I https://dashboard.hanna.co.zw | grep -i strict-transport
  ```
  Expected: Strict-Transport-Security header present

### Security Headers
- [ ] Check security headers
  ```bash
  curl -I https://dashboard.hanna.co.zw | grep -E "X-Frame-Options|X-Content-Type-Options|Referrer-Policy"
  ```

## Rollback Tests

### If rollback is needed:
- [ ] Backup current state
- [ ] Stop certbot
  ```bash
  docker-compose stop certbot
  ```
- [ ] Generate temporary self-signed certificate
- [ ] Restart nginx
- [ ] Verify basic HTTPS access (with warning)

## Sign-off

### Final Verification
- [ ] All domains accessible via HTTPS
- [ ] No browser security warnings
- [ ] Certificates auto-renew
- [ ] All services running stably
- [ ] Documentation reviewed
- [ ] Team notified of changes

### Sign-off
- Tested by: ________________
- Date: ________________
- Environment: Production / Staging
- Result: Pass / Fail
- Notes: ________________

## Quick Reference Commands

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs nginx
docker-compose logs certbot

# Restart services
docker-compose restart nginx
docker-compose restart certbot

# Manual certificate renewal
docker-compose exec certbot certbot renew --force-renewal
docker-compose restart nginx

# Check certificates
docker-compose exec certbot certbot certificates

# Test HTTPS
curl -I https://dashboard.hanna.co.zw

# Run diagnostics
./diagnose-ssl.sh

# Get help
./setup-ssl-certificates.sh --help
```
