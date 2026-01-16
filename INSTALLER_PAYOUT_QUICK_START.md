# Installer Payout System - Quick Start Guide

## Overview

The Installer Payout Approval System enables automated calculation and management of technician payments for completed installations.

## 🚀 Quick Setup (5 minutes)

### Step 1: Apply Migrations

```bash
# Using Docker (recommended)
docker-compose exec backend python manage.py makemigrations installation_systems
docker-compose exec backend python manage.py migrate

# Or using the helper script
./create-payout-migrations.sh
```

### Step 2: Create Default Configurations

```bash
# Using Docker
docker-compose exec backend python setup_payout_configurations.py

# Or locally
cd whatsappcrm_backend
python setup_payout_configurations.py
```

This creates default rates:
- Solar: $60/kW (0-5kW), $50/kW (5-15kW), $45/kW (15kW+)
- Starlink: $100 flat
- Hybrid: $150 flat
- Custom Furniture: $75 flat

### Step 3: Test the System

```bash
# Create a test payout via API
curl -X POST http://localhost:8000/api/admin/installer-payouts/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "technician": 1,
    "installations": ["installation-uuid"],
    "notes": "Test payout"
  }'

# List pending payouts
curl -X GET http://localhost:8000/api/admin/installer-payouts/pending/ \
  -H "Authorization: Token YOUR_TOKEN"
```

## 📋 Usage

### For Admins

**View Pending Payouts:**
```
GET /api/admin/installer-payouts/pending/
```

**Approve a Payout:**
```bash
POST /api/admin/installer-payouts/{id}/approve/
{
  "action": "approve",
  "admin_notes": "Verified installations"
}
```

**Mark as Paid:**
```bash
POST /api/admin/installer-payouts/{id}/mark_paid/
{
  "payment_reference": "TXN-001",
  "payment_date": "2024-01-16T10:30:00Z"
}
```

### For Technicians

**View Own Payouts:**
```
GET /api/installation-systems/installer-payouts/
```

**Check Payout Details:**
```
GET /api/installation-systems/installer-payouts/{id}/
```

## 🎯 Common Tasks

### Adjust Payout Rates

```bash
# Update a configuration
curl -X PATCH http://localhost:8000/api/admin/payout-configurations/{id}/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rate_amount": "55.00"
  }'
```

### Generate Payout Report

```bash
# Get payouts by technician
curl -X GET "http://localhost:8000/api/admin/installer-payouts/by_technician/?status=approved" \
  -H "Authorization: Token YOUR_TOKEN"
```

### Manually Create Payout

```bash
POST /api/admin/installer-payouts/
{
  "technician": 1,
  "installations": ["uuid1", "uuid2"],
  "notes": "Monthly payout for January"
}
```

System automatically:
- Finds matching rate configurations
- Calculates total amount
- Generates breakdown
- Sets status to PENDING

## 📊 Workflow

```
Installation Completed
         ↓
   Payout Created (PENDING)
         ↓
   Admin Reviews
         ↓
    Approve/Reject
         ↓
  [If Approved] → Mark as Paid (PAID)
```

## 🔧 Configuration

### Enable Auto-Creation (Optional)

Add to `settings.py` or Celery configuration:

```python
CELERY_BEAT_SCHEDULE = {
    'auto-create-payouts': {
        'task': 'installation_systems.tasks.auto_create_payouts_for_completed_installations',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
}
```

### Email Configuration

Verify in `.env.prod`:
```
EMAIL_HOST=smtp.your-server.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=installations@hanna.co.zw
```

## 📖 Documentation

- **Complete Guide**: `INSTALLER_PAYOUT_DEPLOYMENT_GUIDE.md`
- **API Reference**: `INSTALLER_PAYOUT_API_REFERENCE.md`
- **Implementation Details**: `INSTALLER_PAYOUT_IMPLEMENTATION_SUMMARY.md`

## 🐛 Troubleshooting

### Payout Not Created Automatically

Check:
1. Installation status is COMMISSIONED or ACTIVE
2. Technician is assigned to installation
3. Matching payout configuration exists
4. Run manually: `python manage.py test installation_systems.tests.PayoutCalculationServiceTests`

### Email Not Sent

Check:
1. Email settings in `.env.prod`
2. Technician has valid email
3. Celery worker is running: `docker-compose logs celery_io_worker`

### Calculation Incorrect

1. Check payout configurations: `GET /api/admin/payout-configurations/`
2. Verify system size and installation type
3. Check priority and size ranges
4. Review calculation breakdown in payout detail

## 🆘 Support

### View Logs

```bash
# Backend logs
docker-compose logs -f backend

# Celery logs
docker-compose logs -f celery_io_worker

# All logs
docker-compose logs -f
```

### Run Tests

```bash
# All payout tests
docker-compose exec backend python manage.py test installation_systems

# Specific test
docker-compose exec backend python manage.py test installation_systems.tests.PayoutCalculationServiceTests.test_calculate_payout_amount_per_unit
```

### Django Shell

```bash
# Access Django shell
docker-compose exec backend python manage.py shell

# Example: Check configurations
>>> from installation_systems.models import PayoutConfiguration
>>> PayoutConfiguration.objects.filter(is_active=True)
```

## ✅ Verification Checklist

After setup, verify:

- [ ] Migrations applied successfully
- [ ] Default configurations created
- [ ] Can create test payout via API
- [ ] Approval workflow works
- [ ] Email notifications sent
- [ ] Technicians can view own payouts
- [ ] Admin can filter and search
- [ ] Calculation breakdown is accurate

## 🔐 Security Notes

- Only admins can approve/reject/pay
- Technicians see only their own data
- All actions logged with timestamp
- Payout amounts are immutable once calculated
- Installation status validated before payout creation

## 🎉 You're Ready!

The system is now configured and ready to use. Start by:

1. Reviewing and adjusting payout configurations
2. Testing with a completed installation
3. Approving test payout
4. Verifying email delivery
5. Training admin staff on the workflow

For detailed information, see the full documentation files.
