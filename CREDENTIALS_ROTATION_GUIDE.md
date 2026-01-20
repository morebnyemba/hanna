# HANNA Credentials Rotation Guide

This guide explains how to securely rotate credentials (passwords and secret keys) in your HANNA WhatsApp CRM stack.

## 🔐 Available Scripts

| Script | Description |
|--------|-------------|
| `reset-redis-password.sh` | Rotate only the Redis password |
| `rotate-all-passwords.sh` | Rotate all credentials (Redis, PostgreSQL, Django) |

## 📋 Prerequisites

Before running these scripts, ensure you have:

1. **OpenSSL installed** - Used to generate secure random passwords
   ```bash
   openssl version
   ```

2. **Docker and Docker Compose** - Required if using `--restart` flag
   ```bash
   docker --version
   docker-compose --version
   ```

3. **Backup your data** - Always backup before rotating credentials
   ```bash
   # Backup PostgreSQL database
   docker-compose exec db pg_dump -U $DB_USER $DB_NAME > backup.sql
   ```

## 🔄 Redis Password Rotation

### Quick Start

```bash
# Generate new Redis password and update all config files
./reset-redis-password.sh

# Update and restart containers
./reset-redis-password.sh --restart
```

### Options

| Option | Description |
|--------|-------------|
| `--restart` | Restart Docker containers after updating |
| `--dry-run` | Preview changes without applying |
| `--password PASS` | Use a custom password instead of generating |
| `--help` | Show help message |

### What Gets Updated

The script updates Redis password in:
- `.env` (root) - `REDIS_PASSWORD`
- `whatsappcrm_backend/.env` - `CELERY_BROKER_URL`, `REDIS_URL` (embedded password in URL)
- `whatsappcrm_backend/.env.prod` - `REDIS_PASSWORD` (used via env variable interpolation)

**Note:** The backend `.env` file uses URL-embedded passwords, while `.env.prod` uses variable interpolation.

### Examples

```bash
# Preview changes (no modifications)
./reset-redis-password.sh --dry-run

# Use a custom password
./reset-redis-password.sh --password "MySecurePassword123!"

# Generate, apply, and restart containers
./reset-redis-password.sh --restart
```

### Verification

After running the script:

```bash
# Verify Redis is responding with new password
docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" ping
# Expected output: PONG

# Check backend logs for Redis connection
docker-compose logs backend | grep -i redis

# Check Celery worker logs
docker-compose logs celery_io_worker | grep -i redis
```

---

## 🔐 Full Credentials Rotation

### Quick Start

```bash
# Rotate ALL credentials (Redis, PostgreSQL, Django)
./rotate-all-passwords.sh

# Rotate all and restart containers
./rotate-all-passwords.sh --restart
```

### Options

| Option | Description |
|--------|-------------|
| `--restart` | Restart Docker containers after updating |
| `--dry-run` | Preview changes without applying |
| `--redis` | Only rotate Redis password |
| `--postgres` | Only rotate PostgreSQL password |
| `--django` | Only rotate Django secret key |
| `--help` | Show help message |

### Examples

```bash
# Preview all changes
./rotate-all-passwords.sh --dry-run

# Rotate only Redis and Django (skip PostgreSQL)
./rotate-all-passwords.sh --redis --django

# Rotate PostgreSQL only
./rotate-all-passwords.sh --postgres

# Rotate everything and restart
./rotate-all-passwords.sh --restart
```

### Special Considerations

#### PostgreSQL Password Change

⚠️ **Important**: Changing the PostgreSQL password requires additional steps if the database already exists:

```bash
# Option 1: Update password in running database
docker-compose exec db psql -U crm_user -d whatsapp_crm_dev -c "ALTER USER crm_user PASSWORD 'new_password_here';"

# Option 2: Recreate database (DATA LOSS!)
# Only use if you can afford to lose all data
docker-compose down -v  # This deletes all data!
docker-compose up -d
```

#### Django Secret Key Change

⚠️ **Note**: Changing the Django secret key will:
- Invalidate all existing user sessions (users must log in again)
- Invalidate all password reset tokens
- Invalidate any signed cookies

---

## 📁 Files Modified

All scripts modify these files:

| File | Variables |
|------|-----------|
| `.env` | `REDIS_PASSWORD`, `DB_PASSWORD` |
| `whatsappcrm_backend/.env` | `REDIS_PASSWORD`, `CELERY_BROKER_URL`, `REDIS_URL`, `DB_PASSWORD`, `DJANGO_SECRET_KEY` |
| `whatsappcrm_backend/.env.prod` | `REDIS_PASSWORD`, `DB_PASSWORD`, `DJANGO_SECRET_KEY` |

---

## 🔑 Password Backup

After running the scripts, a backup file is created:

- **Redis rotation**: `.redis-password-backup`
- **Full rotation**: `.credentials-backup-YYYYMMDD-HHMMSS`

⚠️ **Security Warning**: These backup files contain plaintext passwords!
- Save the credentials to a secure password manager
- Delete the backup files immediately after saving

```bash
# View backup content
cat .redis-password-backup

# Delete backup after saving
rm .redis-password-backup
rm .credentials-backup-*
```

---

## 🐳 Applying Changes to Running Containers

After updating configuration files, you need to restart containers:

```bash
# Graceful restart
docker-compose down && docker-compose up -d

# Watch logs for issues
docker-compose logs -f
```

### Verify Services Are Working

```bash
# Check all containers are running
docker-compose ps

# Verify Redis
docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" ping

# Verify PostgreSQL
docker-compose exec db psql -U $DB_USER -d $DB_NAME -c "SELECT 1;"

# Verify Backend
docker-compose exec backend python manage.py check

# Check Celery
docker-compose logs --tail=20 celery_io_worker
```

---

## 🚨 Troubleshooting

### Redis Connection Failed

If Redis fails to accept the new password:

1. Check the password was correctly updated in all files:
   ```bash
   grep REDIS .env
   grep REDIS whatsappcrm_backend/.env
   grep REDIS whatsappcrm_backend/.env.prod
   ```

2. Restart Redis container:
   ```bash
   docker-compose restart redis
   ```

3. Check Redis logs:
   ```bash
   docker-compose logs redis
   ```

### Backend Can't Connect to Redis

1. Verify Celery broker URL format:
   ```bash
   grep CELERY_BROKER_URL whatsappcrm_backend/.env
   # Should be: redis://:password@redis:6379/0
   ```

2. Check backend logs:
   ```bash
   docker-compose logs backend | grep -i "connection\|redis\|error"
   ```

### PostgreSQL Authentication Failed

If PostgreSQL rejects the new password:

1. The password in the database must match the environment:
   ```bash
   # Update password in running database
   docker-compose exec db psql -U postgres -c "ALTER USER crm_user PASSWORD 'new_password';"
   ```

2. Or restore from the old password and try again.

### Sessions Invalidated After Django Secret Key Change

This is expected behavior. Users will need to log in again. If you need to prevent this:

- Don't rotate the Django secret key
- Or use a session backend that doesn't rely on the secret key

---

## 🔒 Security Best Practices

1. **Regular Rotation**: Rotate credentials periodically (e.g., every 90 days)

2. **Strong Passwords**: The scripts generate 32-byte base64-encoded passwords (44 characters)

3. **Secure Storage**: Store credentials in a secure password manager, not in plain text

4. **Audit Trail**: Keep track of when credentials were rotated

5. **Backup Before Rotation**: Always backup your database before rotating PostgreSQL password

6. **Test in Staging**: Test credential rotation in a staging environment first

7. **Monitor After Rotation**: Watch logs for connection issues after rotating

---

## 📅 Rotation Schedule Recommendation

| Credential | Rotation Frequency | Risk Level |
|------------|-------------------|------------|
| Redis Password | Every 90 days | Low |
| PostgreSQL Password | Every 90 days | Medium (data access) |
| Django Secret Key | Every 180 days | Medium (sessions) |

---

## 🤖 Automation

You can automate credential rotation using cron or a scheduled task:

```bash
# Example cron job (rotate Redis every month, 1st day at 3 AM)
0 3 1 * * /path/to/hanna/reset-redis-password.sh --restart >> /var/log/hanna-rotation.log 2>&1
```

**Note**: Automated rotation should:
- Send notifications before and after rotation
- Verify services are healthy after rotation
- Have a rollback plan if rotation fails

---

## 📚 Related Documentation

- [DEPLOYMENT_GUIDE_SECURITY_UPDATE.md](DEPLOYMENT_GUIDE_SECURITY_UPDATE.md) - Deployment security guide
- [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md) - Security improvement recommendations
- [SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md) - SSL certificate setup
