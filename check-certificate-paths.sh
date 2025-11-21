#!/bin/bash

# Certificate Path Verification Script
# This script checks if nginx is using the correct certificate directory
# and diagnoses any browser warning issues

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Certificate Directory Verification Script                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
DOMAINS="dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
FIRST_DOMAIN="dashboard.hanna.co.zw"
CERT_PATH="/etc/letsencrypt/live/$FIRST_DOMAIN"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "$1"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed"
    exit 1
fi

# Check 1: Verify nginx container is running
print_header "1. Nginx Container Status"

if docker-compose ps nginx 2>/dev/null | grep -q "Up"; then
    print_success "nginx container is running"
else
    print_error "nginx container is NOT running"
    echo "  Start it with: docker-compose up -d nginx"
    exit 1
fi

# Check 2: Verify certbot container exists
print_header "2. Certbot Container Status"

if docker-compose ps certbot 2>/dev/null | grep -q "Up"; then
    print_success "certbot container is running"
else
    print_warning "certbot container is NOT running (needed for renewals)"
fi

# Check 3: List certificate files in nginx container
print_header "3. Certificate Files in Nginx Container"

echo "Checking for certificate files at: $CERT_PATH"
echo ""

if docker-compose exec -T nginx test -d "$CERT_PATH" 2>/dev/null; then
    print_success "Certificate directory exists in nginx container"
    echo ""
    echo "Files in certificate directory:"
    docker-compose exec -T nginx ls -lh "$CERT_PATH" 2>/dev/null || true
    echo ""
    
    # Check for required files
    if docker-compose exec -T nginx test -f "$CERT_PATH/fullchain.pem" 2>/dev/null; then
        print_success "fullchain.pem exists"
        FILE_SIZE=$(docker-compose exec -T nginx stat -c%s "$CERT_PATH/fullchain.pem" 2>/dev/null || echo "0")
        echo "  Size: $FILE_SIZE bytes"
    else
        print_error "fullchain.pem is MISSING"
    fi
    
    if docker-compose exec -T nginx test -f "$CERT_PATH/privkey.pem" 2>/dev/null; then
        print_success "privkey.pem exists"
        FILE_SIZE=$(docker-compose exec -T nginx stat -c%s "$CERT_PATH/privkey.pem" 2>/dev/null || echo "0")
        echo "  Size: $FILE_SIZE bytes"
    else
        print_error "privkey.pem is MISSING"
    fi
    
    if docker-compose exec -T nginx test -f "$CERT_PATH/cert.pem" 2>/dev/null; then
        print_success "cert.pem exists (optional)"
    fi
    
    if docker-compose exec -T nginx test -f "$CERT_PATH/chain.pem" 2>/dev/null; then
        print_success "chain.pem exists (optional)"
    fi
else
    print_error "Certificate directory does NOT exist in nginx container"
    echo ""
    echo "Expected path: $CERT_PATH"
    echo ""
    echo "Checking if /etc/letsencrypt volume is mounted..."
    if docker-compose exec -T nginx test -d /etc/letsencrypt 2>/dev/null; then
        print_success "/etc/letsencrypt directory exists"
        echo ""
        echo "Listing /etc/letsencrypt contents:"
        docker-compose exec -T nginx ls -la /etc/letsencrypt/ 2>/dev/null || true
        echo ""
        echo "Listing /etc/letsencrypt/live contents:"
        docker-compose exec -T nginx ls -la /etc/letsencrypt/live/ 2>/dev/null || true
    else
        print_error "/etc/letsencrypt directory does NOT exist"
        print_error "Volume mount is not working correctly!"
    fi
fi

# Check 4: Verify certificate details
print_header "4. Certificate Details"

if docker-compose exec -T nginx test -f "$CERT_PATH/fullchain.pem" 2>/dev/null; then
    echo "Certificate information:"
    echo ""
    
    # Get certificate subject (CN)
    CERT_SUBJECT=$(docker-compose exec -T nginx openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -subject 2>/dev/null || echo "Unable to read")
    echo "Subject: $CERT_SUBJECT"
    
    # Get certificate issuer
    CERT_ISSUER=$(docker-compose exec -T nginx openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -issuer 2>/dev/null || echo "Unable to read")
    echo "Issuer: $CERT_ISSUER"
    
    # Check if it's a Let's Encrypt certificate
    if echo "$CERT_ISSUER" | grep -qi "Let's Encrypt"; then
        if echo "$CERT_ISSUER" | grep -qi "Staging"; then
            print_warning "This is a STAGING certificate (not trusted by browsers)"
            echo "  To get a production certificate, run:"
            echo "  docker-compose down && ./bootstrap-ssl.sh --email your-email@example.com"
        else
            print_success "Valid Let's Encrypt production certificate"
        fi
    elif echo "$CERT_ISSUER" | echo "$CERT_SUBJECT" | grep -qi "CN=$FIRST_DOMAIN"; then
        print_warning "This appears to be a self-signed certificate"
        echo "  To get a real certificate, run:"
        echo "  ./setup-ssl-certificates.sh --email your-email@example.com"
    else
        print_warning "Certificate issuer is not Let's Encrypt"
    fi
    
    echo ""
    
    # Get certificate dates
    echo "Certificate validity:"
    docker-compose exec -T nginx openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -dates 2>/dev/null || echo "Unable to read dates"
    
    echo ""
    
    # Check certificate expiration
    EXPIRY_DATE=$(docker-compose exec -T nginx openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -enddate 2>/dev/null | cut -d= -f2)
    if [ -n "$EXPIRY_DATE" ]; then
        EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || echo "0")
        CURRENT_EPOCH=$(date +%s)
        DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))
        
        if [ "$DAYS_LEFT" -lt 0 ]; then
            print_error "Certificate has EXPIRED! (expired $((- DAYS_LEFT)) days ago)"
        elif [ "$DAYS_LEFT" -lt 7 ]; then
            print_warning "Certificate expires in $DAYS_LEFT days (URGENT renewal needed)"
        elif [ "$DAYS_LEFT" -lt 30 ]; then
            print_warning "Certificate expires in $DAYS_LEFT days (renewal recommended)"
        else
            print_success "Certificate is valid for $DAYS_LEFT more days"
        fi
    fi
    
    echo ""
    
    # Check Subject Alternative Names (SAN) - which domains are covered
    echo "Domains covered by this certificate:"
    SAN_DOMAINS=$(docker-compose exec -T nginx openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -text 2>/dev/null | grep -A1 "Subject Alternative Name" | tail -n1 | sed 's/DNS://g' | tr ',' '\n' || echo "Unable to read")
    
    if [ -n "$SAN_DOMAINS" ]; then
        echo "$SAN_DOMAINS" | while read -r domain; do
            domain=$(echo "$domain" | xargs)  # trim whitespace
            if [ -n "$domain" ]; then
                echo "  - $domain"
            fi
        done
        
        # Verify all required domains are covered
        echo ""
        echo "Verifying domain coverage:"
        for domain in $DOMAINS; do
            if echo "$SAN_DOMAINS" | grep -qi "$domain"; then
                print_success "$domain is covered"
            else
                print_error "$domain is NOT covered"
            fi
        done
    else
        print_warning "Could not read Subject Alternative Names"
    fi
else
    print_error "Cannot read certificate details - file not found"
fi

# Check 5: Verify nginx configuration references correct paths
print_header "5. Nginx Configuration"

echo "Checking SSL certificate paths in nginx configuration..."
echo ""

CONFIG_PATHS=$(docker-compose exec -T nginx cat /etc/nginx/conf.d/default.conf 2>/dev/null | grep "ssl_certificate" || echo "")

if [ -n "$CONFIG_PATHS" ]; then
    echo "SSL certificate directives found in configuration:"
    echo "$CONFIG_PATHS"
    echo ""
    
    # Check if all paths use the same certificate
    UNIQUE_CERT_PATHS=$(echo "$CONFIG_PATHS" | grep "ssl_certificate " | grep -v "ssl_certificate_key" | awk '{print $2}' | tr -d ';' | sort -u)
    UNIQUE_KEY_PATHS=$(echo "$CONFIG_PATHS" | grep "ssl_certificate_key" | awk '{print $2}' | tr -d ';' | sort -u)
    
    NUM_CERT_PATHS=$(echo "$UNIQUE_CERT_PATHS" | wc -l)
    NUM_KEY_PATHS=$(echo "$UNIQUE_KEY_PATHS" | wc -l)
    
    if [ "$NUM_CERT_PATHS" -eq 1 ]; then
        print_success "All server blocks use the same certificate path"
        echo "  Certificate: $UNIQUE_CERT_PATHS"
    else
        print_warning "Multiple certificate paths found:"
        echo "$UNIQUE_CERT_PATHS"
    fi
    
    if [ "$NUM_KEY_PATHS" -eq 1 ]; then
        print_success "All server blocks use the same key path"
        echo "  Key: $UNIQUE_KEY_PATHS"
    else
        print_warning "Multiple key paths found:"
        echo "$UNIQUE_KEY_PATHS"
    fi
    
    # Verify the configured paths exist
    echo ""
    echo "Verifying configured certificate paths exist:"
    for cert_path in $UNIQUE_CERT_PATHS; do
        if docker-compose exec -T nginx test -f "$cert_path" 2>/dev/null; then
            print_success "Found: $cert_path"
        else
            print_error "Missing: $cert_path"
        fi
    done
    
    for key_path in $UNIQUE_KEY_PATHS; do
        if docker-compose exec -T nginx test -f "$key_path" 2>/dev/null; then
            print_success "Found: $key_path"
        else
            print_error "Missing: $key_path"
        fi
    done
else
    print_error "No SSL certificate directives found in nginx configuration"
fi

echo ""
echo "Testing nginx configuration syntax..."
if docker-compose exec -T nginx nginx -t 2>&1; then
    print_success "Nginx configuration is valid"
else
    print_error "Nginx configuration has errors"
fi

# Check 6: Compare certbot and nginx volumes
print_header "6. Volume Configuration"

echo "Checking docker-compose volume mounts..."
echo ""

# Extract nginx volumes
echo "Nginx container volumes:"
grep -A 10 "  nginx:" /home/runner/work/hanna/hanna/docker-compose.yml | grep -E "^\s+- " | grep "letsencrypt" || echo "  No letsencrypt volumes found"

echo ""
echo "Certbot container volumes:"
grep -A 10 "  certbot:" /home/runner/work/hanna/hanna/docker-compose.yml | grep -E "^\s+- " | grep "letsencrypt" || echo "  No letsencrypt volumes found"

echo ""

# Check volume names
NGINX_VOLUME=$(grep -A 10 "  nginx:" /home/runner/work/hanna/hanna/docker-compose.yml | grep "letsencrypt:" | awk '{print $2}' | cut -d: -f1 || echo "")
CERTBOT_VOLUME=$(grep -A 10 "  certbot:" /home/runner/work/hanna/hanna/docker-compose.yml | grep "letsencrypt:" | awk '{print $2}' | cut -d: -f1 || echo "")

if [ "$NGINX_VOLUME" = "$CERTBOT_VOLUME" ]; then
    print_success "Nginx and certbot use the same volume: $NGINX_VOLUME"
else
    print_error "Nginx and certbot use DIFFERENT volumes!"
    echo "  Nginx: $NGINX_VOLUME"
    echo "  Certbot: $CERTBOT_VOLUME"
    echo ""
    echo "This is a critical issue! Certificates from certbot won't be accessible to nginx."
fi

# Check 7: Test HTTPS connection
print_header "7. Live HTTPS Test"

for domain in $DOMAINS; do
    echo "Testing HTTPS connection to $domain..."
    
    # Test with curl (accepts any certificate)
    HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://$domain 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        print_success "HTTPS responds with HTTP $HTTP_CODE"
    else
        print_error "HTTPS connection failed (HTTP $HTTP_CODE)"
    fi
    
    # Test certificate with openssl (verifies trust)
    if timeout 5 echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | openssl x509 -noout -subject 2>/dev/null; then
        print_success "SSL certificate is served correctly"
    else
        print_warning "Could not verify SSL certificate from external connection"
    fi
    
    echo ""
done

# Summary and Recommendations
print_header "Summary and Recommendations"

echo "Certificate Status:"
if docker-compose exec -T nginx test -f "$CERT_PATH/fullchain.pem" 2>/dev/null; then
    echo "  ✓ Certificate files exist"
    
    CERT_ISSUER=$(docker-compose exec -T nginx openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -issuer 2>/dev/null || echo "")
    
    if echo "$CERT_ISSUER" | grep -qi "Let's Encrypt" && ! echo "$CERT_ISSUER" | grep -qi "Staging"; then
        echo "  ✓ Valid Let's Encrypt production certificate"
    elif echo "$CERT_ISSUER" | grep -qi "Staging"; then
        echo "  ⚠ Using STAGING certificate (causes browser warnings)"
        echo ""
        echo "RECOMMENDED ACTION:"
        echo "  Obtain production certificates:"
        echo "    docker-compose down"
        echo "    ./bootstrap-ssl.sh --email your-email@example.com"
    else
        echo "  ⚠ Using self-signed or non-standard certificate"
        echo ""
        echo "RECOMMENDED ACTION:"
        echo "  Obtain Let's Encrypt certificates:"
        echo "    ./setup-ssl-certificates.sh --email your-email@example.com"
    fi
else
    echo "  ✗ Certificate files are missing"
    echo ""
    echo "REQUIRED ACTION:"
    echo "  Obtain SSL certificates:"
    echo "    ./bootstrap-ssl.sh --email your-email@example.com"
fi

echo ""
echo "For more detailed diagnostics, run: ./diagnose-ssl.sh"
echo "For SSL troubleshooting, run: ./troubleshoot-ssl-warnings.sh"
echo ""
