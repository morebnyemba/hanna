#!/bin/bash
# Fix Untracked Migrations Script for Hanna CRM
# This script resolves the "untracked working tree files would be overwritten by merge" error
# when migration files exist locally but are not tracked by git.
#
# Common Error:
# error: The following untracked working tree files would be overwritten by merge:
#        whatsappcrm_backend/.../migrations/0001_initial.py
# Please move or remove them before you merge.
# Aborting
#
# Root Cause: 
# Migration files were generated locally (by running makemigrations) but the same 
# files also exist in the remote repository. Git refuses to overwrite untracked files.
#
# IMPORTANT: This script will backup your local migrations before removing them.
# This allows the git pull to succeed and use the tracked versions from the repository.

set -e  # Exit on any error

BACKUP_DIR="./migration_backup_$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "Hanna CRM - Fix Untracked Migrations"
echo "=========================================="
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository root directory"
    echo "   Please run this script from the repository root"
    exit 1
fi

echo "This script will:"
echo "  1. Find untracked migration files that conflict with remote"
echo "  2. Backup them to: $BACKUP_DIR"
echo "  3. Remove the untracked files so git pull can succeed"
echo ""
echo "⚠️  After running this script, you should run:"
echo "    git pull origin main"
echo "    docker compose exec backend python manage.py migrate"
echo ""

read -p "Do you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Operation cancelled."
    exit 0
fi

echo ""
echo "Finding untracked migration files..."
echo "----------------------------------------"

# Find untracked migration files in whatsappcrm_backend
UNTRACKED_MIGRATIONS=$(git status --porcelain 2>/dev/null | grep "^??" | grep "migrations/" | awk '{print $2}' || true)

if [ -z "$UNTRACKED_MIGRATIONS" ]; then
    echo "✅ No untracked migration files found."
    echo ""
    echo "If you're still seeing merge errors, try:"
    echo "  git status  # Check for other untracked/modified files"
    echo "  git stash   # Stash local changes"
    echo "  git pull origin main"
    exit 0
fi

echo "Found the following untracked migration files:"
echo "$UNTRACKED_MIGRATIONS"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo "Created backup directory: $BACKUP_DIR"

echo ""
echo "Backing up and removing untracked migrations..."
echo "----------------------------------------"

# Backup and remove each untracked migration file
for FILE in $UNTRACKED_MIGRATIONS; do
    if [ -f "$FILE" ]; then
        # Create the directory structure in backup
        BACKUP_PATH="$BACKUP_DIR/$(dirname "$FILE")"
        mkdir -p "$BACKUP_PATH"
        
        # Copy to backup
        cp "$FILE" "$BACKUP_PATH/"
        echo "  ✅ Backed up: $FILE"
        
        # Remove the file
        rm "$FILE"
        echo "  ✅ Removed: $FILE"
    fi
done

echo ""
echo "=========================================="
echo "Untracked migrations handled successfully!"
echo "=========================================="
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Pull the latest changes:"
echo "     git pull origin main"
echo ""
echo "  2. Rebuild containers if needed:"
echo "     docker compose down"
echo "     docker compose up -d --build"
echo ""
echo "  3. Run migrations:"
echo "     docker compose exec backend python manage.py migrate"
echo ""
echo "  4. If migrations fail, you may need to fix migration history:"
echo "     ./fix-migration-history.sh"
echo ""
echo "⚠️  IMPORTANT: The backup at $BACKUP_DIR contains your local migrations."
echo "    If you made custom changes, review them before deleting the backup."
echo ""
