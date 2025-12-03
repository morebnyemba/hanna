#!/bin/bash
# Database Migration Script for Hanna CRM
# This script runs Django migrations on the backend container

echo "=========================================="
echo "Hanna CRM Database Migration Script"
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

# Check if backend container is running
check_backend_running() {
    # Try newer docker compose ps syntax first
    if $DOCKER_COMPOSE ps backend --status running --services >/dev/null 2>&1; then
        # If command succeeds, backend is running (service name is already filtered)
        return 0
    else
        # Fall back to parsing ps output for older docker-compose versions
        $DOCKER_COMPOSE ps | grep -q "whatsappcrm_backend_app.*Up"
        return $?
    fi
}

if ! check_backend_running; then
    echo "❌ Error: Backend container is not running"
    echo "Please start the containers first with: $DOCKER_COMPOSE up -d"
    exit 1
fi

echo "✅ Backend container is running"
echo ""
echo "Running database migrations..."
echo "----------------------------------------"

# Run migrations and capture output
MIGRATE_OUTPUT=$($DOCKER_COMPOSE exec -T backend python manage.py migrate 2>&1)
MIGRATE_EXIT_CODE=$?

echo "$MIGRATE_OUTPUT"

if [ $MIGRATE_EXIT_CODE -eq 0 ]; then
    echo "----------------------------------------"
    echo "✅ Migrations completed successfully!"
    echo ""
    echo "You may also want to:"
    echo "  1. Create a superuser: $DOCKER_COMPOSE exec backend python manage.py createsuperuser"
    echo "  2. Collect static files: $DOCKER_COMPOSE exec backend python manage.py collectstatic --noinput"
    echo "  3. Load initial data (if you have fixtures): $DOCKER_COMPOSE exec backend python manage.py loaddata initial_data.json"
else
    echo "----------------------------------------"
    echo "❌ Migration failed!"
    echo ""
    
    # Check for specific known errors and provide targeted help
    if echo "$MIGRATE_OUTPUT" | grep -q "InconsistentMigrationHistory"; then
        echo "🔧 DETECTED: InconsistentMigrationHistory error"
        echo ""
        echo "This error occurs when migrations are applied out of order."
        echo "To fix this issue, you can use one of these methods:"
        echo ""
        echo "Option 1 - Use the Django management command:"
        echo "  $DOCKER_COMPOSE exec backend python manage.py fix_migration_history --fix"
        echo ""
        echo "Option 2 - Use the shell script:"
        echo "  ./fix-migration-history.sh"
        echo ""
        echo "After fixing, run this script again."
    elif echo "$MIGRATE_OUTPUT" | grep -q "relation.*already exists"; then
        echo "🔧 DETECTED: Tables already exist error"
        echo ""
        echo "This can happen when the database schema exists but migrations aren't recorded."
        echo "Try running with --fake-initial:"
        echo "  $DOCKER_COMPOSE exec backend python manage.py migrate --fake-initial"
    elif echo "$MIGRATE_OUTPUT" | grep -q "does not exist"; then
        echo "🔧 DETECTED: Missing table or column error"
        echo ""
        echo "This usually means the database needs to be initialized or migrations need to run."
        echo "If this is a fresh database, try:"
        echo "  $DOCKER_COMPOSE exec backend python manage.py migrate"
    fi
    
    exit 1
fi
