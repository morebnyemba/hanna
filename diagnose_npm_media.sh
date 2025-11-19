#!/bin/bash

# NPM Media Files Diagnostic Script
# This script helps diagnose why media files are not accessible via NPM

set -e

echo "=========================================="
echo "NPM Media Files Diagnostic"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found${NC}"
    exit 1
fi

echo "1. Checking Docker containers..."
echo "-----------------------------------"

# Check if containers are running
BACKEND_RUNNING=$(docker-compose ps -q backend 2>/dev/null)
NPM_RUNNING=$(docker-compose ps -q npm 2>/dev/null)

if [ -z "$BACKEND_RUNNING" ]; then
    echo -e "${RED}✗ Backend container is not running${NC}"
    BACKEND_OK=false
else
    echo -e "${GREEN}✓ Backend container is running${NC}"
    BACKEND_OK=true
fi

if [ -z "$NPM_RUNNING" ]; then
    echo -e "${RED}✗ NPM container is not running${NC}"
    NPM_OK=false
else
    echo -e "${GREEN}✓ NPM container is running${NC}"
    NPM_OK=true
fi

echo ""
echo "2. Checking media files in backend container..."
echo "------------------------------------------------"

if [ "$BACKEND_OK" = true ]; then
    # Check if mediafiles directory exists
    if docker-compose exec -T backend test -d /app/mediafiles 2>/dev/null; then
        echo -e "${GREEN}✓ /app/mediafiles directory exists${NC}"
        
        # List files
        echo "  Files in /app/mediafiles:"
        docker-compose exec -T backend ls -lah /app/mediafiles 2>/dev/null | tail -n +4 | while read line; do
            echo "    $line"
        done
        
        # Check test file
        if docker-compose exec -T backend test -f /app/mediafiles/docker-test.txt 2>/dev/null; then
            echo -e "${GREEN}✓ Test file exists: /app/mediafiles/docker-test.txt${NC}"
            echo "  Content:"
            docker-compose exec -T backend cat /app/mediafiles/docker-test.txt 2>/dev/null | while read line; do
                echo "    $line"
            done
        else
            echo -e "${YELLOW}⚠ Test file not found: /app/mediafiles/docker-test.txt${NC}"
            echo "  Creating test file..."
            docker-compose exec -T backend sh -c "echo 'Test media file from Docker' > /app/mediafiles/docker-test.txt"
            echo -e "${GREEN}✓ Test file created${NC}"
        fi
    else
        echo -e "${RED}✗ /app/mediafiles directory does not exist${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping backend checks (container not running)${NC}"
fi

echo ""
echo "3. Checking media files in NPM container..."
echo "--------------------------------------------"

if [ "$NPM_OK" = true ]; then
    # Check if media directory exists
    if docker-compose exec -T npm test -d /srv/www/media 2>/dev/null; then
        echo -e "${GREEN}✓ /srv/www/media directory exists${NC}"
        
        # List files
        echo "  Files in /srv/www/media:"
        docker-compose exec -T npm ls -lah /srv/www/media 2>/dev/null | tail -n +4 | while read line; do
            echo "    $line"
        done
        
        # Check test file
        if docker-compose exec -T npm test -f /srv/www/media/docker-test.txt 2>/dev/null; then
            echo -e "${GREEN}✓ Test file exists: /srv/www/media/docker-test.txt${NC}"
            
            # Check permissions
            PERMS=$(docker-compose exec -T npm stat -c '%a' /srv/www/media/docker-test.txt 2>/dev/null)
            if [ ! -z "$PERMS" ]; then
                echo "  Permissions: $PERMS"
                if [ "$PERMS" -ge 644 ]; then
                    echo -e "${GREEN}✓ File is readable${NC}"
                else
                    echo -e "${RED}✗ File permissions too restrictive${NC}"
                fi
            fi
            
            # Check file content
            echo "  Content:"
            docker-compose exec -T npm cat /srv/www/media/docker-test.txt 2>/dev/null | while read line; do
                echo "    $line"
            done
        else
            echo -e "${RED}✗ Test file not found in NPM: /srv/www/media/docker-test.txt${NC}"
            echo -e "${YELLOW}  This suggests the volume is not properly shared${NC}"
        fi
    else
        echo -e "${RED}✗ /srv/www/media directory does not exist in NPM${NC}"
        echo -e "${YELLOW}  This indicates the mediafiles_volume is not mounted to NPM${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping NPM checks (container not running)${NC}"
fi

echo ""
echo "4. Checking volume mounts..."
echo "-----------------------------"

if [ "$NPM_OK" = true ]; then
    echo "NPM container mounts:"
    docker inspect whatsappcrm_npm 2>/dev/null | grep -A 5 '"Mounts"' | grep -E '(Source|Destination|Type)' | head -20
    
    # Check if mediafiles_volume is mounted
    if docker inspect whatsappcrm_npm 2>/dev/null | grep -q 'mediafiles_volume'; then
        echo -e "${GREEN}✓ mediafiles_volume is mounted to NPM${NC}"
    else
        echo -e "${RED}✗ mediafiles_volume is NOT mounted to NPM${NC}"
        echo -e "${YELLOW}  Fix: Add 'mediafiles_volume:/srv/www/media' to npm service in docker-compose.yml${NC}"
    fi
fi

echo ""
echo "5. Checking NPM nginx configuration..."
echo "---------------------------------------"

if [ "$NPM_OK" = true ]; then
    # Check if custom location exists for /media
    if docker-compose exec -T npm find /data/nginx -name "*.conf" -exec grep -l "location.*media" {} \; 2>/dev/null | grep -q .; then
        echo -e "${GREEN}✓ Found nginx config with /media location${NC}"
        echo "  Configuration:"
        docker-compose exec -T npm find /data/nginx -name "*.conf" -exec grep -A 10 "location.*media" {} \; 2>/dev/null | head -20
    else
        echo -e "${RED}✗ No /media location found in nginx configs${NC}"
        echo -e "${YELLOW}  Fix: Add custom location in NPM web UI for /media path${NC}"
    fi
fi

echo ""
echo "6. Testing HTTP access..."
echo "--------------------------"

# Test local access first
if [ "$NPM_OK" = true ]; then
    echo "Testing direct file access in NPM container..."
    if docker-compose exec -T npm test -f /srv/www/media/docker-test.txt 2>/dev/null; then
        docker-compose exec -T npm cat /srv/www/media/docker-test.txt 2>/dev/null | while read line; do
            echo "  Content: $line"
        done
        echo -e "${GREEN}✓ File accessible inside NPM container${NC}"
    else
        echo -e "${RED}✗ File not accessible inside NPM container${NC}"
    fi
fi

# Test external access
echo ""
echo "Testing external HTTP access..."
echo "  Note: This requires the domain to be configured and accessible"
echo ""

# Try to detect the domain from docker-compose or env
DOMAIN="backend.hanna.co.zw"

echo "  Testing: https://$DOMAIN/media/docker-test.txt"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/media/docker-test.txt" 2>/dev/null || echo "000")

if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ HTTP 200 OK - File is accessible${NC}"
    echo "  Response content:"
    curl -s "https://$DOMAIN/media/docker-test.txt" 2>/dev/null | while read line; do
        echo "    $line"
    done
elif [ "$RESPONSE" = "404" ]; then
    echo -e "${RED}✗ HTTP 404 Not Found${NC}"
    echo -e "${YELLOW}  Possible causes:${NC}"
    echo "    - NPM custom location not configured"
    echo "    - File path mismatch"
    echo "    - Volume not mounted"
elif [ "$RESPONSE" = "403" ]; then
    echo -e "${RED}✗ HTTP 403 Forbidden${NC}"
    echo -e "${YELLOW}  Possible causes:${NC}"
    echo "    - File permissions issue"
    echo "    - Nginx configuration blocking access"
elif [ "$RESPONSE" = "502" ] || [ "$RESPONSE" = "503" ]; then
    echo -e "${RED}✗ HTTP $RESPONSE - Backend not responding${NC}"
    echo -e "${YELLOW}  Possible causes:${NC}"
    echo "    - Backend container not running"
    echo "    - Backend not accessible from NPM"
elif [ "$RESPONSE" = "000" ]; then
    echo -e "${YELLOW}⚠ Could not connect (curl error)${NC}"
    echo -e "${YELLOW}  This might be normal if running locally${NC}"
else
    echo -e "${YELLOW}⚠ HTTP $RESPONSE - Unexpected response${NC}"
fi

echo ""
echo "7. Checking NPM logs..."
echo "------------------------"

if [ "$NPM_OK" = true ]; then
    echo "Recent NPM errors (last 10 lines):"
    docker-compose logs --tail=10 npm 2>/dev/null | tail -10
    
    # Check for media-specific logs if they exist
    if docker-compose exec -T npm test -f /data/logs/media-error.log 2>/dev/null; then
        echo ""
        echo "Media error log (last 10 lines):"
        docker-compose exec -T npm tail -10 /data/logs/media-error.log 2>/dev/null || echo "  (empty)"
    fi
    
    if docker-compose exec -T npm test -f /data/logs/media-access.log 2>/dev/null; then
        echo ""
        echo "Media access log (last 10 lines):"
        docker-compose exec -T npm tail -10 /data/logs/media-access.log 2>/dev/null || echo "  (empty)"
    fi
fi

echo ""
echo "=========================================="
echo "Diagnostic Summary"
echo "=========================================="
echo ""

# Provide recommendations
echo "Recommendations:"
echo ""

if [ "$BACKEND_OK" = false ]; then
    echo -e "${RED}1. Start the backend container:${NC}"
    echo "   docker-compose up -d backend"
    echo ""
fi

if [ "$NPM_OK" = false ]; then
    echo -e "${RED}2. Start the NPM container:${NC}"
    echo "   docker-compose up -d npm"
    echo ""
fi

if [ "$NPM_OK" = true ]; then
    if ! docker inspect whatsappcrm_npm 2>/dev/null | grep -q 'mediafiles_volume'; then
        echo -e "${YELLOW}3. Volume not mounted to NPM:${NC}"
        echo "   Add to docker-compose.yml under npm service:"
        echo "     volumes:"
        echo "       - mediafiles_volume:/srv/www/media"
        echo "   Then: docker-compose up -d npm"
        echo ""
    fi
    
    if ! docker-compose exec -T npm find /data/nginx -name "*.conf" -exec grep -l "location.*media" {} \; 2>/dev/null | grep -q .; then
        echo -e "${YELLOW}4. Configure NPM custom location:${NC}"
        echo "   - Access NPM UI at http://YOUR-SERVER:81"
        echo "   - Edit backend.hanna.co.zw proxy host"
        echo "   - Add Custom Location for /media"
        echo "   - See NPM_MEDIA_FIX_GUIDE.md for details"
        echo ""
    fi
fi

if [ "$RESPONSE" != "200" ] && [ "$RESPONSE" != "000" ]; then
    echo -e "${YELLOW}5. Fix HTTP access:${NC}"
    echo "   - Verify NPM custom location configuration"
    echo "   - Check NPM logs: docker-compose logs npm"
    echo "   - Restart NPM: docker-compose restart npm"
    echo ""
fi

echo "For detailed fix instructions, see:"
echo "  - NPM_MEDIA_FIX_GUIDE.md"
echo "  - NPM_MEDIA_CONFIGURATION.md"
echo ""
echo "=========================================="
