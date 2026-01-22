# Redis Configuration Fix Documentation

## Problem
The Celery worker was failing to start with the error:
```
ValueError: Port could not be cast to integer value as 'FOuP'
```

## Root Cause
The `redis.conf` file contained:
```
requirepass ${REDIS_PASSWORD}
```

Redis configuration files do not support environment variable expansion. This meant Redis was using the literal string `${REDIS_PASSWORD}` as its password instead of the actual password value from the environment.

## Solution
We fixed this by:

1. **Removing the password from redis.conf**: Deleted the `requirepass ${REDIS_PASSWORD}` line
2. **Passing password via command-line**: Modified `docker-compose.yml` to pass the password using the `--requirepass` flag
3. **Fixing network binding**: Changed Redis bind address to allow Docker container connections

### docker-compose.yml Changes
```yaml
redis:
  command: >
    sh -c "redis-server /usr/local/etc/redis/redis.conf --requirepass $${REDIS_PASSWORD}"
  environment:
    REDIS_PASSWORD: ${REDIS_PASSWORD}
```

**How it works:**
1. Docker Compose reads `${REDIS_PASSWORD}` from the `.env` file
2. Sets the `REDIS_PASSWORD` environment variable in the container
3. The command uses `$${REDIS_PASSWORD}` (double `$$` escapes to single `$`)
4. The shell expands `${REDIS_PASSWORD}` using the environment variable
5. Redis starts with `--requirepass <actual_password>`

### redis.conf Changes
```conf
# Password is now set via command-line argument in docker-compose.yml
# This allows proper environment variable substitution

# Bind to all interfaces for Docker networking
bind 0.0.0.0 ::0
```

## Verification
The fix has been tested and verified:
- ✓ URL parsing works correctly
- ✓ Port is correctly parsed as an integer
- ✓ Celery broker URL is properly constructed
- ✓ No more "Port could not be cast to integer value" error

## Security Considerations
- Redis is password-protected via the `--requirepass` flag
- Protected mode is enabled in redis.conf
- Dangerous commands (FLUSHDB, FLUSHALL, CONFIG, etc.) are disabled
- For production, consider restricting bind to Docker's internal network subnet

## Testing
To verify the configuration:
```bash
# Check that Redis URL is correctly formed
python3 -c "
import os, dotenv
from urllib.parse import urlparse
dotenv.load_dotenv('whatsappcrm_backend/.env.prod')
url = f\"redis://:{os.getenv('REDIS_PASSWORD')}@redis:6379/0\"
parsed = urlparse(url)
assert isinstance(parsed.port, int), 'Port must be an integer'
print('✓ Configuration is correct')
"
```

## Migration Notes
When deploying this fix:
1. Stop all Celery workers
2. Update `docker-compose.yml` and `redis.conf`
3. Restart Redis: `docker-compose restart redis`
4. Verify Redis is accessible: `docker exec whatsappcrm_redis redis-cli -a <password> ping`
5. Start Celery workers: `docker-compose up -d celery_io_worker celery_cpu_worker`
