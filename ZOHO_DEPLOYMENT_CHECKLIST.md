# Zoho Integration - Deployment Checklist

## Pre-Deployment Verification ✅

### Code Review
- [ ] Review all new files in `integrations/` app
- [ ] Review changes to `products_and_services/` app
- [ ] Review settings.py changes
- [ ] Verify migrations are correct
- [ ] Review test coverage

### Testing in Development
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run migrations: `python manage.py migrate`
- [ ] Run tests: `python manage.py test integrations products_and_services`
- [ ] Test credential creation in admin
- [ ] Test token expiration logic
- [ ] Test sync with staging Zoho account

## Deployment Steps

### 1. Pre-Deployment

**Backup Database:**
```bash
# PostgreSQL
pg_dump -h localhost -U dbuser -d whatsappcrm > backup_$(date +%Y%m%d_%H%M%S).sql

# Or Django dumpdata
python manage.py dumpdata products_and_services.Product > products_backup.json
```

**Check Environment:**
```bash
# Ensure production environment variables are set
echo $DJANGO_SECRET_KEY
echo $DATABASE_URL
echo $CELERY_BROKER_URL
```

### 2. Deploy Code

**Pull Latest Changes:**
```bash
cd /path/to/hanna
git checkout main
git pull origin copilot/integrate-zoho-inventory
```

**Install Dependencies:**
```bash
pip install -r whatsappcrm_backend/requirements.txt
# No new dependencies required!
```

### 3. Run Migrations

**Check Migration Status:**
```bash
cd whatsappcrm_backend
python manage.py showmigrations integrations
python manage.py showmigrations products_and_services
```

**Run Migrations:**
```bash
# Dry run first
python manage.py migrate integrations --plan
python manage.py migrate products_and_services --plan

# Apply migrations
python manage.py migrate integrations
python manage.py migrate products_and_services
```

**Verify Migrations:**
```bash
python manage.py shell
>>> from integrations.models import ZohoCredential
>>> from products_and_services.models import Product
>>> Product._meta.get_field('zoho_item_id')
<django.db.models.fields.CharField: zoho_item_id>
```

### 4. Configure Zoho Credentials

**Get OAuth Tokens from Zoho:**

1. **Go to Zoho API Console**: https://api-console.zoho.com/
2. **Create Server-based Application**
3. **Set Redirect URI** in the Zoho console:
   - Development: `http://localhost:8000/oauth/callback`
   - Production: `https://backend.hanna.co.zw/oauth/callback`
   - Or use Postman: `https://www.getpostman.com/oauth2/callback`
   - **Important**: This URI must match exactly in steps below
4. **Note Client ID and Client Secret**

**Generate Initial Tokens:**

```bash
# Step 1: Open in browser (replace YOUR_CLIENT_ID and YOUR_REDIRECT_URI)
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoInventory.items.READ&client_id=YOUR_CLIENT_ID&response_type=code&access_type=offline&redirect_uri=YOUR_REDIRECT_URI

# Step 2: After authorization, you'll be redirected to:
# YOUR_REDIRECT_URI?code=1000.xxxxx
# Copy the code parameter

# Step 3: Exchange code for tokens (use same redirect_uri)
curl -X POST https://accounts.zoho.com/oauth/v2/token \
  -d "code=YOUR_AUTH_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI" \
  -d "grant_type=authorization_code"

# Response will include access_token and refresh_token
```

**Note**: The redirect URI is only needed for this initial setup. After obtaining the refresh token, the system handles authentication automatically without needing a redirect endpoint in your application.

**Add to Django Admin:**
```
1. Login to /admin
2. Go to: Integrations → Zoho Credentials
3. Click: Add Zoho Credential
4. Fill in all fields:
   - Client ID: [from Zoho API Console]
   - Client Secret: [from Zoho API Console]
   - Access Token: [from OAuth flow response]
   - Refresh Token: [from OAuth flow response]
   - Organization ID: [from Zoho Inventory settings]
   - API Domain: https://inventory.zoho.com (or .eu, .in based on region)
   - Scope: ZohoInventory.items.READ
   - Expires In: [current time + 1 hour]
5. Save
```

### 5. Restart Services

**Django Application:**
```bash
# For Gunicorn
sudo systemctl restart gunicorn

# For Docker
docker-compose restart backend

# Or manual
pkill -f gunicorn
gunicorn whatsappcrm_backend.wsgi:application
```

**Celery Workers:**
```bash
# For systemd
sudo systemctl restart celery-worker

# For Docker
docker-compose restart celery_worker

# Or manual
pkill -f "celery worker"
celery -A whatsappcrm_backend worker -l info
```

### 6. Verify Deployment

**Check Admin Interface:**
- [ ] Login to /admin
- [ ] See "Integrations" app in sidebar
- [ ] See "Sync Zoho" button in top menu
- [ ] Open Zoho Credentials - verify singleton works
- [ ] Open Product admin - see zoho_item_id field

**Check Token Status:**
```bash
python manage.py shell
>>> from integrations.models import ZohoCredential
>>> cred = ZohoCredential.get_instance()
>>> print(f"Token expires: {cred.expires_in}")
>>> print(f"Is expired: {cred.is_expired()}")
```

**Test API Connection:**
```bash
python manage.py shell
>>> from integrations.utils import ZohoClient
>>> client = ZohoClient()
>>> result = client.fetch_products(page=1, per_page=5)
>>> print(f"Success! Fetched {len(result['items'])} items")
```

### 7. First Production Sync

**Trigger Test Sync:**
```bash
python manage.py shell
>>> from products_and_services.services import sync_zoho_products_to_db
>>> stats = sync_zoho_products_to_db()
>>> print(stats)
```

**Or Use Admin UI:**
1. Click "Sync Zoho" button in admin
2. Wait for success message
3. Check Products list

**Verify Results:**
- [ ] Products appear in Product admin
- [ ] zoho_item_id field is populated
- [ ] Prices match Zoho
- [ ] Stock quantities match Zoho
- [ ] No errors in logs

### 8. Monitor

**Check Logs:**
```bash
# Django logs
tail -f logs/django.log | grep -i zoho

# Celery logs
tail -f logs/celery.log | grep -i zoho

# System logs
journalctl -u gunicorn -f
journalctl -u celery-worker -f
```

**Monitor Task Queue:**
```bash
# Redis queue
redis-cli
> KEYS celery*
> LLEN celery

# Or Flower (if installed)
celery -A whatsappcrm_backend flower
# Visit http://localhost:5555
```

## Post-Deployment

### Verify Sync Success
- [ ] Check Product count: `Product.objects.filter(zoho_item_id__isnull=False).count()`
- [ ] Verify sample products match Zoho
- [ ] Check sync statistics in logs
- [ ] Test updating a product in Zoho and re-syncing

### Configure Monitoring
- [ ] Set up log aggregation for sync events
- [ ] Configure alerts for sync failures
- [ ] Monitor Celery task success rate
- [ ] Track sync duration metrics

### Schedule Regular Syncs (Optional)
```python
# In settings.py or celery.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'sync-zoho-daily': {
        'task': 'products_and_services.tasks.task_sync_zoho_products',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

Then start Celery Beat:
```bash
celery -A whatsappcrm_backend beat -l info
```

### Documentation
- [ ] Update team documentation with Zoho setup
- [ ] Share `ZOHO_INTEGRATION_QUICK_START.md` with team
- [ ] Document Zoho credential rotation procedure
- [ ] Add runbook for common issues

## Rollback Plan

If issues occur:

### 1. Stop Sync Operations
```bash
# Kill running Celery tasks
celery -A whatsappcrm_backend purge

# Or restart worker
sudo systemctl restart celery-worker
```

### 2. Rollback Migrations
```bash
python manage.py migrate products_and_services 0010
python manage.py migrate integrations zero
```

### 3. Rollback Code
```bash
git revert <commit-hash>
# Or
git checkout main
```

### 4. Restore Database (if needed)
```bash
# PostgreSQL
psql -U dbuser -d whatsappcrm < backup_YYYYMMDD_HHMMSS.sql
```

### 5. Restart Services
```bash
sudo systemctl restart gunicorn celery-worker
```

## Troubleshooting

### Issue: Token Refresh Fails
**Solution:**
1. Check refresh_token is valid
2. Verify client_id and client_secret
3. Generate new tokens from Zoho
4. Update in admin panel

### Issue: No Items Synced
**Solution:**
1. Verify organization_id is correct
2. Check API domain (region)
3. Ensure Zoho account has items
4. Check API permissions/scope
5. Review logs for detailed errors

### Issue: Duplicate Products
**Solution:**
1. Zoho uses `zoho_item_id` as identifier
2. Manual products won't conflict (no zoho_item_id)
3. If duplicates exist, merge manually:
   ```python
   # Keep one, delete other
   Product.objects.filter(name="Duplicate Name", zoho_item_id__isnull=True).delete()
   ```

### Issue: Sync Takes Too Long
**Solution:**
1. Check network latency to Zoho API
2. Reduce per_page size if timeouts occur
3. Monitor Celery worker resources
4. Consider splitting into multiple tasks

## Success Metrics

After deployment, verify:
- ✅ Products sync successfully
- ✅ Token auto-refresh works
- ✅ Admin UI is responsive
- ✅ No errors in logs
- ✅ Sync completes in reasonable time
- ✅ Product data matches Zoho

## Contacts

**For Issues:**
- Django Logs: `/var/log/django/`
- Celery Logs: `/var/log/celery/`
- Documentation: `ZOHO_INTEGRATION_README.md`
- Quick Start: `ZOHO_INTEGRATION_QUICK_START.md`

**Support Channels:**
- GitHub Issues: [Link to repo]
- Team Slack/Discord: [Channel]
- Email: [Support email]

---

## Deployment Sign-off

- [ ] Code reviewed and approved
- [ ] Tests passing
- [ ] Documentation complete
- [ ] Backup taken
- [ ] Migrations tested
- [ ] Credentials configured
- [ ] Services restarted
- [ ] Sync verified
- [ ] Monitoring configured
- [ ] Team notified

**Deployed by:** _________________  
**Date:** _________________  
**Version:** v1.0.0  
**Commit:** 382f10d  
