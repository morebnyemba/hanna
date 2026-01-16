#!/bin/bash

# Installer Payout System - Migration Creation Script
# This script helps create the necessary database migrations for the payout system

set -e

echo "=========================================="
echo "Installer Payout System - Migration Setup"
echo "=========================================="
echo ""

# Check if running in Docker or local
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    MANAGE_CMD="python manage.py"
else
    echo "Running locally"
    MANAGE_CMD="python manage.py"
fi

echo ""
echo "Step 1: Checking for existing migrations..."
cd /app 2>/dev/null || cd whatsappcrm_backend 2>/dev/null || {
    echo "Error: Could not find backend directory"
    exit 1
}

# Show current migration status
echo ""
echo "Current migration status for installation_systems:"
$MANAGE_CMD showmigrations installation_systems || true

echo ""
echo "Step 2: Creating new migrations..."
$MANAGE_CMD makemigrations installation_systems

echo ""
echo "Step 3: Displaying migration plan..."
$MANAGE_CMD migrate --plan installation_systems

echo ""
echo "=========================================="
echo "Migration files created successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the migration files in installation_systems/migrations/"
echo "2. Test in development environment first"
echo "3. Apply migrations:"
echo "   - Docker: docker-compose exec backend python manage.py migrate"
echo "   - Local:  python manage.py migrate"
echo "4. Create initial payout configurations (see deployment guide)"
echo ""
