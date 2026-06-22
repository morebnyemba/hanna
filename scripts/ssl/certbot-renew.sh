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

# Configuration for certificate detection
CERT_CHECK_INTERVAL=30  # Seconds between certificate checks
MAX_CERT_WAIT=600  # Wait up to 10 minutes for initial certificates (longer for slow networks)

# Wait for initial certificates to be created before starting renewal loop
# This prevents the renewal script from interfering with initial certificate setup
echo "Waiting for valid Let's Encrypt certificates to be created..."
WAIT_TIME=0

while [ $WAIT_TIME -lt $MAX_CERT_WAIT ]; do
    # Check if certbot has any managed certificates
    # Note: Self-signed certificates created by bootstrap are NOT managed by certbot
    # and won't appear in 'certbot certificates' output, so this check is reliable
    CERT_OUTPUT=$(certbot certificates 2>/dev/null)
    
    if echo "$CERT_OUTPUT" | grep -q "Certificate Name"; then
        # Found certificates managed by certbot - these are real Let's Encrypt certs
        echo "$(date): Found certbot-managed certificates, starting renewal monitoring"
        echo "$(date): Certificate details:"
        echo "$CERT_OUTPUT" | grep -A 5 "Certificate Name" | head -6
        break
    fi
    
    # If we've waited the max time, continue anyway (certificates may be set up externally)
    if [ $WAIT_TIME -ge $MAX_CERT_WAIT ]; then
        echo "$(date): No certbot-managed certificates found after waiting $MAX_CERT_WAIT seconds"
        echo "$(date): Continuing anyway - renewal checks will be performed but may fail until certificates are obtained"
        break
    fi
    
    echo "$(date): No certbot-managed certificates found yet, waiting... ($WAIT_TIME/$MAX_CERT_WAIT seconds)"
    sleep $CERT_CHECK_INTERVAL
    WAIT_TIME=$((WAIT_TIME + CERT_CHECK_INTERVAL))
done

# Main renewal loop
while :; do
    echo "$(date): Checking for certificate renewals..."
    
    # Run certbot renewal
    if certbot renew --webroot -w /var/www/letsencrypt --quiet; then
        echo "$(date): Certificate renewal check completed successfully"
        echo "$(date): Note: If certificates were renewed, nginx should be reloaded manually"
        echo "$(date): Run: docker-compose exec nginx nginx -s reload"
    else
        echo "$(date): Certificate renewal check failed (this is normal if certificates don't need renewal yet)"
    fi
    
    # Sleep for 12 hours, but allow interruption by TERM signal
    sleep 12h & wait $!
done
