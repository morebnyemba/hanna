#!/bin/bash

# SSL Browser Warning Troubleshooting Script
# This script helps diagnose and fix SSL certificate issues that cause browser warnings

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        SSL Browser Warning Troubleshooting Tool               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
DOMAINS="dashboard.hanna.co.zw backend.hanna.co.zw hanna.co.zw"
FIRST_DOMAIN=$(echo $DOMAINS | awk '{print $1}')

# Function to print section header
print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

print_header "1. Checking Certificate Type"

# Check if nginx is running
if ! docker-compose ps nginx | grep -q "Up"; then
    echo "✗ nginx is not running"
    echo "  Start it with: docker-compose up -d nginx"
    exit 1
fi

echo "Analyzing certificate issuer..."
CERT_INFO=$(docker-compose exec -T nginx openssl x509 -in /etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem -noout -issuer -subject -dates 2>/dev/null || echo "ERROR")

if [ "$CERT_INFO" = "ERROR" ]; then
    echo "✗ Could not read certificate file"
    echo "  The certificate might be missing or corrupted."
    echo ""
    echo "  FIX: Run ./bootstrap-ssl.sh --email your-email@example.com"
    exit 1
fi

echo "$CERT_INFO"
echo ""

# Check certificate type
if echo "$CERT_INFO" | grep -qi "Let's Encrypt.*Staging"; then
    echo "⚠ ISSUE FOUND: Using Let's Encrypt STAGING certificate"
    echo ""
    echo "  Staging certificates are for testing only and are not trusted by browsers."
    echo "  This is why you see browser warnings."
    echo ""
    echo "  FIX:"
    echo "    1. Stop all services: docker-compose down -v"
    echo "    2. Run bootstrap WITHOUT --staging flag:"
    echo "       ./bootstrap-ssl.sh --email your-email@example.com"
    echo ""
    exit 0
elif echo "$CERT_INFO" | grep -qi "Let's Encrypt"; then
    echo "✓ Valid Let's Encrypt production certificate"
elif echo "$CERT_INFO" | grep -qi "CN=$FIRST_DOMAIN.*issuer.*CN=$FIRST_DOMAIN"; then
    echo "⚠ ISSUE FOUND: Using self-signed certificate"
    echo ""
    echo "  Self-signed certificates are not trusted by browsers."
    echo "  This is typically a temporary certificate used during setup."
    echo ""
    echo "  FIX:"
    echo "    Run: ./setup-ssl-certificates.sh --email your-email@example.com"
    echo ""
    exit 0
else
    echo "⚠ Unknown certificate type"
    echo "  Check the certificate details above."
fi

print_header "2. Checking Certificate Validity Dates"

CERT_DATES=$(echo "$CERT_INFO" | grep -E "notBefore|notAfter")
echo "$CERT_DATES"
echo ""

# Check if certificate is expired
NOT_AFTER=$(echo "$CERT_DATES" | grep "notAfter" | cut -d= -f2)
if [ -n "$NOT_AFTER" ]; then
    EXPIRY_EPOCH=$(date -d "$NOT_AFTER" +%s 2>/dev/null || echo "0")
    CURRENT_EPOCH=$(date +%s)
    
    if [ "$EXPIRY_EPOCH" -lt "$CURRENT_EPOCH" ]; then
        echo "✗ ISSUE FOUND: Certificate has EXPIRED"
        echo ""
        echo "  FIX:"
        echo "    1. Run: docker-compose down"
        echo "    2. Run: ./bootstrap-ssl.sh --email your-email@example.com"
        exit 0
    else
        DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
        echo "✓ Certificate is valid for $DAYS_UNTIL_EXPIRY more days"
    fi
fi

print_header "3. Checking Certificate Domain Names"

echo "Checking if certificate covers all required domains..."
CERT_SANS=$(docker-compose exec -T nginx openssl x509 -in /etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem -noout -text 2>/dev/null | grep -A1 "Subject Alternative Name" | tail -1 || echo "")

if [ -n "$CERT_SANS" ]; then
    echo "Certificate covers: $CERT_SANS"
    echo ""
    
    # Check each domain
    ALL_COVERED=true
    for domain in $DOMAINS; do
        if echo "$CERT_SANS" | grep -q "$domain"; then
            echo "  ✓ $domain is covered"
        else
            echo "  ✗ $domain is NOT covered"
            ALL_COVERED=false
        fi
    done
    
    if [ "$ALL_COVERED" = false ]; then
        echo ""
        echo "⚠ ISSUE FOUND: Some domains are not covered by the certificate"
        echo ""
        echo "  FIX:"
        echo "    1. Run: docker-compose down"
        echo "    2. Run: ./bootstrap-ssl.sh --email your-email@example.com --domains \"$DOMAINS\""
        exit 0
    fi
else
    echo "⚠ Could not retrieve Subject Alternative Names"
fi

print_header "4. Checking OCSP Stapling"

echo "Testing OCSP stapling configuration..."

# Check if resolver is configured
if docker-compose exec -T nginx grep -q "resolver" /etc/nginx/conf.d/default.conf 2>/dev/null; then
    echo "✓ DNS resolver is configured for OCSP"
else
    echo "⚠ DNS resolver not found in nginx config"
    echo "  OCSP stapling might not work properly"
fi

print_header "5. Checking Nginx SSL Configuration"

echo "Testing nginx configuration..."
if docker-compose exec -T nginx nginx -t 2>&1 | grep -q "successful"; then
    echo "✓ Nginx configuration is valid"
else
    echo "✗ Nginx configuration has errors"
    docker-compose exec -T nginx nginx -t 2>&1
fi

print_header "6. Testing HTTPS Access"

echo "Testing HTTPS connectivity to your domains..."
echo ""

for domain in $DOMAINS; do
    echo "Testing $domain..."
    
    # Test HTTPS with certificate verification
    if curl -s --max-time 5 https://$domain > /dev/null 2>&1; then
        echo "  ✓ HTTPS works with valid certificate"
    else
        # Try without verification to see if it's a certificate issue
        if curl -k -s --max-time 5 https://$domain > /dev/null 2>&1; then
            echo "  ⚠ HTTPS works but certificate is not trusted"
            echo "    This confirms the browser warning issue"
        else
            echo "  ✗ Cannot connect via HTTPS"
            echo "    Check if nginx is running and ports are open"
        fi
    fi
    echo ""
done

print_header "Summary & Recommendations"

echo "If you're still seeing browser warnings after reviewing the checks above,"
echo "try these additional steps:"
echo ""
echo "1. Clear browser cache and cookies"
echo "   - Chrome: Settings → Privacy → Clear browsing data"
echo "   - Firefox: Settings → Privacy → Clear Data"
echo ""
echo "2. Wait a few minutes"
echo "   - Nginx might need time to fully reload the certificates"
echo "   - OCSP responses might be cached"
echo ""
echo "3. Force nginx to reload certificates:"
echo "   docker-compose exec nginx nginx -s reload"
echo ""
echo "4. Check if you're accessing the correct domain"
echo "   - Ensure you're using https:// (not http://)"
echo "   - Ensure the domain matches one of: $DOMAINS"
echo ""
echo "5. Test from a different device/network"
echo "   - Browser cache issues are often device-specific"
echo "   - Some networks have SSL inspection that interferes"
echo ""
echo "6. Get detailed certificate information from browser:"
echo "   - Click the padlock icon in the address bar"
echo "   - View certificate details"
echo "   - Check issuer, expiration, and domain names"
echo ""
echo "7. If all else fails, regenerate certificates:"
echo "   docker-compose down -v"
echo "   ./bootstrap-ssl.sh --email your-email@example.com"
echo ""
echo "For more help, run: ./diagnose-ssl.sh"
echo ""
