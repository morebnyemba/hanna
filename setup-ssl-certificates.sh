#!/bin/bash

# SSL Certificate Setup Script
# This script obtains initial SSL certificates for the HANNA application

set -e

echo "=== HANNA SSL Certificate Setup ==="
echo ""

# Configuration
DOMAINS="dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
EMAIL="your-email@example.com"  # Change this to your actual email address
STAGING=false  # Set to true for testing with Let's Encrypt staging server

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
            echo "Usage: ./setup-ssl-certificates.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --staging          Use Let's Encrypt staging server (for testing)"
            echo "  --email EMAIL      Email address for Let's Encrypt notifications"
            echo "  --domains DOMAINS  Space-separated list of domains (default: dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw)"
            echo "  --help             Show this help message"
            echo ""
            echo "Example:"
            echo "  ./setup-ssl-certificates.sh --email admin@example.com --domains \"example.com www.example.com\""
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
    echo "ERROR: Please specify your email address with --email"
    echo "Example: ./setup-ssl-certificates.sh --email admin@example.com"
    exit 1
fi

echo "Configuration:"
echo "  Domains: $DOMAINS"
echo "  Email: $EMAIL"
echo "  Staging: $STAGING"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed or not in PATH"
    exit 1
fi

# Extract first domain for certificate path
FIRST_DOMAIN=$(echo $DOMAINS | awk '{print $1}')

# Check if nginx container is running
NGINX_STATUS=$(docker-compose ps nginx 2>/dev/null || echo "")

if echo "$NGINX_STATUS" | grep -q "Restarting"; then
    echo "ERROR: nginx container is in a restart loop"
    echo "This usually means nginx cannot load SSL certificate files."
    echo ""
    echo "Stopping nginx to fix..."
    docker-compose stop nginx
    echo ""
fi

if ! docker-compose ps nginx | grep -q "Up"; then
    echo "WARNING: nginx container is not running"
    echo ""
    
    # Check if certificates exist at all
    if ! docker-compose run --rm --entrypoint sh certbot -c "test -f /etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem" 2>/dev/null; then
        echo "No certificates found. Running SSL initialization first..."
        echo ""
        
        # Run initialization script to create temporary certificates
        if [ -f "./init-ssl.sh" ]; then
            SSL_DOMAINS="$DOMAINS" ./init-ssl.sh
        else
            echo "WARNING: init-ssl.sh not found, creating temporary certificates manually..."
            docker-compose run --rm --entrypoint sh certbot -c "
                set -e
                mkdir -p /var/www/letsencrypt/.well-known/acme-challenge
                mkdir -p /etc/letsencrypt/live/$FIRST_DOMAIN
                # Set proper permissions for ACME challenge directory
                chmod -R 755 /var/www/letsencrypt
                
                # Generate self-signed certificate (suppress non-error output)
                if openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
                    -keyout /etc/letsencrypt/live/$FIRST_DOMAIN/privkey.pem \
                    -out /etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem \
                    -subj '/CN=$FIRST_DOMAIN' 2>/dev/null; then
                    echo 'Temporary certificate created successfully'
                else
                    echo 'ERROR: Failed to generate temporary certificate'
                    exit 1
                fi
                
                # Ensure certificate files have proper permissions
                chmod 644 /etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem
                chmod 600 /etc/letsencrypt/live/$FIRST_DOMAIN/privkey.pem
            "
            echo "✓ Temporary certificates created"
        fi
        
        echo ""
        echo "Starting nginx with temporary certificates..."
        docker-compose up -d nginx
        echo ""
        
        # Wait for nginx to start
        sleep 5
        
        if ! docker-compose ps nginx | grep -q "Up"; then
            echo "ERROR: nginx failed to start even with temporary certificates"
            echo "Please check nginx logs: docker-compose logs nginx"
            exit 1
        fi
        
        echo "✓ nginx started successfully"
        echo ""
    else
        echo "Certificates exist but nginx is not running. Starting nginx..."
        docker-compose up -d nginx
        sleep 5
        
        if ! docker-compose ps nginx | grep -q "Up"; then
            echo "ERROR: nginx failed to start"
            echo "Please check nginx logs: docker-compose logs nginx"
            exit 1
        fi
    fi
fi

echo "Step 1: Ensuring webroot directory exists for ACME challenge..."
docker-compose exec -T nginx mkdir -p /var/www/letsencrypt 2>/dev/null || \
    docker-compose run --rm --entrypoint sh certbot -c "mkdir -p /var/www/letsencrypt"
echo "✓ Webroot directory ready"
echo ""

# Build certbot command
# Use --force-renewal to replace any existing certificates (including temporary self-signed ones)
# Use --expand to allow adding more domains to existing certificate
CERTBOT_CMD="certonly --webroot -w /var/www/letsencrypt --email $EMAIL --agree-tos --no-eff-email --force-renewal --expand"

if [ "$STAGING" = true ]; then
    CERTBOT_CMD="$CERTBOT_CMD --staging"
    echo "WARNING: Using Let's Encrypt staging server (certificates will not be trusted)"
    echo ""
fi

# Add domains
for domain in $DOMAINS; do
    CERTBOT_CMD="$CERTBOT_CMD -d $domain"
done

echo "Step 2: Obtaining SSL certificates from Let's Encrypt..."
echo "This may take a few minutes..."
echo ""

# Run certbot to obtain certificates using a separate one-off container
# This avoids interference with the renewal service container
if docker-compose run --rm --entrypoint certbot certbot $CERTBOT_CMD; then
    echo ""
    echo "✓ SSL certificates obtained successfully!"
    echo ""
    
    echo "Step 3: Restarting nginx to load new certificates..."
    docker-compose restart nginx
    echo "✓ nginx restarted"
    echo ""
    
    echo "=== Setup Complete ==="
    echo ""
    echo "SSL certificates have been obtained and installed for:"
    for domain in $DOMAINS; do
        echo "  - https://$domain"
    done
    echo ""
    echo "Certificates will be automatically renewed by the certbot container."
    echo ""
    echo "To verify your setup, visit the domains listed above."
else
    echo ""
    echo "ERROR: Failed to obtain SSL certificates"
    echo ""
    echo "Common issues:"
    echo "  1. DNS records not pointing to this server"
    echo "  2. Port 80 not accessible from the internet"
    echo "  3. Firewall blocking incoming connections"
    echo "  4. Domain already has certificates (use --force-renewal)"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check DNS: dig dashboard.hanna.co.zw"
    echo "  - Check port 80: curl http://dashboard.hanna.co.zw/.well-known/acme-challenge/test"
    echo "  - View nginx logs: docker-compose logs nginx"
    echo "  - View certbot logs: docker-compose logs certbot"
    echo ""
    echo "For testing, you can use the staging server:"
    echo "  ./setup-ssl-certificates.sh --staging"
    exit 1
fi
