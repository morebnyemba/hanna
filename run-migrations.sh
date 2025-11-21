#!/bin/bash
# Database Migration Script for Hanna CRM
# This script runs Django migrations on the backend container

set -e  # Exit on any error

echo "=========================================="
echo "Hanna CRM Database Migration Script"
echo "=========================================="
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed or not in PATH"
    exit 1
fi

# Check if backend container is running
if ! docker-compose ps backend | grep -q "Up"; then
    echo "❌ Error: Backend container is not running"
    echo "Please start the containers first with: docker-compose up -d"
    exit 1
fi

echo "✅ Backend container is running"
echo ""
echo "Running database migrations..."
echo "----------------------------------------"

# Run migrations
docker-compose exec backend python manage.py migrate

if [ $? -eq 0 ]; then
    echo "----------------------------------------"
    echo "✅ Migrations completed successfully!"
    echo ""
    echo "You may also want to:"
    echo "  1. Create a superuser: docker-compose exec backend python manage.py createsuperuser"
    echo "  2. Collect static files: docker-compose exec backend python manage.py collectstatic --noinput"
    echo "  3. Load initial data (if any): docker-compose exec backend python manage.py loaddata <fixture_name>"
else
    echo "----------------------------------------"
    echo "❌ Migration failed!"
    echo "Please check the error messages above"
    exit 1
fi
