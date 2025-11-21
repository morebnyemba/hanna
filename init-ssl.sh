#!/bin/bash

# SSL Initialization Script
# This script creates temporary self-signed certificates to allow nginx to start
# before obtaining real Let's Encrypt certificates

set -e

echo "=== HANNA SSL Initialization ==="
echo ""

# Configuration - can be overridden via environment variables
DOMAINS="${SSL_DOMAINS:-dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw}"
FIRST_DOMAIN=$(echo $DOMAINS | awk '{print $1}')
CERT_DIR="/etc/letsencrypt/live/$FIRST_DOMAIN"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed or not in PATH"
    exit 1
fi

echo "Step 1: Creating ACME challenge directory..."
# Create the webroot directory in the volume
docker-compose run --rm --entrypoint sh certbot -c "mkdir -p /var/www/letsencrypt/.well-known/acme-challenge"
echo "✓ ACME challenge directory created"
echo ""

echo "Step 2: Checking for existing certificates..."
# Check if real certificates already exist
if docker-compose run --rm --entrypoint sh certbot -c "test -f $CERT_DIR/fullchain.pem" 2>/dev/null; then
    echo "✓ SSL certificates already exist, skipping initialization"
    exit 0
fi

echo "No existing certificates found."
echo ""

echo "Step 3: Creating temporary self-signed certificates..."
echo "This allows nginx to start before obtaining real Let's Encrypt certificates."
echo ""

# Create directory structure and generate self-signed certificate
docker-compose run --rm --entrypoint sh certbot -c "
    mkdir -p $CERT_DIR && \
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout $CERT_DIR/privkey.pem \
        -out $CERT_DIR/fullchain.pem \
        -subj '/CN=$FIRST_DOMAIN' && \
    echo 'Temporary self-signed certificate created'
"

echo ""
echo "✓ Temporary self-signed certificates created"
echo ""
echo "=== Initialization Complete ==="
echo ""
echo "You can now start nginx with: docker-compose up -d nginx"
echo "Then obtain real certificates with: ./setup-ssl-certificates.sh --email your-email@example.com"
echo ""
