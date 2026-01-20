#!/bin/bash

# Rotate All Passwords Script
# This script securely rotates all sensitive credentials in the HANNA stack:
# - Redis password
# - PostgreSQL password
# - Django secret key
#
# Usage:
#   ./rotate-all-passwords.sh              # Rotate all passwords
#   ./rotate-all-passwords.sh --restart    # Rotate all and restart containers
#   ./rotate-all-passwords.sh --dry-run    # Show what would be changed
#   ./rotate-all-passwords.sh --redis      # Only rotate Redis password
#   ./rotate-all-passwords.sh --postgres   # Only rotate PostgreSQL password
#   ./rotate-all-passwords.sh --django     # Only rotate Django secret key

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         HANNA Credentials Rotation Script                     ║"
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
ROTATE_REDIS=false
ROTATE_POSTGRES=false
ROTATE_DJANGO=false
ROTATE_ALL=true

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
        --redis)
            ROTATE_REDIS=true
            ROTATE_ALL=false
            shift
            ;;
        --postgres)
            ROTATE_POSTGRES=true
            ROTATE_ALL=false
            shift
            ;;
        --django)
            ROTATE_DJANGO=true
            ROTATE_ALL=false
            shift
            ;;
        --help|-h)
            echo "Usage: ./rotate-all-passwords.sh [OPTIONS]"
            echo ""
            echo "This script securely rotates all sensitive credentials in the HANNA stack."
            echo ""
            echo "Options:"
            echo "  --restart          Restart Docker containers after updating passwords"
            echo "  --dry-run          Show what would be changed without applying"
            echo "  --redis            Only rotate Redis password"
            echo "  --postgres         Only rotate PostgreSQL password"
            echo "  --django           Only rotate Django secret key"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "By default, all credentials are rotated."
            echo ""
            echo "Files that will be updated:"
            echo "  - .env (root directory - Docker Compose variables)"
            echo "  - whatsappcrm_backend/.env (development environment)"
            echo "  - whatsappcrm_backend/.env.prod (production environment)"
            echo ""
            echo "Examples:"
            echo "  ./rotate-all-passwords.sh                    # Rotate all credentials"
            echo "  ./rotate-all-passwords.sh --restart          # Rotate all and restart"
            echo "  ./rotate-all-passwords.sh --redis --postgres # Rotate only Redis and PostgreSQL"
            echo "  ./rotate-all-passwords.sh --dry-run          # Preview changes"
            echo ""
            echo "⚠️  WARNING: Rotating PostgreSQL password requires database restart"
            echo "    and may cause temporary data access issues if not done carefully."
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

# If rotating all, set all flags to true
if [ "$ROTATE_ALL" = true ]; then
    ROTATE_REDIS=true
    ROTATE_POSTGRES=true
    ROTATE_DJANGO=true
fi

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
    exit 1
fi

echo ""

# Function to generate secure password
generate_password() {
    openssl rand -base64 32
}

# Function to generate Django secret key (50 chars)
generate_django_secret() {
    openssl rand -base64 50 | tr -dc 'a-zA-Z0-9!@#$%^&*()_+-=' | head -c 50
}

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
        echo "Warning: $key not found in $file"
        return 1
    fi
}

# Function to update Redis URL in backend env files
update_redis_urls() {
    local file="$1"
    local password="$2"
    
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi
    
    local escaped_password=$(printf '%s\n' "$password" | sed -e 's/[\/&]/\\&/g')
    
    if grep -q "^CELERY_BROKER_URL=" "$file"; then
        sed -i "s|^CELERY_BROKER_URL=.*|CELERY_BROKER_URL='redis://:${escaped_password}@redis:6379/0'|" "$file"
    fi
    
    if grep -q "^REDIS_URL=" "$file"; then
        sed -i "s|^REDIS_URL=.*|REDIS_URL='redis://:${escaped_password}@redis:6379/1'|" "$file"
    fi
}

# Store generated passwords for final summary
declare -A NEW_PASSWORDS

# ═══════════════════════════════════════════════════════════════
# REDIS PASSWORD ROTATION
# ═══════════════════════════════════════════════════════════════
if [ "$ROTATE_REDIS" = true ]; then
    echo "═══ Rotating Redis Password ═══"
    echo ""
    
    NEW_REDIS_PASSWORD=$(generate_password)
    NEW_PASSWORDS["REDIS"]="$NEW_REDIS_PASSWORD"
    
    # Update root .env
    update_env_var "$ROOT_ENV_FILE" "REDIS_PASSWORD" "$NEW_REDIS_PASSWORD"
    echo "✓ Updated REDIS_PASSWORD in .env"
    
    # Update backend .env
    if grep -q "^REDIS_PASSWORD=" "$BACKEND_ENV_FILE"; then
        update_env_var "$BACKEND_ENV_FILE" "REDIS_PASSWORD" "$NEW_REDIS_PASSWORD"
    fi
    update_redis_urls "$BACKEND_ENV_FILE" "$NEW_REDIS_PASSWORD"
    echo "✓ Updated Redis config in whatsappcrm_backend/.env"
    
    # Update backend .env.prod
    update_env_var "$BACKEND_ENV_PROD_FILE" "REDIS_PASSWORD" "$NEW_REDIS_PASSWORD"
    if grep -q "^CELERY_BROKER_URL=" "$BACKEND_ENV_PROD_FILE"; then
        update_redis_urls "$BACKEND_ENV_PROD_FILE" "$NEW_REDIS_PASSWORD"
    fi
    echo "✓ Updated Redis config in whatsappcrm_backend/.env.prod"
    
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# POSTGRESQL PASSWORD ROTATION
# ═══════════════════════════════════════════════════════════════
if [ "$ROTATE_POSTGRES" = true ]; then
    echo "═══ Rotating PostgreSQL Password ═══"
    echo ""
    
    NEW_DB_PASSWORD=$(generate_password)
    NEW_PASSWORDS["POSTGRES"]="$NEW_DB_PASSWORD"
    
    # Update root .env
    update_env_var "$ROOT_ENV_FILE" "DB_PASSWORD" "$NEW_DB_PASSWORD"
    echo "✓ Updated DB_PASSWORD in .env"
    
    # Update backend .env
    update_env_var "$BACKEND_ENV_FILE" "DB_PASSWORD" "$NEW_DB_PASSWORD"
    echo "✓ Updated DB_PASSWORD in whatsappcrm_backend/.env"
    
    # Update backend .env.prod
    update_env_var "$BACKEND_ENV_PROD_FILE" "DB_PASSWORD" "$NEW_DB_PASSWORD"
    echo "✓ Updated DB_PASSWORD in whatsappcrm_backend/.env.prod"
    
    echo ""
    echo "⚠️  IMPORTANT: PostgreSQL password change requires additional steps!"
    echo "   After changing the password in environment files, you need to:"
    echo "   1. Update the password in PostgreSQL itself:"
    echo "      docker-compose exec db psql -U \$DB_USER -c \"ALTER USER \$DB_USER PASSWORD '\$NEW_PASSWORD';\""
    echo "   2. Or recreate the database (WARNING: data loss):"
    echo "      docker-compose down -v  # This deletes all data!"
    echo "      docker-compose up -d"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# DJANGO SECRET KEY ROTATION
# ═══════════════════════════════════════════════════════════════
if [ "$ROTATE_DJANGO" = true ]; then
    echo "═══ Rotating Django Secret Key ═══"
    echo ""
    
    NEW_DJANGO_SECRET=$(generate_django_secret)
    NEW_PASSWORDS["DJANGO"]="$NEW_DJANGO_SECRET"
    
    # Update backend .env
    update_env_var "$BACKEND_ENV_FILE" "DJANGO_SECRET_KEY" "$NEW_DJANGO_SECRET"
    echo "✓ Updated DJANGO_SECRET_KEY in whatsappcrm_backend/.env"
    
    # Update backend .env.prod
    update_env_var "$BACKEND_ENV_PROD_FILE" "DJANGO_SECRET_KEY" "$NEW_DJANGO_SECRET"
    echo "✓ Updated DJANGO_SECRET_KEY in whatsappcrm_backend/.env.prod"
    
    echo ""
    echo "⚠️  NOTE: Changing Django secret key will:"
    echo "   - Invalidate all existing sessions (users must log in again)"
    echo "   - Invalidate all password reset tokens"
    echo "   - Invalidate signed cookies"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# SAVE CREDENTIALS BACKUP
# ═══════════════════════════════════════════════════════════════
echo "═══ Saving Credentials Backup ═══"
echo ""

BACKUP_FILE="$SCRIPT_DIR/.credentials-backup-$(date +%Y%m%d-%H%M%S)"
if [ "$DRY_RUN" = false ]; then
    {
        echo "# HANNA Credentials Backup - $(date)"
        echo "# KEEP THIS FILE SECURE AND DELETE AFTER SAVING CREDENTIALS!"
        echo "#"
        echo "# These are the NEW credentials that have been applied."
        echo ""
        if [ -n "${NEW_PASSWORDS["REDIS"]}" ]; then
            echo "REDIS_PASSWORD='${NEW_PASSWORDS["REDIS"]}'"
        fi
        if [ -n "${NEW_PASSWORDS["POSTGRES"]}" ]; then
            echo "DB_PASSWORD='${NEW_PASSWORDS["POSTGRES"]}'"
        fi
        if [ -n "${NEW_PASSWORDS["DJANGO"]}" ]; then
            echo "DJANGO_SECRET_KEY='${NEW_PASSWORDS["DJANGO"]}'"
        fi
    } > "$BACKUP_FILE"
    chmod 600 "$BACKUP_FILE"
    echo "✓ Credentials backup saved to: $(basename $BACKUP_FILE)"
    echo "  ⚠️  DELETE THIS FILE after saving credentials securely!"
else
    echo "[DRY RUN] Would create credentials backup"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# RESTART CONTAINERS
# ═══════════════════════════════════════════════════════════════
if [ "$RESTART_CONTAINERS" = true ]; then
    echo "═══ Restarting Docker Containers ═══"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would restart Docker containers"
    else
        if command -v docker-compose &> /dev/null; then
            # If PostgreSQL password was changed, need full restart (not just reload)
            if [ "$ROTATE_POSTGRES" = true ]; then
                echo "⚠️  PostgreSQL password was changed."
                echo "   If the database already exists, you need to update the password manually."
                echo "   See the PostgreSQL rotation notes above."
                echo ""
                read -p "Continue with restart? (y/N): " confirm
                if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
                    echo "Restart cancelled."
                    exit 0
                fi
                echo "Stopping containers..."
                docker-compose down
                echo "Starting containers..."
                docker-compose up -d
            else
                # For Redis/Django changes, restart is sufficient
                echo "Restarting containers..."
                docker-compose restart
            fi
            echo "✓ Containers restarted successfully"
            
            # Wait for services
            echo ""
            echo "Waiting for services to be ready..."
            sleep 15
            
            # Verify services
            echo "Verifying services..."
            
            if [ "$ROTATE_REDIS" = true ] && [ -n "${NEW_PASSWORDS["REDIS"]}" ]; then
                # Use REDISCLI_AUTH env var for security (avoid exposing password in process list)
                if REDISCLI_AUTH="${NEW_PASSWORDS["REDIS"]}" docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
                    echo "✓ Redis is responding with new password"
                else
                    echo "⚠️  Could not verify Redis connection"
                fi
            fi
            
            if docker-compose ps backend | grep -q "Up"; then
                echo "✓ Backend container is running"
            else
                echo "⚠️  Backend container may have issues"
            fi
        else
            echo "⚠️  docker-compose not found"
            echo "   Please restart containers manually"
        fi
    fi
else
    echo "═══ Next Steps ═══"
    echo ""
    echo "Credentials have been updated in all configuration files."
    echo "To apply the changes:"
    echo ""
    echo "  docker-compose down && docker-compose up -d"
    echo ""
    if [ "$ROTATE_POSTGRES" = true ]; then
        echo "⚠️  For PostgreSQL, also run:"
        echo "  docker-compose exec db psql -U \$DB_USER -d \$DB_NAME -c \"ALTER USER \$DB_USER PASSWORD 'new_password';\""
        echo ""
    fi
fi

echo ""

# Final summary
echo "╔════════════════════════════════════════════════════════════════╗"
if [ "$DRY_RUN" = true ]; then
echo "║           DRY RUN COMPLETE - No Changes Made                  ║"
else
echo "║           ✓ Credentials Rotation Complete!                    ║"
fi
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo "Summary of rotated credentials:"
    [ "$ROTATE_REDIS" = true ] && echo "  ✓ Redis password"
    [ "$ROTATE_POSTGRES" = true ] && echo "  ✓ PostgreSQL password (manual DB update may be required)"
    [ "$ROTATE_DJANGO" = true ] && echo "  ✓ Django secret key (sessions invalidated)"
    echo ""
    echo "Backup file: $(basename $BACKUP_FILE)"
    echo "⚠️  Remember to delete the backup file after saving credentials securely!"
    echo ""
fi
