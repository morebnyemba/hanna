#!/bin/bash

# Certificate Path Fix Script
# This script detects and fixes certificate path issues in nginx configuration

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Certificate Path Fix Script                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
DOMAINS="dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
EXPECTED_CERT_NAME="dashboard.hanna.co.zw"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check prerequisites
if ! docker-compose ps nginx 2>/dev/null | grep -q "Up"; then
    print_error "nginx container is not running"
    echo "Start it with: docker-compose up -d nginx"
    exit 1
fi

echo "Detecting certificate directory structure..."
echo ""

# Check what certificate directories exist
CERT_DIRS=$(docker-compose exec -T nginx find /etc/letsencrypt/live -maxdepth 1 -type d 2>/dev/null | grep -v "^/etc/letsencrypt/live$" || echo "")

if [ -z "$CERT_DIRS" ]; then
    print_error "No certificate directories found in /etc/letsencrypt/live"
    echo ""
    echo "You need to obtain certificates first:"
    echo "  ./setup-ssl-certificates.sh --email your-email@example.com"
    exit 1
fi

echo "Found certificate directories:"
echo "$CERT_DIRS" | while read -r dir; do
    dir=$(basename "$dir")
    echo "  - $dir"
done
echo ""

# Determine which certificate directory to use
ACTUAL_CERT_DIR=""
ACTUAL_CERT_NAME=""

# First, check if the expected directory exists
for domain in $DOMAINS; do
    if echo "$CERT_DIRS" | grep -q "/etc/letsencrypt/live/$domain"; then
        CERT_PATH="/etc/letsencrypt/live/$domain"
        
        # Verify it has the required files
        if docker-compose exec -T nginx test -f "$CERT_PATH/fullchain.pem" 2>/dev/null && \
           docker-compose exec -T nginx test -f "$CERT_PATH/privkey.pem" 2>/dev/null; then
            
            # Check if this certificate covers all our domains
            SAN_DOMAINS=$(docker-compose exec -T nginx openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -text 2>/dev/null | \
                         grep -A1 "Subject Alternative Name" | tail -n1 | sed 's/DNS://g' | tr ',' '\n' | sed 's/^[[:space:]]*//' || echo "")
            
            COVERED_COUNT=0
            for check_domain in $DOMAINS; do
                if echo "$SAN_DOMAINS" | grep -qi "^$check_domain$"; then
                    COVERED_COUNT=$((COVERED_COUNT + 1))
                fi
            done
            
            if [ "$COVERED_COUNT" -eq 3 ]; then
                ACTUAL_CERT_DIR="$CERT_PATH"
                ACTUAL_CERT_NAME="$domain"
                print_success "Found valid SAN certificate at: $CERT_PATH"
                echo "  Covers all $COVERED_COUNT required domains"
                break
            elif [ -z "$ACTUAL_CERT_DIR" ]; then
                # Use as fallback if no better certificate found
                ACTUAL_CERT_DIR="$CERT_PATH"
                ACTUAL_CERT_NAME="$domain"
                print_warning "Found certificate at $CERT_PATH but it only covers $COVERED_COUNT/$(($(echo $DOMAINS | wc -w))) domains"
            fi
        fi
    fi
done

if [ -z "$ACTUAL_CERT_DIR" ]; then
    print_error "No valid certificate directory found with required files"
    echo ""
    echo "Expected to find fullchain.pem and privkey.pem in one of these locations:"
    for domain in $DOMAINS; do
        echo "  - /etc/letsencrypt/live/$domain/"
    done
    echo ""
    echo "Obtain certificates with:"
    echo "  ./setup-ssl-certificates.sh --email your-email@example.com"
    exit 1
fi

echo ""
echo "Certificate Analysis:"
echo "  Using: $ACTUAL_CERT_DIR"
echo ""

# Show which domains are covered
echo "Domains covered by certificate:"
SAN_DOMAINS=$(docker-compose exec -T nginx openssl x509 -in "$ACTUAL_CERT_DIR/fullchain.pem" -noout -text 2>/dev/null | \
             grep -A1 "Subject Alternative Name" | tail -n1 | sed 's/DNS://g' | tr ',' '\n' | sed 's/^[[:space:]]*//' || echo "")

for domain in $DOMAINS; do
    if echo "$SAN_DOMAINS" | grep -qi "^$domain$"; then
        print_success "$domain"
    else
        print_error "$domain (NOT COVERED)"
    fi
done
echo ""

# Check current nginx configuration
CURRENT_CERT_PATH=$(docker-compose exec -T nginx grep "ssl_certificate " /etc/nginx/conf.d/default.conf 2>/dev/null | \
                    grep -v "ssl_certificate_key" | head -n1 | awk '{print $2}' | tr -d ';' || echo "")

if [ -z "$CURRENT_CERT_PATH" ]; then
    print_error "Could not find ssl_certificate directive in nginx configuration"
    exit 1
fi

echo "Current nginx configuration:"
echo "  Certificate path: $CURRENT_CERT_PATH"
echo ""

# Compare paths
EXPECTED_PATH="/etc/letsencrypt/live/$EXPECTED_CERT_NAME/fullchain.pem"

if [ "$CURRENT_CERT_PATH" = "$ACTUAL_CERT_DIR/fullchain.pem" ]; then
    print_success "Nginx is already using the correct certificate path"
    echo ""
    
    # Check certificate validity
    CERT_ISSUER=$(docker-compose exec -T nginx openssl x509 -in "$ACTUAL_CERT_DIR/fullchain.pem" -noout -issuer 2>/dev/null || echo "")
    
    if echo "$CERT_ISSUER" | grep -qi "Let's Encrypt" && ! echo "$CERT_ISSUER" | grep -qi "Staging"; then
        print_success "Using valid Let's Encrypt production certificate"
    elif echo "$CERT_ISSUER" | grep -qi "Staging"; then
        print_warning "Using STAGING certificate - this causes browser warnings!"
        echo ""
        echo "RECOMMENDED ACTION:"
        echo "  Obtain production certificate:"
        echo "    docker-compose down"
        echo "    ./bootstrap-ssl.sh --email your-email@example.com"
        exit 2
    else
        print_warning "Certificate issuer: $CERT_ISSUER"
        echo ""
        echo "This may be a self-signed or non-standard certificate."
        echo "To obtain a Let's Encrypt certificate:"
        echo "  ./setup-ssl-certificates.sh --email your-email@example.com"
        exit 2
    fi
    
    echo ""
    echo "No changes needed. If you're still seeing browser warnings:"
    echo "  1. Clear browser cache"
    echo "  2. Reload nginx: docker-compose exec nginx nginx -s reload"
    echo "  3. Check certificate expiry: ./check-certificate-paths.sh"
    exit 0
else
    print_warning "Nginx configuration needs to be updated"
    echo ""
    echo "  Current: $CURRENT_CERT_PATH"
    echo "  Should be: $ACTUAL_CERT_DIR/fullchain.pem"
    echo ""
    
    # Check if actual certificate path is different from expected
    if [ "$ACTUAL_CERT_DIR" != "/etc/letsencrypt/live/$EXPECTED_CERT_NAME" ]; then
        print_warning "Certificate is in unexpected location"
        echo ""
        echo "EXPLANATION:"
        echo "  The nginx configuration expects certificates at:"
        echo "    /etc/letsencrypt/live/$EXPECTED_CERT_NAME/"
        echo ""
        echo "  But certificates are actually at:"
        echo "    $ACTUAL_CERT_DIR/"
        echo ""
        echo "This happened because certificates were obtained with a different"
        echo "primary domain name than expected."
        echo ""
        echo "SOLUTION:"
        echo "  We need to update nginx configuration to use the correct path."
        echo ""
        read -p "Do you want to update nginx configuration now? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "Updating nginx configuration..."
            
            # Backup current configuration
            docker-compose exec -T nginx cp /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.backup
            print_success "Created backup at /etc/nginx/conf.d/default.conf.backup"
            
            # Update certificate paths in configuration
            docker-compose exec -T nginx sed -i \
                "s|ssl_certificate /etc/letsencrypt/live/[^/]*/fullchain.pem;|ssl_certificate $ACTUAL_CERT_DIR/fullchain.pem;|g" \
                /etc/nginx/conf.d/default.conf
            
            docker-compose exec -T nginx sed -i \
                "s|ssl_certificate_key /etc/letsencrypt/live/[^/]*/privkey.pem;|ssl_certificate_key $ACTUAL_CERT_DIR/privkey.pem;|g" \
                /etc/nginx/conf.d/default.conf
            
            # Test configuration
            if docker-compose exec -T nginx nginx -t 2>&1; then
                print_success "Nginx configuration is valid"
                echo ""
                echo "Reloading nginx..."
                
                if docker-compose exec -T nginx nginx -s reload; then
                    print_success "Nginx reloaded successfully"
                    echo ""
                    print_success "Certificate paths have been fixed!"
                    echo ""
                    echo "Test your sites:"
                    for domain in $DOMAINS; do
                        echo "  https://$domain"
                    done
                else
                    print_error "Failed to reload nginx"
                    echo "Restoring backup..."
                    docker-compose exec -T nginx mv /etc/nginx/conf.d/default.conf.backup /etc/nginx/conf.d/default.conf
                    exit 1
                fi
            else
                print_error "Nginx configuration test failed"
                echo "Restoring backup..."
                docker-compose exec -T nginx mv /etc/nginx/conf.d/default.conf.backup /etc/nginx/conf.d/default.conf
                exit 1
            fi
        else
            echo ""
            echo "No changes made."
            echo ""
            echo "To fix manually, update these lines in nginx_proxy/nginx.conf:"
            echo "  ssl_certificate $ACTUAL_CERT_DIR/fullchain.pem;"
            echo "  ssl_certificate_key $ACTUAL_CERT_DIR/privkey.pem;"
            echo ""
            echo "Then run:"
            echo "  docker-compose restart nginx"
            exit 0
        fi
    fi
fi

echo ""
print_success "Certificate configuration verified successfully"
echo ""
