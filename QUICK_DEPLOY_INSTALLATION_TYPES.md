# Quick Deployment Commands

## Step 1: Apply Database Migrations
```powershell
docker compose exec backend python manage.py makemigrations customer_data
docker compose exec backend python manage.py migrate
```

## Step 2: Load Conversational Flows
```powershell
docker compose exec backend python manage.py load_flows
```

## Step 3: Sync WhatsApp Interactive Flows
```powershell
docker compose exec backend python manage.py sync_whatsapp_flows --publish --force
```

## Step 4: Restart Services (if needed)
```powershell
docker compose restart backend celery_worker
```

## Verification Commands

### Check Installation Types in Database
```powershell
docker compose exec backend python manage.py shell
```
Then in Python shell:
```python
from customer_data.models import InstallationRequest
# Check field choices
print(InstallationRequest.INSTALLATION_TYPES)
# Should show: [('starlink', 'Starlink Installation'), ('solar', 'Solar Installation'), ('hybrid', 'Hybrid Installation'), ('custom_furniture', 'Custom Furniture Installation'), ('residential', 'Residential Installation'), ('commercial', 'Commercial Installation')]
```

### Check Loaded Flows
```powershell
docker compose exec backend python manage.py shell
```
Then in Python shell:
```python
from flows.models import Flow
# List all flows
Flow.objects.filter(is_active=True).values_list('name', 'friendly_name')
# Should include: hybrid_installation_request, custom_furniture_installation_request
```

### Check Synced WhatsApp Flows
```powershell
docker compose exec backend python manage.py shell
```
Then in Python shell:
```python
from flows.models import WhatsAppFlow
# List synced flows
WhatsAppFlow.objects.filter(sync_status='published').values_list('name', 'friendly_name', 'flow_id')
# Should include: hybrid_installation_whatsapp, custom_furniture_installation_whatsapp
```

## Testing the Installation Menu

1. **Open WhatsApp** and message your bot number
2. **Send**: `menu`
3. **Select**: "🛠️ Request Installation"
4. **Verify**: You should see a list with 4 installation types:
   - ☀️ Solar Installation
   - 🛰️ Starlink Installation  
   - ⚡ Hybrid Installation
   - 🪑 Custom Furniture
5. **Test each type**: Select one and complete the form
6. **Verify location request**: After submission, bot should ask for location pin
7. **Share location**: Use WhatsApp's location sharing feature
8. **Verify confirmation**: Bot should confirm location saved

## Troubleshooting

### If migrations fail:
```powershell
# Check existing migrations
docker compose exec backend python manage.py showmigrations customer_data

# If there are conflicts, try:
docker compose exec backend python manage.py makemigrations --merge
```

### If flow loading fails:
```powershell
# Check for syntax errors in flow definitions
docker compose exec backend python -c "from flows.definitions.hybrid_installation_flow import HYBRID_INSTALLATION_FLOW; print('Hybrid flow OK')"
docker compose exec backend python -c "from flows.definitions.custom_furniture_installation_flow import CUSTOM_FURNITURE_INSTALLATION_FLOW; print('Furniture flow OK')"
```

### If WhatsApp flow sync fails:
```powershell
# Check Meta API credentials
docker compose exec backend python manage.py shell
```
Then:
```python
from django.conf import settings
print(settings.WHATSAPP_ACCESS_TOKEN[:10] + "...")  # Should show token prefix
print(settings.WHATSAPP_BUSINESS_ACCOUNT_ID)  # Should show account ID
```

### If location handler not working:
```powershell
# Check recent logs
docker compose logs backend --tail=100 | grep -i location
docker compose logs celery_worker --tail=100 | grep -i location
```

## Expected Output

### After migrations:
```
Operations to perform:
  Apply all migrations: customer_data
Running migrations:
  Applying customer_data.XXXX_installationrequest_location_fields... OK
```

### After load_flows:
```
Loading flow: Main Menu
Loading flow: Solar Installation Inquiry
Loading flow: Starlink Installation Request
Loading flow: Hybrid Installation Request ← NEW
Loading flow: Custom Furniture Installation Request ← NEW
...
Successfully loaded X flows.
```

### After sync_whatsapp_flows:
```
Syncing WhatsApp Flows...
✓ solar_installation_whatsapp (published)
✓ starlink_installation_whatsapp (published)
✓ hybrid_installation_whatsapp (published) ← NEW
✓ custom_furniture_installation_whatsapp (published) ← NEW
✓ solar_cleaning_whatsapp (published)
✓ site_inspection_whatsapp (published)
✓ loan_application_whatsapp (published)
Successfully synced X flows.
```

## Complete in ~5 minutes! 🚀
