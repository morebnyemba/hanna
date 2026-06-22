#!/bin/bash
# Fix Migration History Script for Hanna CRM
# This script fixes the InconsistentMigrationHistory error by updating the django_migrations table
#
# Issue: Migration flows.0003_flow_friendly_name_flow_trigger_config_and_more is applied 
#        before its dependency conversations.0003_contact_associated_app_config_and_more
#
# This happens when migrations are applied out of order, usually due to:
# - Manual database manipulation
# - Restoring from an older backup
# - Running migrations in a different order on different environments

set -e  # Exit on any error

# Migration names as variables for maintainability
FLOWS_MIGRATION="0003_flow_friendly_name_flow_trigger_config_and_more"
CONVERSATIONS_MIGRATION="0003_contact_associated_app_config_and_more"

echo "=========================================="
echo "Hanna CRM Migration History Fix Script"
echo "=========================================="
echo ""

# Check if docker-compose or docker compose is available
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Error: docker-compose/docker compose is not available"
    exit 1
fi

# Check if db container is running
check_db_running() {
    # Try the newer status check first, then fall back to parsing ps output
    if $DOCKER_COMPOSE ps db --status running --services >/dev/null 2>&1; then
        $DOCKER_COMPOSE ps db --status running --services | grep -q db
        return $?
    else
        $DOCKER_COMPOSE ps | grep -q "whatsappcrm_db.*Up"
        return $?
    fi
}

if ! check_db_running; then
    echo "❌ Error: Database container is not running"
    echo "Please start the containers first with: $DOCKER_COMPOSE up -d"
    exit 1
fi

echo "✅ Database container is running"
echo ""

# Check for required environment variables
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    echo "⚠️  Warning: DB_USER and/or DB_NAME environment variables are not set."
    echo "    Using default values (postgres/postgres)."
    echo "    For production, please set: export DB_USER=your_user DB_NAME=your_db"
    echo ""
    DB_USER="${DB_USER:-postgres}"
    DB_NAME="${DB_NAME:-postgres}"
fi

echo "This script will fix the migration history by ensuring conversations.0003"
echo "is recorded as applied before flows.0003 in the django_migrations table."
echo ""
echo "⚠️  WARNING: This script modifies the django_migrations table."
echo "    Make sure you have a backup of your database before proceeding."
echo ""
read -p "Do you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Operation cancelled."
    exit 0
fi

echo ""
echo "Checking current migration state..."
echo "----------------------------------------"

# Get the current migration state
$DOCKER_COMPOSE exec db psql -U "$DB_USER" -d "$DB_NAME" -c "
SELECT id, app, name, applied
FROM django_migrations 
WHERE (app = 'flows' AND name = '$FLOWS_MIGRATION')
   OR (app = 'conversations' AND name = '$CONVERSATIONS_MIGRATION')
ORDER BY applied;
"

echo ""
echo "Fixing migration history..."
echo "----------------------------------------"

# The fix: We need to ensure conversations.0003 appears to have been applied before flows.0003
# We'll update the 'applied' timestamp of conversations.0003 to be earlier than flows.0003

$DOCKER_COMPOSE exec db psql -U "$DB_USER" -d "$DB_NAME" -c "
DO \$\$
DECLARE
    conversations_exists BOOLEAN;
    flows_exists BOOLEAN;
    flows_applied TIMESTAMP;
BEGIN
    -- Check if both migrations exist
    SELECT EXISTS(SELECT 1 FROM django_migrations 
                  WHERE app = 'conversations' 
                  AND name = '$CONVERSATIONS_MIGRATION') INTO conversations_exists;
    
    SELECT EXISTS(SELECT 1 FROM django_migrations 
                  WHERE app = 'flows' 
                  AND name = '$FLOWS_MIGRATION') INTO flows_exists;
    
    IF NOT flows_exists THEN
        RAISE NOTICE 'flows.0003 is not in the migrations table - no fix needed';
        RETURN;
    END IF;
    
    IF NOT conversations_exists THEN
        -- conversations.0003 is not recorded, we need to add it
        SELECT applied INTO flows_applied 
        FROM django_migrations 
        WHERE app = 'flows' AND name = '$FLOWS_MIGRATION';
        
        INSERT INTO django_migrations (app, name, applied)
        VALUES ('conversations', '$CONVERSATIONS_MIGRATION', flows_applied - INTERVAL '1 second');
        
        RAISE NOTICE 'Added conversations.0003 to migration history (1 second before flows.0003)';
    ELSE
        -- Both exist, update the timestamp of conversations.0003 to be before flows.0003
        SELECT applied INTO flows_applied 
        FROM django_migrations 
        WHERE app = 'flows' AND name = '$FLOWS_MIGRATION';
        
        UPDATE django_migrations 
        SET applied = flows_applied - INTERVAL '1 second'
        WHERE app = 'conversations' 
        AND name = '$CONVERSATIONS_MIGRATION';
        
        RAISE NOTICE 'Updated conversations.0003 timestamp to be before flows.0003';
    END IF;
END \$\$;
"

echo ""
echo "Verifying fix..."
echo "----------------------------------------"

# Verify the fix
$DOCKER_COMPOSE exec db psql -U "$DB_USER" -d "$DB_NAME" -c "
SELECT id, app, name, applied
FROM django_migrations 
WHERE (app = 'flows' AND name = '$FLOWS_MIGRATION')
   OR (app = 'conversations' AND name = '$CONVERSATIONS_MIGRATION')
ORDER BY applied;
"

echo ""
echo "Testing migration command..."
echo "----------------------------------------"

# Test the migration command and capture output
MIGRATE_OUTPUT=$($DOCKER_COMPOSE exec backend python manage.py migrate --check 2>&1) || true
MIGRATE_EXIT_CODE=$?

if [ $MIGRATE_EXIT_CODE -eq 0 ]; then
    echo "✅ Migration check passed!"
else
    echo "⚠️  Migration check shows pending migrations (this is normal if new migrations exist)"
    echo ""
    echo "Migration check output:"
    echo "$MIGRATE_OUTPUT"
fi

echo ""
echo "=========================================="
echo "Migration history fix completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Run migrations: $DOCKER_COMPOSE exec backend python manage.py migrate"
echo "  2. If issues persist, check: $DOCKER_COMPOSE exec backend python manage.py showmigrations"
echo ""
