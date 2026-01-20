#!/bin/bash

# Reset Redis Password Script
# This script securely rotates the Redis password across all configuration files
# and optionally restarts Docker containers to apply the changes.
#
# Usage:
#   ./reset-redis-password.sh              # Generate new password and update files
#   ./reset-redis-password.sh --restart    # Update files and restart containers
#   ./reset-redis-password.sh --password YOUR_PASSWORD  # Use custom password
#   ./reset-redis-password.sh --dry-run    # Show what would be changed without applying

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           HANNA Redis Password Reset Script                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Script directory (for relative paths)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration files to update
ROOT_ENV_FILE="$SCRIPT_DIR/.env"
BACKEND_ENV_FILE="$SCRIPT_DIR/whatsappcrm_backend/.env"
BACKEND_ENV_PROD_FILE="$SCRIPT_DIR/whatsappcrm_backend/.env.prod"

# Default options
RESTART_CONTAINERS=false
DRY_RUN=false
CUSTOM_PASSWORD=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --restart)
            RESTART_CONTAINERS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --password)
            CUSTOM_PASSWORD="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./reset-redis-password.sh [OPTIONS]"
            echo ""
            echo "This script securely rotates the Redis password across all configuration files."
            echo ""
            echo "Options:"
            echo "  --restart          Restart Docker containers after updating password"
            echo "  --dry-run          Show what would be changed without applying"
            echo "  --password PASS    Use a custom password instead of generating one"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Files that will be updated:"
            echo "  - .env (root directory - Docker Compose variables)"
            echo "  - whatsappcrm_backend/.env (development environment)"
            echo "  - whatsappcrm_backend/.env.prod (production environment)"
            echo ""
            echo "Examples:"
            echo "  ./reset-redis-password.sh                    # Generate and apply new password"
            echo "  ./reset-redis-password.sh --restart          # Generate, apply, and restart containers"
            echo "  ./reset-redis-password.sh --dry-run          # Preview changes without applying"
            echo "  ./reset-redis-password.sh --password MyPass  # Use custom password"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check prerequisites
echo "═══ Checking Prerequisites ═══"
echo ""

if ! command -v openssl &> /dev/null; then
    echo "✗ ERROR: openssl is not installed"
    echo "  Please install openssl to generate secure passwords"
    exit 1
fi
echo "✓ openssl is available"

# Check that environment files exist
MISSING_FILES=false
for env_file in "$ROOT_ENV_FILE" "$BACKEND_ENV_FILE" "$BACKEND_ENV_PROD_FILE"; do
    if [ -f "$env_file" ]; then
        echo "✓ Found: $env_file"
    else
        echo "✗ Missing: $env_file"
        MISSING_FILES=true
    fi
done

if [ "$MISSING_FILES" = true ]; then
    echo ""
    echo "✗ ERROR: Some environment files are missing"
    echo "  Please ensure all environment files exist before running this script."
    exit 1
fi

echo ""

# Generate or use custom password
if [ -n "$CUSTOM_PASSWORD" ]; then
    NEW_PASSWORD="$CUSTOM_PASSWORD"
    echo "Using custom password provided via --password"
else
    # Generate a secure 32-byte base64 password (44 characters)
    NEW_PASSWORD=$(openssl rand -base64 32)
    echo "Generated new secure password (44 characters, base64 encoded)"
fi

# Function to get current password from a file
get_current_password() {
    local file="$1"
    grep "^REDIS_PASSWORD=" "$file" 2>/dev/null | cut -d'=' -f2 | tr -d "'" | tr -d '"' || echo ""
}

# Get current password for display
CURRENT_PASSWORD=$(get_current_password "$ROOT_ENV_FILE")

echo ""
echo "═══ Password Change Details ═══"
echo ""
echo "Current Password: ${CURRENT_PASSWORD:0:8}... (truncated for security)"
echo "New Password:     ${NEW_PASSWORD:0:8}... (truncated for security)"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "═══ DRY RUN MODE - No changes will be made ═══"
    echo ""
fi

# Function to update a simple key=value in env file
update_env_var() {
    local file="$1"
    local key="$2"
    local value="$3"
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would update $key in $file"
        return 0
    fi
    
    if grep -q "^${key}=" "$file"; then
        # Escape special characters in the value for sed
        local escaped_value=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')
        sed -i "s|^${key}=.*|${key}='${escaped_value}'|" "$file"
        return 0
    else
        echo "Warning: $key not found in $file, adding it"
        echo "${key}='${value}'" >> "$file"
        return 0
    fi
}

# Function to update Redis URL in backend env files
update_redis_urls() {
    local file="$1"
    local password="$2"
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would update CELERY_BROKER_URL in $file"
        echo "[DRY RUN] Would update REDIS_URL in $file"
        return 0
    fi
    
    # Escape special characters for sed
    local escaped_password=$(printf '%s\n' "$password" | sed -e 's/[\/&]/\\&/g')
    
    # Update CELERY_BROKER_URL
    if grep -q "^CELERY_BROKER_URL=" "$file"; then
        sed -i "s|^CELERY_BROKER_URL=.*|CELERY_BROKER_URL='redis://:${escaped_password}@redis:6379/0'|" "$file"
    fi
    
    # Update REDIS_URL
    if grep -q "^REDIS_URL=" "$file"; then
        sed -i "s|^REDIS_URL=.*|REDIS_URL='redis://:${escaped_password}@redis:6379/1'|" "$file"
    fi
}

# Step 1: Update root .env file
echo "═══ Step 1: Updating Root .env File ═══"
echo ""

update_env_var "$ROOT_ENV_FILE" "REDIS_PASSWORD" "$NEW_PASSWORD"
echo "✓ Updated REDIS_PASSWORD in .env"
echo ""

# Step 2: Update backend .env file (development)
echo "═══ Step 2: Updating Backend .env File (Development) ═══"
echo ""

# Check for REDIS_PASSWORD variable (may not exist in all configurations)
if grep -q "^REDIS_PASSWORD=" "$BACKEND_ENV_FILE"; then
    update_env_var "$BACKEND_ENV_FILE" "REDIS_PASSWORD" "$NEW_PASSWORD"
    echo "✓ Updated REDIS_PASSWORD in whatsappcrm_backend/.env"
else
    echo "ℹ️  REDIS_PASSWORD not found in whatsappcrm_backend/.env (uses URL-embedded password)"
fi

# Update Redis URLs with embedded password
update_redis_urls "$BACKEND_ENV_FILE" "$NEW_PASSWORD"
echo "✓ Updated Redis URLs in whatsappcrm_backend/.env"
echo ""

# Step 3: Update backend .env.prod file (production)
echo "═══ Step 3: Updating Backend .env.prod File (Production) ═══"
echo ""

# Update REDIS_PASSWORD variable
if grep -q "^REDIS_PASSWORD=" "$BACKEND_ENV_PROD_FILE"; then
    update_env_var "$BACKEND_ENV_PROD_FILE" "REDIS_PASSWORD" "$NEW_PASSWORD"
    echo "✓ Updated REDIS_PASSWORD in whatsappcrm_backend/.env.prod"
else
    echo "⚠️  REDIS_PASSWORD not found in whatsappcrm_backend/.env.prod"
fi

# Check for uncommented CELERY_BROKER_URL and REDIS_URL (skip if commented)
if grep -q "^CELERY_BROKER_URL=" "$BACKEND_ENV_PROD_FILE"; then
    update_redis_urls "$BACKEND_ENV_PROD_FILE" "$NEW_PASSWORD"
    echo "✓ Updated Redis URLs in whatsappcrm_backend/.env.prod"
else
    echo "ℹ️  Redis URLs are commented/not set in .env.prod (uses env variable interpolation)"
fi
echo ""

# Step 4: Create backup of password for reference
echo "═══ Step 4: Creating Password Backup ═══"
echo ""

BACKUP_FILE="$SCRIPT_DIR/.redis-password-backup"
if [ "$DRY_RUN" = false ]; then
    echo "# Redis password backup - $(date)" > "$BACKUP_FILE"
    echo "# Keep this file secure and delete after noting the password" >> "$BACKUP_FILE"
    echo "REDIS_PASSWORD='$NEW_PASSWORD'" >> "$BACKUP_FILE"
    chmod 600 "$BACKUP_FILE"
    echo "✓ Password backup saved to .redis-password-backup"
    echo "  ⚠️  This file contains the password in plain text!"
    echo "  ⚠️  Delete this file after saving the password securely!"
else
    echo "[DRY RUN] Would create password backup at .redis-password-backup"
fi
echo ""

# Step 5: Restart containers if requested
if [ "$RESTART_CONTAINERS" = true ]; then
    echo "═══ Step 5: Restarting Docker Containers ═══"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would restart Docker containers"
    else
        if command -v docker-compose &> /dev/null; then
            echo "Restarting containers to apply new password..."
            # Restart containers (maintains state better than down/up)
            docker-compose restart
            echo "✓ Containers restarted successfully"
            
            # Wait for services to be healthy
            echo ""
            echo "Waiting for services to be ready..."
            sleep 10
            
            # Check Redis connectivity (use REDISCLI_AUTH env var for security)
            if REDISCLI_AUTH="$NEW_PASSWORD" docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
                echo "✓ Redis is responding with new password"
            else
                echo "⚠️  Could not verify Redis connection"
                echo "   You may need to manually verify the connection"
            fi
        else
            echo "⚠️  docker-compose not found, skipping container restart"
            echo "   Please restart containers manually:"
            echo "   docker-compose restart"
        fi
    fi
else
    echo "═══ Next Steps ═══"
    echo ""
    echo "The password has been updated in all configuration files."
    echo "To apply the changes, restart your Docker containers:"
    echo ""
    echo "  docker-compose restart"
    echo ""
    echo "Or run this script with --restart flag:"
    echo ""
    echo "  ./reset-redis-password.sh --restart"
fi

echo ""

# Final summary
echo "╔════════════════════════════════════════════════════════════════╗"
if [ "$DRY_RUN" = true ]; then
echo "║           DRY RUN COMPLETE - No Changes Made                  ║"
else
echo "║           ✓ Redis Password Reset Complete!                    ║"
fi
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo "Summary of changes:"
    echo "  ✓ .env - Updated REDIS_PASSWORD"
    echo "  ✓ whatsappcrm_backend/.env - Updated Redis URLs"
    echo "  ✓ whatsappcrm_backend/.env.prod - Updated REDIS_PASSWORD"
    echo ""
    echo "Important:"
    echo "  1. The new password has been applied to all configuration files"
    echo "  2. A backup has been saved to .redis-password-backup (delete after noting)"
    echo "  3. Remember to restart Docker containers if not using --restart flag"
    echo ""
    echo "Verification commands:"
    echo "  # Check Redis is using new password:"
    echo "  docker-compose exec redis redis-cli -a '\$REDIS_PASSWORD' ping"
    echo ""
    echo "  # Check backend can connect to Redis:"
    echo "  docker-compose logs backend | grep -i redis"
    echo ""
fi
