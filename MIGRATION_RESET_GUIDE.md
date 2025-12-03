# Migration Reset Guide for Hanna CRM

This guide provides instructions for completely resetting all Django migrations in the Hanna CRM project.

## When to Use This

Use this when you encounter migration errors such as:
- `The following untracked working tree files would be overwritten by merge`
- `InconsistentMigrationHistory` errors
- Migration files that are out of sync between local and remote repositories
- Need to start fresh with migrations after database schema changes

## Quick Start - What Has Been Done

The migration files have been **deleted** from the repository. You now need to:

1. **Reset the database migration table** (clears all migration history)
2. **Regenerate migrations** (creates fresh migration files based on current models)
3. **Apply migrations** (creates database tables)

## Step-by-Step Commands

### Step 1: Clear Migration History from Database

Run this command to clear all records from the `django_migrations` table:

```bash
docker compose exec db psql -U postgres -d postgres -c "DELETE FROM django_migrations;"
```

Or if you're using custom database credentials:

```bash
docker compose exec db psql -U ${DB_USER} -d ${DB_NAME} -c "DELETE FROM django_migrations;"
```

### Step 2: Regenerate All Migrations

Generate fresh migration files for all apps:

```bash
docker compose exec backend python manage.py makemigrations
```

This will create new migration files based on your current models.

### Step 3: Apply Migrations

Apply the fresh migrations to the database:

```bash
docker compose exec backend python manage.py migrate
```

**Note:** If your database already has tables from previous migrations, you may need to use:

```bash
docker compose exec backend python manage.py migrate --fake-initial
```

This tells Django to mark the initial migrations as applied without actually running them (useful when tables already exist).

### Step 4: Create Superuser (If Needed)

If this is a fresh database or you need a new superuser:

```bash
docker compose exec backend python manage.py createsuperuser
```

### Step 5: Commit New Migration Files

After verifying everything works:

```bash
git add whatsappcrm_backend/*/migrations/*.py
git commit -m "Regenerate all Django migrations"
git push
```

## Automated Reset Script

A helper script `reset-all-migrations.sh` is provided for convenience:

```bash
./reset-all-migrations.sh
```

This script will:
1. Clear the `django_migrations` table in the database
2. Delete all migration files (preserves `__init__.py`)
3. Provide instructions for next steps

## Troubleshooting

### Tables Already Exist

If you see errors like `relation "table_name" already exists`:

```bash
docker compose exec backend python manage.py migrate --fake-initial
```

### Need to Completely Reset Database

If you need to start with a completely fresh database:

```bash
# Stop all containers
docker compose down

# Find the database volume name
docker volume ls | grep postgres

# Remove the database volume (WARNING: This deletes all data!)
# Replace <volume_name> with the actual volume name from the previous command
docker volume rm <volume_name>

# Start containers again
docker compose up -d

# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser
```

### Check Migration Status

To see which migrations are applied:

```bash
docker compose exec backend python manage.py showmigrations
```

### View Migration History

To see migration records in the database:

```bash
docker compose exec db psql -U postgres -d postgres -c "SELECT app, name, applied FROM django_migrations ORDER BY applied;"
```

## Important Notes

1. **Always backup your data** before performing migration resets on production databases.

2. The `--fake-initial` flag is useful when:
   - Database tables already exist from previous migrations
   - You want Django to skip the initial table creation but still record the migration as applied

3. After resetting migrations, all team members will need to:
   - Pull the latest code
   - Run `docker compose exec backend python manage.py migrate`

4. If you encounter `InconsistentMigrationHistory` errors in the future, use the `fix-migration-history.sh` script first before doing a complete reset.
