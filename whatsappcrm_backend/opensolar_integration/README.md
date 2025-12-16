# OpenSolar Integration App

This Django app integrates OpenSolar solar design and project management platform with the Hanna WhatsApp CRM system.

## Features

- **Automatic Sync**: Solar installation requests are automatically synced to OpenSolar
- **Webhook Processing**: Receives and processes webhook events from OpenSolar
- **Project Tracking**: Links installation requests to OpenSolar projects
- **Status Updates**: Bidirectional status synchronization
- **Admin Interface**: Full admin UI for managing configuration and monitoring sync status

## Models

### OpenSolarConfig
Configuration for OpenSolar API integration. Stores API credentials and feature flags.

### OpenSolarProject
Links InstallationRequest to OpenSolar project. Tracks sync status and project details.

### OpenSolarWebhookLog
Logs all webhook events received from OpenSolar.

### OpenSolarSyncLog
Tracks synchronization operations for debugging and monitoring.

## Setup

1. **Add to INSTALLED_APPS** in `settings.py`:
```python
INSTALLED_APPS = [
    # ... other apps ...
    'opensolar_integration',
]
```

2. **Add URL patterns** in main `urls.py`:
```python
urlpatterns = [
    # ... other patterns ...
    path('api/opensolar/', include('opensolar_integration.urls')),
]
```

3. **Add environment variables** to `.env`:
```bash
OPENSOLAR_API_KEY=your_api_key_here
OPENSOLAR_ORG_ID=your_org_id_here
OPENSOLAR_API_BASE_URL=https://api.opensolar.com
OPENSOLAR_WEBHOOK_SECRET=your_webhook_secret
```

4. **Run migrations**:
```bash
python manage.py makemigrations opensolar_integration
python manage.py migrate opensolar_integration
```

5. **Create OpenSolar configuration** in Django admin:
   - Go to OpenSolar Integration → OpenSolar Configurations
   - Click "Add OpenSolar Configuration"
   - Fill in your organization details and API credentials
   - Enable auto-sync and webhooks
   - Save

6. **Configure webhooks in OpenSolar**:
   - Log in to OpenSolar dashboard
   - Go to Settings → Webhooks
   - Add webhook URL: `https://backend.hanna.co.zw/api/opensolar/webhook/`
   - Select events to monitor
   - Save

## Usage

### Automatic Sync

When a new solar installation request is created, it will automatically be synced to OpenSolar if:
- OpenSolar integration is configured and active
- Auto-sync is enabled
- Installation type is 'solar' or 'hybrid'

### Manual Sync

To manually sync a project:

1. **Via Admin**:
   - Go to OpenSolar Projects
   - Select projects to sync
   - Choose "Sync selected projects to OpenSolar" action

2. **Via API**:
```bash
POST /api/opensolar/projects/{id}/sync/
```

3. **Via Python**:
```python
from opensolar_integration.services import ProjectSyncService

service = ProjectSyncService()
service.sync_installation_request(installation_request, force=True)
```

### Webhook Processing

Webhooks are automatically processed when received. Supported events:
- `project.status_changed` - Updates project and installation request status
- `project.design_complete` - Logs design completion
- `project.proposal_sent` - Stores proposal URL
- `project.contract_signed` - Marks contract as signed
- `project.installation_scheduled` - Sets installation date

## Celery Tasks

### Automatic Tasks

- `sync_installation_to_opensolar` - Async task for syncing installation requests
- `fetch_opensolar_project_updates` - Periodic task to fetch updates (runs every 24 hours)
- `retry_failed_syncs` - Retry failed sync operations (runs every hour)

### Configure Celery Beat

Add to `celery.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'fetch-opensolar-updates': {
        'task': 'opensolar_integration.tasks.fetch_opensolar_project_updates',
        'schedule': crontab(hour='*/24'),  # Every 24 hours
    },
    'retry-failed-syncs': {
        'task': 'opensolar_integration.tasks.retry_failed_syncs',
        'schedule': crontab(minute='*/60'),  # Every hour
    },
}
```

## API Endpoints

### Projects

- `GET /api/opensolar/projects/` - List all OpenSolar projects
- `GET /api/opensolar/projects/{id}/` - Get project details
- `POST /api/opensolar/projects/{id}/sync/` - Manually sync project
- `GET /api/opensolar/projects/{id}/status/` - Fetch latest status

### Webhooks

- `POST /api/opensolar/webhook/` - Receive webhooks from OpenSolar

## Testing

Run tests:
```bash
python manage.py test opensolar_integration
```

## Troubleshooting

### Sync Failures

Check the OpenSolar Sync Logs in admin to see detailed error messages.

Common issues:
- Invalid API credentials
- Network connectivity problems
- Missing required fields in installation request
- OpenSolar API rate limits

### Webhook Issues

Check the OpenSolar Webhook Logs in admin to see all received webhooks.

Common issues:
- Invalid webhook secret
- Missing webhook configuration in OpenSolar
- Webhook URL not accessible from OpenSolar servers

## Monitoring

Key metrics to monitor:
- Sync success rate
- Average sync time
- Webhook processing errors
- Failed sync retry count

View these in Django admin under OpenSolar Integration models.

## See Also

- [OPENSOLAR_INTEGRATION_GUIDE.md](../../OPENSOLAR_INTEGRATION_GUIDE.md) - Complete integration guide
- [OPENSOLAR_IMPLEMENTATION.md](../../OPENSOLAR_IMPLEMENTATION.md) - Technical implementation details
- [OPENSOLAR_QUICK_START.md](../../OPENSOLAR_QUICK_START.md) - Quick start for business team
