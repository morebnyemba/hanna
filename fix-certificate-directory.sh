#!/bin/bash

# Certificate Directory Fix Script
# Fixes issue where nginx points to wrong certificate directory
# Works without requiring openssl in nginx container

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Certificate Directory Fix - Improved Version               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
DOMAINS="dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
EXPECTED_CERT_NAME="dashboard.hanna.co.zw"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check prerequisites
if ! docker-compose ps nginx 2>/dev/null | grep -q "Up"; then
    print_error "nginx container is not running"
    echo "Start it with: docker-compose up -d nginx"
    exit 1
fi

if ! docker-compose ps certbot 2>/dev/null | grep -q "Up"; then
    print_warning "certbot container is not running, starting it..."
    docker-compose up -d certbot
    sleep 2
fi

echo "Step 1: Detecting certificate directories..."
echo ""

# List all certificate directories (use certbot container which has better tools)
CERT_DIRS=$(docker-compose exec -T certbot find /etc/letsencrypt/live -maxdepth 1 -type d 2>/dev/null | grep -v "^/etc/letsencrypt/live$" | sort || true)

if [ -z "$CERT_DIRS" ]; then
    print_error "No certificate directories found in /etc/letsencrypt/live"
    echo ""
    echo "You need to obtain certificates first:"
    echo "  ./setup-ssl-certificates.sh --email your-email@example.com"
    exit 1
fi

echo "Found certificate directories:"
for dir in $CERT_DIRS; do
    dir_name=$(basename "$dir")
    echo "  - $dir_name"
done
echo ""

# Find the best certificate directory to use
echo "Step 2: Analyzing certificates..."
echo ""

BEST_CERT_DIR=""
BEST_CERT_NAME=""
BEST_SCORE=0

for cert_dir in $CERT_DIRS; do
    cert_name=$(basename "$cert_dir")
    
    # Skip README directories
    if [ "$cert_name" = "README" ]; then
        continue
    fi
    
    # Check if certificate files exist
    if ! docker-compose exec -T certbot test -f "$cert_dir/fullchain.pem" 2>/dev/null || \
       ! docker-compose exec -T certbot test -f "$cert_dir/privkey.pem" 2>/dev/null; then
        print_warning "Skipping $cert_name (missing certificate files)"
        continue
    fi
    
    # Calculate a score for this certificate
    score=0
    
    # Prefer the expected name without numbers
    if [ "$cert_name" = "$EXPECTED_CERT_NAME" ]; then
        score=$((score + 100))
    fi
    
    # Prefer newer certificates (higher numbers in -0001, -0002, etc.)
    if echo "$cert_name" | grep -q -- "-[0-9]\+$"; then
        cert_num=$(echo "$cert_name" | sed 's/.*-\([0-9]\+\)$/\1/')
        score=$((score + cert_num))
    fi
    
    # Check certificate validity using certbot container (has openssl)
    CERT_VALID=$(docker-compose exec -T certbot sh -c "
        if openssl x509 -in '$cert_dir/fullchain.pem' -noout -checkend 0 2>/dev/null; then
            echo 'valid'
        else
            echo 'expired'
        fi
    " 2>/dev/null || echo "unknown")
    
    if [ "$CERT_VALID" = "valid" ]; then
        score=$((score + 50))
        cert_status="${GREEN}valid${NC}"
    elif [ "$CERT_VALID" = "expired" ]; then
        cert_status="${RED}expired${NC}"
    else
        cert_status="${YELLOW}unknown${NC}"
    fi
    
    # Get certificate details
    CERT_INFO=$(docker-compose exec -T certbot openssl x509 -in "$cert_dir/fullchain.pem" -noout -subject -issuer 2>/dev/null || echo "")
    CERT_ISSUER=$(echo "$CERT_INFO" | grep "issuer" | sed 's/.*CN *= *\([^,]*\).*/\1/' || echo "Unknown")
    
    # Check if it's a staging certificate
    IS_STAGING="no"
    if echo "$CERT_ISSUER" | grep -qi "staging"; then
        IS_STAGING="yes"
        print_warning "Certificate $cert_name is a STAGING certificate (not trusted by browsers)"
    fi
    
    echo "Certificate: $cert_name"
    echo "  Status: $(echo -e $cert_status)"
    echo "  Issuer: $CERT_ISSUER"
    if [ "$IS_STAGING" = "yes" ]; then
        echo "  Type: ${YELLOW}STAGING${NC} (causes browser warnings!)"
    fi
    echo "  Score: $score"
    echo ""
    
    # Track the best certificate
    if [ $score -gt $BEST_SCORE ]; then
        BEST_SCORE=$score
        BEST_CERT_DIR="$cert_dir"
        BEST_CERT_NAME="$cert_name"
    fi
done

if [ -z "$BEST_CERT_DIR" ]; then
    print_error "No valid certificate found"
    echo ""
    echo "Obtain certificates with:"
    echo "  ./setup-ssl-certificates.sh --email your-email@example.com"
    exit 1
fi

print_success "Best certificate to use: $BEST_CERT_NAME"
echo "  Path: $BEST_CERT_DIR"
echo ""

# Check current nginx configuration
echo "Step 3: Checking nginx configuration..."
echo ""

CURRENT_CERT_PATH=$(docker-compose exec -T nginx grep "ssl_certificate " /etc/nginx/conf.d/default.conf 2>/dev/null | \
                    grep -v "ssl_certificate_key" | head -n1 | awk '{print $2}' | tr -d ';' || echo "")

if [ -z "$CURRENT_CERT_PATH" ]; then
    print_error "Could not find ssl_certificate directive in nginx configuration"
    exit 1
fi

CURRENT_CERT_DIR=$(dirname "$CURRENT_CERT_PATH")
CURRENT_CERT_NAME=$(basename "$CURRENT_CERT_DIR")

echo "Current nginx configuration:"
echo "  Certificate: $CURRENT_CERT_NAME"
echo "  Full path: $CURRENT_CERT_PATH"
echo ""

# Compare paths
if [ "$CURRENT_CERT_DIR" = "$BEST_CERT_DIR" ]; then
    print_success "Nginx is already using the correct certificate directory!"
    echo ""
    
    # Check if it's a staging certificate
    CERT_INFO=$(docker-compose exec -T certbot openssl x509 -in "$BEST_CERT_DIR/fullchain.pem" -noout -issuer 2>/dev/null || echo "")
    
    if echo "$CERT_INFO" | grep -qi "staging"; then
        print_warning "However, you are using a STAGING certificate!"
        echo ""
        echo "Staging certificates are not trusted by browsers and will show security warnings."
        echo ""
        echo "To fix this, obtain production certificates:"
        echo "  1. Stop nginx: docker-compose stop nginx"
        echo "  2. Remove staging certs: docker-compose run --rm --entrypoint sh certbot -c 'rm -rf /etc/letsencrypt/live/* /etc/letsencrypt/archive/* /etc/letsencrypt/renewal/*'"
        echo "  3. Get production certs: ./setup-ssl-certificates.sh --email your-email@example.com"
        echo ""
        echo "NOTE: Make sure you're not hitting Let's Encrypt rate limits (5 certs per domain set per week)"
        exit 2
    fi
    
    print_success "Configuration is correct and using production certificates"
    echo ""
    echo "If you're still seeing browser warnings:"
    echo "  1. Clear browser cache and cookies"
    echo "  2. Try in incognito/private mode"
    echo "  3. Reload nginx: docker-compose exec nginx nginx -s reload"
    echo "  4. Restart nginx: docker-compose restart nginx"
    exit 0
fi

# Paths don't match - need to update
print_warning "Certificate directory mismatch detected!"
echo ""
echo "  Current nginx config points to: $CURRENT_CERT_NAME"
echo "  Should point to: $BEST_CERT_NAME"
echo ""

# Check if the best cert is a staging certificate
BEST_CERT_INFO=$(docker-compose exec -T certbot openssl x509 -in "$BEST_CERT_DIR/fullchain.pem" -noout -issuer 2>/dev/null || echo "")
if echo "$BEST_CERT_INFO" | grep -qi "staging"; then
    print_warning "The newer certificate ($BEST_CERT_NAME) is a STAGING certificate!"
    echo ""
    echo "STAGING certificates cause browser warnings."
    echo ""
    echo "RECOMMENDED: Obtain production certificates instead of updating to staging ones:"
    echo "  1. Stop nginx: docker-compose stop nginx"
    echo "  2. Remove all certs: docker-compose run --rm --entrypoint sh certbot -c 'rm -rf /etc/letsencrypt/live/* /etc/letsencrypt/archive/* /etc/letsencrypt/renewal/*'"
    echo "  3. Get production certs: ./setup-ssl-certificates.sh --email your-email@example.com"
    echo ""
    read -p "Do you want to update nginx to use the staging certificate anyway? (NOT RECOMMENDED) (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Follow the recommended steps above to fix this properly."
        exit 0
    fi
fi

echo "Updating nginx configuration..."
echo ""

# Detect the correct nginx config file path
# Try common locations (relative path first for portability)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/nginx_proxy/nginx.conf" ]; then
    NGINX_CONF="$SCRIPT_DIR/nginx_proxy/nginx.conf"
elif [ -f "./nginx_proxy/nginx.conf" ]; then
    NGINX_CONF="./nginx_proxy/nginx.conf"
else
    print_error "Cannot find nginx.conf in expected locations"
    echo "Expected locations:"
    echo "  - $SCRIPT_DIR/nginx_proxy/nginx.conf"
    echo "  - ./nginx_proxy/nginx.conf"
    echo ""
    echo "Please run this script from the repository root directory."
    exit 1
fi

print_info "Using nginx config: $NGINX_CONF"

# Create backup with unique timestamp and process ID to avoid collisions
BACKUP_FILE="$NGINX_CONF.backup.$(date +%Y%m%d_%H%M%S).$$"
cp "$NGINX_CONF" "$BACKUP_FILE"
print_success "Created backup at: $BACKUP_FILE"

# Update certificate paths
sed -i "s|ssl_certificate /etc/letsencrypt/live/[^/]*/fullchain.pem;|ssl_certificate $BEST_CERT_DIR/fullchain.pem;|g" "$NGINX_CONF"
sed -i "s|ssl_certificate_key /etc/letsencrypt/live/[^/]*/privkey.pem;|ssl_certificate_key $BEST_CERT_DIR/privkey.pem;|g" "$NGINX_CONF"

print_success "Updated nginx.conf"

# Apply the updated config to the running container
# Note: We update the local source file AND copy it to the container
# This ensures the fix persists across container restarts
NGINX_CONTAINER=$(docker-compose ps -q nginx)
if [ -z "$NGINX_CONTAINER" ]; then
    print_error "nginx container is not running or not found"
    echo "Start nginx with: docker-compose up -d nginx"
    exit 1
fi

# Copy the updated local config file to the container
docker cp "$NGINX_CONF" "$NGINX_CONTAINER:/etc/nginx/conf.d/default.conf"
print_success "Applied updated config to nginx container"

# Test configuration
echo ""
echo "Testing nginx configuration..."
if docker-compose exec -T nginx nginx -t 2>&1 | grep -q "successful"; then
    print_success "Nginx configuration is valid"
    echo ""
    echo "Reloading nginx..."
    
    if docker-compose exec -T nginx nginx -s reload 2>&1; then
        print_success "Nginx reloaded successfully"
        echo ""
        print_success "Certificate directory has been fixed!"
        echo ""
        echo "Updated configuration:"
        echo "  Old: $CURRENT_CERT_DIR"
        echo "  New: $BEST_CERT_DIR"
        echo ""
        echo "Test your sites:"
        for domain in $DOMAINS; do
            echo "  - https://$domain"
        done
        echo ""
        echo "If you still see browser warnings:"
        echo "  1. Clear browser cache"
        echo "  2. Wait 30 seconds for nginx to fully reload"
        echo "  3. Try in incognito/private mode"
    else
        print_error "Failed to reload nginx"
        echo "Restoring backup..."
        if [ -f "$BACKUP_FILE" ]; then
            cp "$BACKUP_FILE" "$NGINX_CONF"
            print_success "Configuration restored from backup"
        fi
        exit 1
    fi
else
    print_error "Nginx configuration test failed"
    echo "Restoring backup..."
    if [ -f "$BACKUP_FILE" ]; then
        cp "$BACKUP_FILE" "$NGINX_CONF"
        print_success "Configuration restored from backup"
    fi
    exit 1
fi

echo ""
print_info "Backup saved at: $BACKUP_FILE"
echo ""
