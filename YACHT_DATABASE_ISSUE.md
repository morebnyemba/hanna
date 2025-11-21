# Database Empty After Installing Yacht - Analysis

## Question
"The database was populated prior to today, is it because I installed Yacht?"

## Answer: Yes, likely Yacht is the cause

### What is Yacht?
Yacht is a web-based Docker container management UI. When you install and use Yacht to manage your containers, it can cause issues with existing Docker Compose setups.

### Why Your Database Became Empty

There are several possible reasons:

#### 1. **Volume Recreation (Most Likely)**
When Yacht manages containers, it may:
- Stop and remove containers
- Recreate containers with new configurations
- Create new volumes instead of reusing existing ones

If Yacht created a new `postgres_data` volume, your old database data would be on the **old volume**, while the new PostgreSQL container is using the **new empty volume**.

#### 2. **Volume Path Mismatch**
Yacht might have changed the volume mount path or created a different volume with a similar name, resulting in:
- Old volume: `postgres_data` (with your data)
- New volume: `hanna_postgres_data` or similar (empty)

#### 3. **Container Network Issues**
If Yacht changed the network configuration, containers might not be able to communicate properly, though this wouldn't directly empty the database.

### How to Verify

Check your Docker volumes:

```bash
# List all volumes
docker volume ls

# Look for postgres volumes - you might see multiple:
# - postgres_data (old, with data)
# - hanna_postgres_data (new, empty)
# - or variations
```

Check volume details:

```bash
# Inspect the volume currently in use
docker volume inspect postgres_data

# Check if there are other postgres volumes
docker volume ls | grep postgres
```

### How to Recover Your Data

#### Option 1: Find and Use the Old Volume (Recommended)

1. **List all volumes to find the old one:**
   ```bash
   docker volume ls | grep postgres
   ```

2. **If you find multiple postgres volumes, inspect them:**
   ```bash
   docker volume inspect <volume_name>
   ```

3. **Check the data in each volume:**
   ```bash
   # Stop the database container first
   docker-compose stop db
   
   # Start a temporary container to explore the volume
   docker run --rm -v <volume_name>:/data alpine ls -la /data
   ```

4. **If you find the volume with data, update docker-compose.yml:**
   ```yaml
   services:
     db:
       volumes:
         - <old_volume_name>:/var/lib/postgresql/data/
   ```

5. **Restart services:**
   ```bash
   docker-compose up -d
   ```

#### Option 2: Migrate Data from Old Volume

If you found the old volume:

```bash
# Stop current database
docker-compose stop db

# Create temporary container with both volumes
docker run --rm \
  -v <old_volume>:/source \
  -v postgres_data:/target \
  alpine sh -c "cp -a /source/. /target/"

# Start services
docker-compose up -d
```

#### Option 3: Restore from Backup

If you have a database backup:

```bash
# Restore from SQL backup
docker-compose exec db psql -U ${DB_USER} ${DB_NAME} < backup.sql

# Or restore from pg_dump file
docker-compose exec -T db pg_restore -U ${DB_USER} -d ${DB_NAME} < backup.dump
```

### Prevention for Future

1. **Always Backup Before Making Infrastructure Changes:**
   ```bash
   # Backup database before any changes
   docker-compose exec db pg_dump -U ${DB_USER} ${DB_NAME} > backup_$(date +%Y%m%d).sql
   ```

2. **Use Named Volumes with Explicit Names:**
   In docker-compose.yml, explicitly name volumes:
   ```yaml
   volumes:
     postgres_data:
       name: hanna_postgres_data_v1
   ```

3. **Avoid Mixing Management Tools:**
   - If using Yacht, let it manage everything
   - If using docker-compose, don't let Yacht manage those containers
   - Mixing tools can cause conflicts

4. **Document Your Volume Names:**
   Keep track of which volumes contain production data

### Recommended Actions Now

1. **List all volumes and find the one with your data:**
   ```bash
   docker volume ls
   docker volume ls | grep -E '(postgres|hanna|whatsapp)'
   ```

2. **Inspect volumes to find the one with data:**
   ```bash
   docker run --rm -v <volume_name>:/data alpine ls -lah /data/
   ```

3. **Once found, update docker-compose.yml to use that volume**

4. **If data is lost and no backup exists:**
   - Run migrations to recreate schema: `./run-migrations.sh`
   - Manually re-enter critical data or restore from application-level backups

### About Yacht and Docker Compose

**Important:** Yacht and docker-compose can conflict because:
- Both try to manage container lifecycle
- They may use different volume naming schemes
- Network configurations can differ
- Container names might conflict

**Best Practice:** Choose one management approach:
- **Docker Compose**: Better for development, version control, reproducible deployments
- **Yacht**: Better for visual management, quick container inspection
- **Don't mix both** for the same containers

### Summary

Your database became empty most likely because:
1. Yacht created new volumes when managing containers
2. Your old `postgres_data` volume still exists with your data
3. The new PostgreSQL container is using a different (empty) volume

**Next steps:**
1. Find the old volume with your data
2. Update docker-compose.yml to use it
3. Restart services
4. Consider avoiding Yacht for docker-compose managed services
