# Immediate Fix Guide for DNS and Database Issues

## Quick Fix Steps

### 1. Stop All Containers
```bash
docker-compose down
```

### 2. Pull Latest Changes
```bash
git pull origin <your-branch>
```

### 3. Recreate Network and Start Containers
```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (30 seconds should be enough)
sleep 30
```

### 4. Run Database Migrations
```bash
# Option A: Use the provided script
./run-migrations.sh

# Option B: Run manually
docker-compose exec backend python manage.py migrate
```

### 5. Create Admin User (if needed)
```bash
docker-compose exec backend python manage.py createsuperuser
```

### 6. Verify Services
```bash
# Check all containers are running
docker-compose ps

# Check backend logs
docker-compose logs backend --tail=50

# Check nginx logs
docker-compose logs nginx --tail=50
```

## What These Changes Fix

### DNS Resolution Issues ✅
**Problem:** Nginx intermittently couldn't resolve service names (`backend`, `hanna-management-frontend`)

**Error:**
```
backend could not be resolved (3: Host not found)
hanna-management-frontend could not be resolved (3: Host not found)
```

**Solution:** Added explicit Docker network configuration in `docker-compose.yml`:
```yaml
networks:
  default:
    name: hanna_network
    driver: bridge
```

**Why this helps:**
- Creates a dedicated bridge network for all services
- Ensures consistent DNS resolution via Docker's internal DNS (127.0.0.11)
- Provides better isolation and network management
- More reliable service discovery

### Empty Database Issue ✅
**Problem:** Database was empty with no tables

**Root Cause:** Migrations are intentionally commented out in docker-compose.yml for production best practices

**Solution:** Provided `run-migrations.sh` script to run migrations on-demand

**Why migrations are commented out:**
- Prevents race conditions when multiple containers start simultaneously
- Avoids conflicts in zero-downtime deployments
- Gives explicit control over when migrations run
- Best practice for production environments

## Verification Steps

### 1. Check DNS Resolution
After the fix, nginx should consistently resolve service names. Test by:

```bash
# Check nginx can reach backend
docker-compose exec nginx ping -c 3 backend

# Check nginx can reach frontend
docker-compose exec nginx ping -c 3 frontend

# Check nginx can reach management frontend
docker-compose exec nginx ping -c 3 hanna-management-frontend
```

All should respond successfully.

### 2. Check Database Tables
Verify database has been properly migrated:

```bash
# List all tables
docker-compose exec backend python manage.py dbshell -c "\dt"

# Or check migrations
docker-compose exec backend python manage.py showmigrations
```

You should see many tables listed and all migrations marked as applied with `[X]`.

### 3. Test Application Access
1. Visit `https://backend.hanna.co.zw/admin/` - Should load without 502 errors
2. Visit `https://hanna.co.zw/` - Should load management frontend
3. Visit `https://dashboard.hanna.co.zw/` - Should load dashboard

## Troubleshooting

### If DNS errors persist:
```bash
# Restart nginx to refresh DNS cache
docker-compose restart nginx

# Check if all services are on the same network
docker network inspect hanna_network

# Verify resolver in nginx config
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf | grep resolver
```

### If database is still empty:
```bash
# Check database connection
docker-compose exec backend python manage.py check --database default

# Try migrations with verbose output
docker-compose exec backend python manage.py migrate --verbosity 2

# Check if database volume exists
docker volume ls | grep postgres_data
```

### If containers won't start:
```bash
# Check for port conflicts
sudo netstat -tlnp | grep -E ':(80|443|5432|6379)'

# Check docker logs
docker-compose logs --tail=100

# Remove old containers and volumes (⚠️ WARNING: This will delete data!)
# docker-compose down -v
# docker-compose up -d
```

## Additional Recommendations

### 1. Enable Health Checks (Optional)
Add health checks to docker-compose.yml for better reliability:

```yaml
backend:
  # ... existing config ...
  healthcheck:
    test: ["CMD", "python", "manage.py", "check", "--database", "default"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### 2. Monitor Logs
Set up log monitoring to catch DNS resolution failures early:

```bash
# Watch nginx error log for DNS issues
docker-compose logs -f nginx | grep "could not be resolved"
```

### 3. Database Backup
Before running migrations in production, always backup:

```bash
# Backup database
docker-compose exec db pg_dump -U ${DB_USER} ${DB_NAME} > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Summary of Changes Made

| File | Change | Purpose |
|------|--------|---------|
| `docker-compose.yml` | Added `networks:` section | Fix DNS resolution issues |
| `run-migrations.sh` | New script | Easy database migration execution |
| `DNS_AND_DATABASE_ISSUES_ANALYSIS.md` | New documentation | Detailed root cause analysis |
| `IMMEDIATE_FIX_GUIDE.md` | New documentation | Step-by-step fix instructions |

## Need Help?

If you encounter issues after following this guide:
1. Check the logs: `docker-compose logs`
2. Verify network: `docker network inspect hanna_network`
3. Check service status: `docker-compose ps`
4. Review the detailed analysis in `DNS_AND_DATABASE_ISSUES_ANALYSIS.md`
