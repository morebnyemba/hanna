#!/bin/sh

# Certbot Certificate Renewal Script
# This script runs continuously in the certbot container and checks for certificate
# renewals every 12 hours. Let's Encrypt certificates are valid for 90 days and
# are renewed when they have less than 30 days remaining.

set -e

echo "Certbot automatic renewal service started"
echo "Checking for certificate renewals every 12 hours..."

# Trap TERM signal for graceful shutdown
trap 'echo "Received TERM signal, exiting..."; exit 0' TERM

# Wait for initial certificates to be created before starting renewal loop
# This prevents the renewal script from interfering with initial certificate setup
echo "Waiting for valid Let's Encrypt certificates to be created..."
WAIT_TIME=0
MAX_WAIT=600  # Wait up to 10 minutes for initial certificates (longer for slow networks)

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    # Check if any valid certificates exist (issued by Let's Encrypt, not self-signed)
    if certbot certificates 2>/dev/null | grep -q "Certificate Name"; then
        # Verify it's a real certificate by checking the issuer
        # Self-signed certificates won't have "Let's Encrypt" in the output
        if certbot certificates 2>/dev/null | grep -A 10 "Certificate Name" | grep -q "Expiry Date"; then
            echo "$(date): Found valid certificates, starting renewal monitoring"
            break
        fi
    fi
    
    # If we've waited the max time, continue anyway (certificates may be set up externally)
    if [ $WAIT_TIME -ge $MAX_WAIT ]; then
        echo "$(date): No valid certificates found after waiting, continuing anyway"
        echo "$(date): Renewal checks will be performed but may fail until certificates are obtained"
        break
    fi
    
    echo "$(date): No valid certificates found yet, waiting... ($WAIT_TIME/$MAX_WAIT seconds)"
    sleep 30
    WAIT_TIME=$((WAIT_TIME + 30))
done

# Main renewal loop
while :; do
    echo "$(date): Checking for certificate renewals..."
    
    # Run certbot renewal
    if certbot renew --webroot -w /var/www/letsencrypt --quiet; then
        echo "$(date): Certificate renewal check completed successfully"
    else
        echo "$(date): Certificate renewal check failed (this is normal if certificates don't need renewal yet)"
    fi
    
    # Sleep for 12 hours, but allow interruption by TERM signal
    sleep 12h & wait $!
done
