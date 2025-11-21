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
