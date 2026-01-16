# Installer Payout System - Migration and Deployment Guide

## Overview
This guide explains how to apply migrations and deploy the new Installer Payout Approval System.

## Database Migrations

The following new models have been added to the `installation_systems` app:

1. **PayoutConfiguration** - Defines payout rates and calculation methods
2. **InstallerPayout** - Tracks technician payouts and approval workflow

### Creating Migrations

Run the following commands in the Docker backend container or local environment:

```bash
# If using Docker:
docker-compose exec backend python manage.py makemigrations installation_systems

# If running locally:
cd whatsappcrm_backend
python manage.py makemigrations installation_systems
```

### Applying Migrations

```bash
# If using Docker:
docker-compose exec backend python manage.py migrate installation_systems

# If running locally:
cd whatsappcrm_backend
python manage.py migrate installation_systems
```

## Initial Configuration

### 1. Create Payout Configurations

After migrations are applied, create payout configurations through the Django admin or API:

```python
# Example: Solar installations with per-kW rate
PayoutConfiguration.objects.create(
    name='Solar Standard Rate',
    installation_type='solar',
    capacity_unit='kW',
    min_system_size=0,
    max_system_size=10,
    rate_type='per_unit',
    rate_amount=50.00,  # $50 per kW
    is_active=True,
    priority=1
)

# Example: Large solar installations with better rate
PayoutConfiguration.objects.create(
    name='Solar Premium Rate',
    installation_type='solar',
    capacity_unit='kW',
    min_system_size=10,
    rate_type='per_unit',
    rate_amount=45.00,  # $45 per kW for larger systems
    is_active=True,
    priority=2
)

# Example: Starlink installations with flat rate
PayoutConfiguration.objects.create(
    name='Starlink Flat Rate',
    installation_type='starlink',
    capacity_unit='units',
    rate_type='flat',
    rate_amount=75.00,  # $75 per installation
    is_active=True,
    priority=1
)
```

### 2. Configure Celery Beat Schedule (Optional)

To enable automatic payout creation for completed installations, add to Celery beat schedule:

```python
# In settings.py or celery.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # ... existing schedules ...
    
    'auto-create-payouts': {
        'task': 'installation_systems.tasks.auto_create_payouts_for_completed_installations',
        'schedule': crontab(hour=1, minute=0),  # Run daily at 1 AM
    },
}
```

## API Endpoints

### Admin API Endpoints

All endpoints require admin authentication (`IsAdminUser` permission).

#### Payout Configuration

- `GET /api/admin/payout-configurations/` - List all configurations
- `POST /api/admin/payout-configurations/` - Create new configuration
- `GET /api/admin/payout-configurations/{id}/` - Get configuration details
- `PUT /api/admin/payout-configurations/{id}/` - Update configuration
- `DELETE /api/admin/payout-configurations/{id}/` - Delete configuration
- `GET /api/admin/payout-configurations/active/` - Get only active configurations

#### Installer Payouts

- `GET /api/admin/installer-payouts/` - List all payouts
- `POST /api/admin/installer-payouts/` - Create new payout manually
- `GET /api/admin/installer-payouts/{id}/` - Get payout details
- `PUT /api/admin/installer-payouts/{id}/` - Update payout notes
- `GET /api/admin/installer-payouts/pending/` - Get pending payouts
- `GET /api/admin/installer-payouts/history/` - Get approved/rejected/paid payouts
- `GET /api/admin/installer-payouts/by_technician/` - Get payouts grouped by technician

### Installation Systems Endpoints

These endpoints are available to technicians (read-only for their own payouts):

- `GET /api/installation-systems/installer-payouts/` - List payouts (filtered by role)
- `GET /api/installation-systems/installer-payouts/{id}/` - Get payout details

## Workflow Actions

### Approve a Payout

```bash
POST /api/admin/installer-payouts/{id}/approve/
Content-Type: application/json

{
    "action": "approve",
    "admin_notes": "Verified all installations completed"
}
```

### Reject a Payout

```bash
POST /api/admin/installer-payouts/{id}/approve/
Content-Type: application/json

{
    "action": "reject",
    "rejection_reason": "Missing commissioning certificates",
    "admin_notes": "Need to resubmit with proper documentation"
}
```

### Mark as Paid

```bash
POST /api/admin/installer-payouts/{id}/mark_paid/
Content-Type: application/json

{
    "payment_reference": "TXN-2024-001234",
    "payment_date": "2024-01-16T10:30:00Z",
    "notes": "Paid via bank transfer"
}
```

### Sync to Zoho

```bash
POST /api/admin/installer-payouts/{id}/sync_to_zoho/
```

Note: Zoho Books API integration requires full implementation. Currently marked as pending.

## Email Notifications

The system automatically sends email notifications to technicians:

1. **Approval Email** - When payout is approved
2. **Rejection Email** - When payout is rejected
3. **Payment Email** - When payment is completed

Emails are sent via Celery tasks using Django's email backend configured in `settings.py`.

## Testing

Run the test suite to verify everything works:

```bash
# If using Docker:
docker-compose exec backend python manage.py test installation_systems.tests.PayoutCalculationServiceTests
docker-compose exec backend python manage.py test installation_systems.tests.InstallerPayoutModelTests

# If running locally:
cd whatsappcrm_backend
python manage.py test installation_systems.tests.PayoutCalculationServiceTests
python manage.py test installation_systems.tests.InstallerPayoutModelTests
```

## Frontend Integration

### Dashboard Pages to Create

1. **Payout Configurations Page** (`/admin/payout-configurations`)
   - List all configurations
   - Create/edit/delete configurations
   - Set active status and priorities

2. **Pending Payouts Page** (`/admin/payouts/pending`)
   - List all pending payouts
   - View payout details
   - Approve/reject actions
   - Bulk approval option

3. **Payout History Page** (`/admin/payouts/history`)
   - List all approved/rejected/paid payouts
   - Filter by technician, status, date range
   - Export to CSV

4. **Payout Detail Page** (`/admin/payouts/{id}`)
   - Full payout information
   - Installation details
   - Calculation breakdown
   - Approval workflow
   - Payment tracking
   - Zoho sync status

5. **Technician Payout View** (`/technician/payouts`)
   - Technicians see their own payouts
   - View status and amounts
   - Download payout reports

## Zoho Books Integration (Future)

To complete Zoho Books integration:

1. Add a method to `ZohoClient` for creating bills/expenses:
   ```python
   def create_bill(self, bill_data):
       # Implement Zoho Books API call
       pass
   ```

2. Update `sync_payout_to_zoho` task in `tasks.py` to use the new method

3. Configure Zoho Books API credentials in `ZohoCredential` model

4. Test the integration with sandbox data

## Security Considerations

1. **Permissions**: Only admin users can approve/reject/pay payouts
2. **Audit Trail**: All actions are logged with timestamps and user information
3. **Validation**: Payouts can only be created for completed installations
4. **Technician Assignment**: System verifies technician is assigned to installations

## Troubleshooting

### Payout not created automatically

Check:
- Installation status is COMMISSIONED or ACTIVE
- Technician is assigned to the installation
- Payout configuration exists for the installation type
- Celery workers are running

### Email not sent

Check:
- Email settings in `.env.prod` or `settings.py`
- Technician has valid email address
- Celery worker is processing email tasks
- Email logs in Django admin

### Zoho sync fails

Check:
- Zoho credentials are configured
- Access token is valid (not expired)
- Organization ID is correct
- Zoho Books API integration is implemented

## Maintenance

### Regular Tasks

1. Monitor pending payouts daily
2. Review rejected payouts weekly
3. Verify Zoho sync status
4. Check email delivery logs
5. Update payout configurations as needed

### Performance Optimization

- Index on `technician_id`, `status`, `created_at` already added
- Consider archiving old paid payouts after 1 year
- Monitor Celery queue length

## Support

For issues or questions:
1. Check logs: `docker-compose logs backend`
2. Review Celery logs: `docker-compose logs celery_io_worker`
3. Check Django admin for error messages
4. Review API response errors
