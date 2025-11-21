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
echo "Waiting for initial certificates to be created..."
WAIT_TIME=0
MAX_WAIT=300  # Wait up to 5 minutes for initial certificates

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    # Check if any certificates exist
    if certbot certificates 2>/dev/null | grep -q "Certificate Name"; then
        echo "$(date): Found existing certificates, starting renewal monitoring"
        break
    fi
    
    # If we've waited the max time, continue anyway (certificates may be set up externally)
    if [ $WAIT_TIME -ge $MAX_WAIT ]; then
        echo "$(date): No certificates found after waiting, continuing anyway"
        break
    fi
    
    echo "$(date): No certificates found yet, waiting... ($WAIT_TIME/$MAX_WAIT seconds)"
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
