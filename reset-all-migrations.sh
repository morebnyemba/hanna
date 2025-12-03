#!/bin/bash
# Reset All Migrations Script for Hanna CRM
# 
# This script completely resets all Django migrations:
# 1. Clears all records from the django_migrations table in the database
# 2. Removes all migration files from all apps (preserves __init__.py)
# 3. Provides instructions to regenerate fresh migrations
#
# ⚠️  WARNING: This is a destructive operation!
# - All migration history will be lost
# - All migration files will be deleted
# - You will need to regenerate all migrations
#
# Use this when you need a complete fresh start with migrations.

set -e  # Exit on any error

echo "=========================================="
echo "Hanna CRM - Complete Migration Reset"
echo "=========================================="
echo ""

# Check if we're in the repository root
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository root directory"
    echo "   Please run this script from the repository root (where docker-compose.yml is)"
    exit 1
fi

if [ ! -d "whatsappcrm_backend" ]; then
    echo "❌ Error: whatsappcrm_backend directory not found"
    echo "   Please run this script from the repository root"
    exit 1
fi

# Check if docker-compose or docker compose is available
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Error: docker-compose/docker compose is not available"
    exit 1
fi

echo "⚠️  WARNING: This will COMPLETELY reset all migrations!"
echo ""
echo "This script will:"
echo "  1. Clear ALL records from the django_migrations table"
echo "  2. Delete ALL migration files (except __init__.py)"
echo ""
echo "After running this script, you MUST:"
echo "  1. Run makemigrations to regenerate all migration files"
echo "  2. Run migrate to apply the fresh migrations"
echo ""
echo "⚠️  THIS IS A DESTRUCTIVE OPERATION!"
echo "    Make sure you have a backup of your database if needed."
echo ""

read -p "Type 'RESET' (all caps) to confirm you want to proceed: " CONFIRM

if [ "$CONFIRM" != "RESET" ]; then
    echo "❌ Operation cancelled. You must type 'RESET' to proceed."
    exit 0
fi

echo ""
echo "=========================================="
echo "Step 1: Clearing django_migrations table"
echo "=========================================="
echo ""

# Check for required environment variables, using defaults if not set
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    echo "⚠️  Note: DB_USER and/or DB_NAME not set in environment."
    echo "    Using defaults: DB_USER=postgres, DB_NAME=postgres"
    echo "    Set these in your environment or .env file for production."
    echo ""
    DB_USER="${DB_USER:-postgres}"
    DB_NAME="${DB_NAME:-postgres}"
fi

# Check if db container is running
check_db_running() {
    if $DOCKER_COMPOSE ps db --status running --services >/dev/null 2>&1; then
        $DOCKER_COMPOSE ps db --status running --services | grep -q db
        return $?
    else
        $DOCKER_COMPOSE ps | grep -q "whatsappcrm_db.*Up"
        return $?
    fi
}

if check_db_running; then
    echo "Clearing django_migrations table..."
    
    # Delete all migration records from the database
    $DOCKER_COMPOSE exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "
    DO \$\$
    DECLARE
        migration_count INTEGER;
    BEGIN
        SELECT COUNT(*) INTO migration_count FROM django_migrations;
        RAISE NOTICE 'Found % migration records', migration_count;
        
        DELETE FROM django_migrations;
        
        RAISE NOTICE 'Deleted all migration records from django_migrations table';
    END \$\$;
    " 2>/dev/null || {
        echo "⚠️  Could not clear django_migrations table."
        echo "    This might happen if the table doesn't exist yet (fresh database)."
        echo "    Continuing with file deletion..."
    }
    
    echo "✅ Database migration records cleared"
else
    echo "⚠️  Database container is not running."
    echo "    Skipping database cleanup - only deleting migration files."
    echo "    Run this again after starting containers to clear the database."
fi

echo ""
echo "=========================================="
echo "Step 2: Removing all migration files"
echo "=========================================="
echo ""

# Find and count migration files before deletion
MIGRATION_FILES=$(find whatsappcrm_backend -path "*/migrations/*.py" -not -name "__init__.py" -type f 2>/dev/null)
FILE_COUNT=$(echo "$MIGRATION_FILES" | grep -c "^" 2>/dev/null || echo "0")

if [ "$FILE_COUNT" -gt 0 ]; then
    echo "Found $FILE_COUNT migration files to delete:"
    echo "$MIGRATION_FILES" | head -20
    if [ "$FILE_COUNT" -gt 20 ]; then
        echo "... and $((FILE_COUNT - 20)) more files"
    fi
    echo ""
    
    # Delete all migration files except __init__.py
    find whatsappcrm_backend -path "*/migrations/*.py" -not -name "__init__.py" -type f -delete
    
    echo "✅ Deleted $FILE_COUNT migration files"
else
    echo "✅ No migration files found to delete"
fi

# Also remove any compiled Python files in migrations folders
PYCS=$(find whatsappcrm_backend -path "*/migrations/__pycache__" -type d 2>/dev/null)
if [ -n "$PYCS" ]; then
    find whatsappcrm_backend -path "*/migrations/__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    echo "✅ Cleaned up migration __pycache__ directories"
fi

echo ""
echo "=========================================="
echo "Migration Reset Complete!"
echo "=========================================="
echo ""
echo "✅ All migration records cleared from database"
echo "✅ All migration files deleted from repository"
echo ""
echo "=========================================="
echo "NEXT STEPS - Run these commands in order:"
echo "=========================================="
echo ""
echo "1. Rebuild the backend container (optional but recommended):"
echo "   $DOCKER_COMPOSE down"
echo "   $DOCKER_COMPOSE up -d --build"
echo ""
echo "2. Generate fresh migrations for all apps:"
echo "   $DOCKER_COMPOSE exec backend python manage.py makemigrations"
echo ""
echo "3. Apply the new migrations:"
echo "   $DOCKER_COMPOSE exec backend python manage.py migrate"
echo ""
echo "4. Create a superuser (if needed):"
echo "   $DOCKER_COMPOSE exec backend python manage.py createsuperuser"
echo ""
echo "5. Commit the new migration files to git:"
echo "   git add whatsappcrm_backend/*/migrations/*.py"
echo "   git commit -m 'Regenerate all Django migrations'"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - The new migrations will be based on your current models"
echo "   - If your database has existing data, you may need to handle"
echo "     the migration carefully or reset the database tables too"
echo ""
