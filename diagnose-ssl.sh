#!/bin/bash

# SSL and Domain Access Diagnostic Script
# This script checks the SSL and domain configuration for HANNA

set -e

echo "=== HANNA SSL and Domain Diagnostic Tool ==="
echo ""

# Configuration
DOMAINS="dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
EXPECTED_IP=""  # Leave empty to skip IP check

echo "Checking domain configuration for:"
for domain in $DOMAINS; do
    echo "  - $domain"
done
echo ""

# Function to print section header
print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Function to print success
print_success() {
    echo "✓ $1"
}

# Function to print error
print_error() {
    echo "✗ $1"
}

# Function to print warning
print_warning() {
    echo "⚠ $1"
}

# Check 1: Docker Services
print_header "1. Docker Services Status"

if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed"
    exit 1
fi

echo "Checking container status..."
docker-compose ps

# Check nginx specifically
if docker-compose ps nginx | grep -q "Up"; then
    print_success "nginx container is running"
else
    print_error "nginx container is NOT running"
    echo "  Start it with: docker-compose up -d nginx"
fi

# Check certbot
if docker-compose ps certbot | grep -q "Up"; then
    print_success "certbot container is running"
else
    print_warning "certbot container is NOT running (needed for certificate renewal)"
    echo "  Start it with: docker-compose up -d certbot"
fi

# Check 2: DNS Resolution
print_header "2. DNS Resolution"

for domain in $DOMAINS; do
    echo "Checking $domain..."
    if command -v dig &> /dev/null; then
        IP=$(dig +short $domain | tail -n1)
        if [ -n "$IP" ]; then
            print_success "$domain resolves to $IP"
        else
            print_error "$domain does not resolve"
        fi
    elif command -v nslookup &> /dev/null; then
        if nslookup $domain > /dev/null 2>&1; then
            print_success "$domain resolves"
        else
            print_error "$domain does not resolve"
        fi
    else
        print_warning "dig or nslookup not available, skipping DNS check"
        break
    fi
done

# Check 3: SSL Certificates
print_header "3. SSL Certificates"

# Get the first domain for certificate path check
FIRST_DOMAIN=$(echo $DOMAINS | awk '{print $1}')

echo "Checking if certificates exist..."
if docker-compose exec -T nginx test -f /etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem 2>/dev/null; then
    print_success "Certificate files exist in nginx container"
    
    # Check certificate validity
    echo ""
    echo "Certificate details:"
    docker-compose exec -T nginx openssl x509 -in /etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem -noout -subject -issuer -dates 2>/dev/null || true
else
    print_error "Certificate files NOT found in nginx container"
    echo ""
    echo "  To obtain certificates, run:"
    echo "    ./setup-ssl-certificates.sh"
fi

# Check certbot volume
echo ""
echo "Checking certbot certificates..."
if docker-compose run --rm certbot certbot certificates 2>/dev/null | grep -q "Certificate Name"; then
    docker-compose run --rm certbot certbot certificates
else
    print_warning "No certificates found in certbot"
fi

# Check 4: ACME Challenge Directory
print_header "4. ACME Challenge Configuration"

echo "Checking ACME challenge directory..."
if docker-compose exec -T nginx test -d /var/www/letsencrypt 2>/dev/null; then
    print_success "ACME challenge directory exists in nginx"
    docker-compose exec -T nginx ls -la /var/www/letsencrypt/ 2>/dev/null || true
else
    print_error "ACME challenge directory NOT found in nginx"
    echo "  Creating directory..."
    docker-compose exec -T nginx mkdir -p /var/www/letsencrypt
fi

# Check 5: Nginx Configuration
print_header "5. Nginx Configuration"

echo "Testing nginx configuration..."
if docker-compose exec -T nginx nginx -t 2>&1; then
    print_success "nginx configuration is valid"
else
    print_error "nginx configuration has errors"
    echo "  Check nginx configuration in nginx_proxy/nginx.conf"
fi

# Check 6: Port Accessibility
print_header "6. Port Accessibility"

echo "Checking if ports 80 and 443 are listening..."
if docker-compose exec -T nginx netstat -tlnp 2>/dev/null | grep -q ":80"; then
    print_success "Port 80 is listening"
else
    print_error "Port 80 is NOT listening"
fi

if docker-compose exec -T nginx netstat -tlnp 2>/dev/null | grep -q ":443"; then
    print_success "Port 443 is listening"
else
    print_error "Port 443 is NOT listening"
fi

# Check 7: HTTP/HTTPS Access
print_header "7. Domain Accessibility"

for domain in $DOMAINS; do
    echo ""
    echo "Testing $domain..."
    
    # Test HTTP (should redirect to HTTPS)
    echo "  Checking HTTP..."
    if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$domain 2>/dev/null | grep -q "30[12]"; then
        print_success "HTTP access OK (redirects to HTTPS)"
    else
        print_error "HTTP access failed or doesn't redirect"
    fi
    
    # Test HTTPS
    echo "  Checking HTTPS..."
    HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://$domain 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        print_success "HTTPS access OK (HTTP $HTTP_CODE)"
    else
        print_error "HTTPS access failed (HTTP $HTTP_CODE)"
    fi
done

# Check 8: SSL Certificate Validity (external check)
print_header "8. SSL Certificate Validity (External Check)"

for domain in $DOMAINS; do
    echo "Checking SSL certificate for $domain..."
    if command -v openssl &> /dev/null; then
        if timeout 5 openssl s_client -connect $domain:443 -servername $domain < /dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null; then
            print_success "SSL certificate is valid"
        else
            print_warning "Could not verify SSL certificate (may not be accessible from this network)"
        fi
    else
        print_warning "openssl not available, skipping external SSL check"
        break
    fi
    echo ""
done

# Summary
print_header "Summary and Recommendations"

echo "Docker Services:"
echo "  - Nginx: $(docker-compose ps -q nginx > /dev/null 2>&1 && echo '✓ Running' || echo '✗ Not Running')"
echo "  - Certbot: $(docker-compose ps -q certbot > /dev/null 2>&1 && echo '✓ Running' || echo '✗ Not Running')"
echo ""

if docker-compose exec -T nginx test -f /etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem 2>/dev/null; then
    echo "SSL Certificates: ✓ Present"
else
    echo "SSL Certificates: ✗ Missing"
    echo ""
    echo "ACTION REQUIRED:"
    echo "  1. Ensure DNS records point to this server"
    echo "  2. Ensure ports 80 and 443 are accessible"
    echo "  3. Run: ./setup-ssl-certificates.sh"
fi

echo ""
echo "For more information, see:"
echo "  - SSL_SETUP_GUIDE.md - Complete SSL setup guide"
echo "  - docker-compose logs nginx - Nginx logs"
echo "  - docker-compose logs certbot - Certbot logs"
echo ""
