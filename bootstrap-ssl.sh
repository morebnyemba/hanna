#!/bin/bash

# Bootstrap SSL Script
# This script handles the complete SSL setup from scratch, including:
# 1. Creating temporary self-signed certificates
# 2. Starting nginx
# 3. Obtaining real Let's Encrypt certificates
# 4. Restarting nginx with real certificates

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         HANNA SSL Certificate Bootstrap Script                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration - can be overridden via command line
DOMAINS="dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
EMAIL="your-email@example.com"  # CHANGE THIS! Must be a valid email for Let's Encrypt
STAGING=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --staging)
            STAGING=true
            shift
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --domains)
            DOMAINS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./bootstrap-ssl.sh [OPTIONS]"
            echo ""
            echo "This script performs a complete SSL setup from scratch:"
            echo "  1. Creates temporary self-signed certificates"
            echo "  2. Starts all services including nginx"
            echo "  3. Obtains real Let's Encrypt SSL certificates"
            echo "  4. Replaces temporary certificates with real ones"
            echo ""
            echo "Options:"
            echo "  --staging          Use Let's Encrypt staging server (for testing)"
            echo "  --email EMAIL      Email address for Let's Encrypt notifications"
            echo "  --domains DOMAINS  Space-separated list of domains"
            echo "  --help             Show this help message"
            echo ""
            echo "Example:"
            echo "  ./bootstrap-ssl.sh --email admin@example.com"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate email
if [ "$EMAIL" = "your-email@example.com" ]; then
    echo "✗ ERROR: Please specify your email address with --email"
    echo ""
    echo "Example: ./bootstrap-ssl.sh --email your-email@example.com"
    echo ""
    exit 1
fi

echo "Configuration:"
echo "  Domains: $DOMAINS"
echo "  Email: $EMAIL"
echo "  Staging: $STAGING"
echo ""

# Check prerequisites
echo "═══ Checking Prerequisites ═══"
echo ""

if ! command -v docker-compose &> /dev/null; then
    echo "✗ ERROR: docker-compose is not installed"
    exit 1
fi
echo "✓ docker-compose is available"

if ! command -v docker &> /dev/null; then
    echo "✗ ERROR: docker is not installed"
    exit 1
fi
echo "✓ docker is available"

echo ""

# Step 1: Stop any running containers to start fresh
echo "═══ Step 1: Stopping existing containers ═══"
echo ""

if docker-compose ps -q | grep -q .; then
    echo "Stopping running containers..."
    docker-compose down
    echo "✓ Containers stopped"
else
    echo "No running containers found"
fi
echo ""

# Step 2: Initialize SSL with temporary certificates
echo "═══ Step 2: Creating temporary SSL certificates ═══"
echo ""
echo "Creating temporary self-signed certificates to allow nginx to start..."

# Ensure certbot service is available (pull image if needed)
echo "Pulling certbot image if needed..."
docker-compose pull certbot 2>&1 | grep -v "Pulling" || true

# Create temporary certificates
FIRST_DOMAIN=$(echo $DOMAINS | awk '{print $1}')
CERT_DIR="/etc/letsencrypt/live/$FIRST_DOMAIN"
docker-compose run --rm --entrypoint sh certbot -c "
    set -e
    echo 'Creating directory structure...'
    mkdir -p $CERT_DIR
    mkdir -p /var/www/letsencrypt/.well-known/acme-challenge
    # Set proper permissions for ACME challenge directory
    chmod -R 755 /var/www/letsencrypt
    
    echo 'Generating temporary self-signed certificate...'
    # Generate self-signed certificate (suppress non-error output)
    # Note: Variables are expanded by outer shell before being passed to docker
    # The escaped quotes ensure proper DN format handling in openssl
    if openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout $CERT_DIR/privkey.pem \
        -out $CERT_DIR/fullchain.pem \
        -subj \"/CN=$FIRST_DOMAIN\" 2>/dev/null; then
        echo 'Temporary certificate created successfully'
    else
        echo 'ERROR: Failed to generate temporary certificate'
        exit 1
    fi
    
    # Ensure certificate files have proper permissions
    chmod 644 $CERT_DIR/fullchain.pem
    chmod 600 $CERT_DIR/privkey.pem
"

echo "✓ Temporary certificates created"
echo "✓ ACME challenge directory created"
echo ""

# Step 3: Start all services
echo "═══ Step 3: Starting all services ═══"
echo ""

docker-compose up -d

echo ""
echo "Waiting for services to be healthy..."

# Configuration for nginx startup checks
NGINX_STARTUP_WAIT=5  # Initial wait before checking nginx status
NGINX_RETRY_INTERVAL=5  # Seconds between retries
MAX_NGINX_RETRIES=12  # Maximum number of retries (12 * 5 = 60 seconds max)

sleep $NGINX_STARTUP_WAIT

# Check if nginx is running (with retries for transient startup issues)
NGINX_RETRIES=0
while [ $NGINX_RETRIES -lt $MAX_NGINX_RETRIES ]; do
    if docker-compose ps nginx | grep -q "Up"; then
        echo "✓ nginx is running"
        break
    elif docker-compose ps nginx | grep -q "Restarting"; then
        echo "⚠ nginx is restarting (attempt $((NGINX_RETRIES + 1))/$MAX_NGINX_RETRIES)..."
        sleep $NGINX_RETRY_INTERVAL
        NGINX_RETRIES=$((NGINX_RETRIES + 1))
    else
        echo "✗ nginx failed to start"
        echo ""
        echo "Checking logs..."
        docker-compose logs --tail=30 nginx
        echo ""
        echo "Please check the error above and try again"
        exit 1
    fi
done

if [ $NGINX_RETRIES -eq $MAX_NGINX_RETRIES ]; then
    echo "✗ nginx failed to start after $MAX_NGINX_RETRIES attempts"
    echo ""
    echo "Checking logs..."
    docker-compose logs --tail=30 nginx
    echo ""
    echo "Common issues:"
    echo "  - Missing SSL configuration files"
    echo "  - Invalid nginx configuration syntax"
    echo "  - Port already in use"
    echo ""
    exit 1
fi

echo ""

# Step 4: Obtain real SSL certificates
echo "═══ Step 4: Obtaining real SSL certificates ═══"
echo ""
echo "Requesting SSL certificates from Let's Encrypt..."
echo "This may take a few minutes..."
echo ""

# Build certbot command
# Use --force-renewal to replace any existing certificates (including temporary self-signed ones)
# Use --expand to allow adding more domains to existing certificate
CERTBOT_CMD="certonly --webroot -w /var/www/letsencrypt --email $EMAIL --agree-tos --no-eff-email --force-renewal --expand"

if [ "$STAGING" = true ]; then
    CERTBOT_CMD="$CERTBOT_CMD --staging"
    echo "⚠ WARNING: Using Let's Encrypt staging server"
    echo "           Certificates will not be trusted by browsers"
    echo ""
fi

# Add domains
for domain in $DOMAINS; do
    CERTBOT_CMD="$CERTBOT_CMD -d $domain"
done

# Run certbot to obtain certificates using a separate one-off container
# This avoids interference with the renewal service container
if docker-compose run --rm --entrypoint certbot certbot $CERTBOT_CMD; then
    echo ""
    echo "✓ SSL certificates obtained successfully!"
else
    echo ""
    echo "✗ Failed to obtain SSL certificates"
    echo ""
    echo "Common issues:"
    echo "  1. DNS records not pointing to this server"
    echo "  2. Firewall blocking port 80 or 443"
    echo "  3. Domain already has rate-limited certificates"
    echo ""
    echo "The temporary certificates are still in place, so nginx should"
    echo "continue running (with browser warnings about untrusted certificates)."
    echo ""
    echo "Troubleshooting:"
    echo "  - Verify DNS: dig dashboard.hanna.co.zw"
    echo "  - Test HTTP access: curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test"
    echo "  - Check nginx logs: docker-compose logs nginx"
    echo "  - Try with staging: ./bootstrap-ssl.sh --staging"
    exit 1
fi

echo ""

# Step 5: Restart nginx to load new certificates
echo "═══ Step 5: Activating SSL certificates ═══"
echo ""

docker-compose restart nginx
sleep 5

if docker-compose ps nginx | grep -q "Up"; then
    echo "✓ nginx restarted successfully"
else
    echo "✗ nginx failed to restart"
    echo "Please check logs: docker-compose logs nginx"
    exit 1
fi

echo ""

# Step 6: Verify setup
echo "═══ Step 6: Verifying SSL setup ═══"
echo ""

FIRST_DOMAIN=$(echo $DOMAINS | awk '{print $1}')

# Check if certificates are valid
if docker-compose exec -T certbot certbot certificates 2>/dev/null | grep -q "Certificate Name"; then
    echo "Certificate details:"
    docker-compose exec -T certbot certbot certificates | grep -A 5 "Certificate Name"
else
    echo "⚠ Could not retrieve certificate details"
fi

echo ""

# Final success message
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  ✓ SSL Setup Complete!                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Your domains are now secured with SSL certificates:"
for domain in $DOMAINS; do
    echo "  ✓ https://$domain"
done
echo ""
echo "Certificates will be automatically renewed by the certbot container."
echo ""
echo "To verify your setup:"
echo "  1. Visit the domains listed above in your browser"
echo "  2. Run diagnostics: ./diagnose-ssl.sh"
echo "  3. Check certificate expiry: docker-compose exec certbot certbot certificates"
echo ""
echo "Useful commands:"
echo "  - View nginx logs: docker-compose logs nginx"
echo "  - View certbot logs: docker-compose logs certbot"
echo "  - Restart services: docker-compose restart"
echo "  - Stop services: docker-compose down"
echo ""
