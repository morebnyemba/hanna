#!/bin/bash

# Test Script for SSL Scripts
# This script validates that all SSL-related scripts are working correctly

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              SSL Scripts Validation Test                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

# Function to print test result
test_result() {
    if [ $1 -eq 0 ]; then
        echo "  ✓ PASS: $2"
        PASSED=$((PASSED + 1))
    else
        echo "  ✗ FAIL: $2"
        FAILED=$((FAILED + 1))
    fi
}

echo "Test 1: Script Syntax Validation"
echo "─────────────────────────────────"

# Test bootstrap-ssl.sh
bash -n bootstrap-ssl.sh
test_result $? "bootstrap-ssl.sh syntax"

# Test setup-ssl-certificates.sh
bash -n setup-ssl-certificates.sh
test_result $? "setup-ssl-certificates.sh syntax"

# Test init-ssl.sh
bash -n init-ssl.sh
test_result $? "init-ssl.sh syntax"

# Test certbot-renew.sh
bash -n certbot-renew.sh
test_result $? "certbot-renew.sh syntax"

# Test diagnose-ssl.sh
bash -n diagnose-ssl.sh
test_result $? "diagnose-ssl.sh syntax"

# Test troubleshoot-ssl-warnings.sh
bash -n troubleshoot-ssl-warnings.sh
test_result $? "troubleshoot-ssl-warnings.sh syntax"

echo ""
echo "Test 2: Script Help Messages"
echo "─────────────────────────────────"

# Test bootstrap-ssl.sh help
./bootstrap-ssl.sh --help > /dev/null 2>&1
test_result $? "bootstrap-ssl.sh --help works"

# Test setup-ssl-certificates.sh help
./setup-ssl-certificates.sh --help > /dev/null 2>&1
test_result $? "setup-ssl-certificates.sh --help works"

echo ""
echo "Test 3: Nginx Configuration"
echo "─────────────────────────────────"

# Check if nginx.conf has resolver configured
if grep -q "resolver.*8.8.8.8" nginx_proxy/nginx.conf; then
    test_result 0 "Nginx has external DNS resolvers configured"
else
    test_result 1 "Nginx missing external DNS resolvers"
fi

# Check if resolver_timeout is set
if grep -q "resolver_timeout" nginx_proxy/nginx.conf; then
    test_result 0 "Nginx has resolver_timeout configured"
else
    test_result 1 "Nginx missing resolver_timeout"
fi

# Check for SSL stapling configuration
if grep -q "ssl_stapling" nginx_proxy/ssl_custom/options-ssl-nginx.conf; then
    test_result 0 "SSL stapling is configured"
else
    test_result 1 "SSL stapling not configured"
fi

echo ""
echo "Test 4: File Permissions"
echo "─────────────────────────────────"

# Check if scripts are executable
[ -x bootstrap-ssl.sh ]
test_result $? "bootstrap-ssl.sh is executable"

[ -x setup-ssl-certificates.sh ]
test_result $? "setup-ssl-certificates.sh is executable"

[ -x init-ssl.sh ]
test_result $? "init-ssl.sh is executable"

[ -x diagnose-ssl.sh ]
test_result $? "diagnose-ssl.sh is executable"

[ -x troubleshoot-ssl-warnings.sh ]
test_result $? "troubleshoot-ssl-warnings.sh is executable"

echo ""
echo "Test 5: Documentation Existence"
echo "─────────────────────────────────"

[ -f SSL_BROWSER_WARNING_FIX.md ]
test_result $? "SSL_BROWSER_WARNING_FIX.md exists"

[ -f SSL_BOOTSTRAP_FIX.md ]
test_result $? "SSL_BOOTSTRAP_FIX.md exists"

[ -f SSL_SETUP_GUIDE.md ]
test_result $? "SSL_SETUP_GUIDE.md exists"

[ -f README_SSL.md ]
test_result $? "README_SSL.md exists"

echo ""
echo "Test 6: Script Content Validation"
echo "─────────────────────────────────"

# Check if bootstrap-ssl.sh uses nginx reload
if grep -q "nginx -s reload" bootstrap-ssl.sh; then
    test_result 0 "bootstrap-ssl.sh uses graceful nginx reload"
else
    test_result 1 "bootstrap-ssl.sh doesn't use graceful reload"
fi

# Check if setup-ssl-certificates.sh uses nginx reload
if grep -q "nginx -s reload" setup-ssl-certificates.sh; then
    test_result 0 "setup-ssl-certificates.sh uses graceful nginx reload"
else
    test_result 1 "setup-ssl-certificates.sh doesn't use graceful reload"
fi

# Check if bootstrap-ssl.sh has certificate verification
if grep -q "CERT_ISSUER" bootstrap-ssl.sh; then
    test_result 0 "bootstrap-ssl.sh has certificate type verification"
else
    test_result 1 "bootstrap-ssl.sh missing certificate verification"
fi

# Check if troubleshoot script checks for staging certificates
if grep -q "Staging" troubleshoot-ssl-warnings.sh; then
    test_result 0 "troubleshoot-ssl-warnings.sh checks for staging certificates"
else
    test_result 1 "troubleshoot-ssl-warnings.sh doesn't check staging"
fi

echo ""
echo "Test 7: Error Handling"
echo "─────────────────────────────────"

# Test that bootstrap fails without email
./bootstrap-ssl.sh 2>&1 | grep -q "ERROR.*email" && EXIT_CODE=0 || EXIT_CODE=1
test_result $EXIT_CODE "bootstrap-ssl.sh requires email parameter"

# Test that setup fails without email
./setup-ssl-certificates.sh 2>&1 | grep -q "ERROR.*email" && EXIT_CODE=0 || EXIT_CODE=1
test_result $EXIT_CODE "setup-ssl-certificates.sh requires email parameter"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                       Test Summary                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "  Total Tests: $((PASSED + FAILED))"
echo "  ✓ Passed: $PASSED"
echo "  ✗ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed. Please review the output above."
    exit 1
fi
