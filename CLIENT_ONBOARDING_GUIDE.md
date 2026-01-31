# Client Onboarding Guide - HANNA CRM

## Overview
This guide explains how to onboard clients to their respective client dashboards in the HANNA Management Frontend using data from:
- Installation System Records (ISR)
- Orders
- Customer Profile Information
- WhatsApp Contact Information

## The Problem
Clients trying to access `/client/my-installation` were getting 404 errors because:
1. No User account existed for them in Django
2. No CustomerProfile linked their Contact to a User
3. The backend `my_installations` endpoint requires `request.user.customer_profile` to exist

## Solution Architecture

```
ISR Record
    ↓
Contact (from WhatsApp)
    ↓
CustomerProfile (links Contact to User)
    ↓
User Account (Django auth)
    ↓
Client Can Access Portal
```

## Manual Onboarding Process

If you need to onboard clients one at a time:

1. **Get Contact WhatsApp ID** from ISR
2. **Create/Link User Account**:
   ```python
   from django.contrib.auth.models import User
   from customer_data.models import CustomerProfile
   from conversations.models import Contact
   
   # Get the contact
   contact = Contact.objects.get(whatsapp_id="1234567890")
   
   # Get or create user
   user, created = User.objects.get_or_create(
       username="customer_1234567890",  # Or use their email
       defaults={
           'email': contact.customer_profile.email,
           'first_name': contact.customer_profile.first_name,
           'last_name': contact.customer_profile.last_name,
       }
   )
   user.is_active = True
   user.save()
   
   # Link CustomerProfile to User
   profile = contact.customer_profile
   profile.user = user
   profile.save()
   ```

## Automated Onboarding (Recommended)

Use the management command to onboard clients in bulk from ISR records:

### Basic Usage
```bash
cd /path/to/whatsappcrm_backend
python manage.py onboard_clients_from_isr
```

### Preview Changes First (Dry-Run)
```bash
python manage.py onboard_clients_from_isr --dry-run
```

Output will show:
```
======================================================================
CLIENT ONBOARDING FROM ISR RECORDS
======================================================================

DRY RUN MODE - No changes will be saved

Processing 25 unique customers from 25 ISR records...

[1/25] ✓ Created user: john.doe + Profile
[2/25] ✓ Created user: jane.smith + Profile
[3/25]   Existing profile: 263771234567
...

======================================================================
ONBOARDING SUMMARY
======================================================================
Total Processed:      25
Users Created:        18
Profiles Created:     15
Profiles Updated:     0
Errors:               0

DRY RUN COMPLETE - No changes were saved. Run without --dry-run to apply.
======================================================================
```

### Actually Apply Changes
```bash
python manage.py onboard_clients_from_isr
```

### Filter by Installation Status
```bash
# Only onboard clients with commissioned installations
python manage.py onboard_clients_from_isr --status commissioned

# Onboard clients with multiple statuses
python manage.py onboard_clients_from_isr --status commissioned,active,in_progress
```

### Force Update Existing Profiles
```bash
# Update existing profiles with new user links or data
python manage.py onboard_clients_from_isr --force
```

## How Username is Generated

The command generates usernames as follows:

1. **If email exists**: Use email prefix
   - `john.doe@example.com` → `john.doe`
   - `jane_smith@company.co.zw` → `jane_smith`

2. **If no email**: Use WhatsApp ID
   - Contact 263771234567 → `client_263771234567`

3. **Ensure uniqueness**: If username exists, append counter
   - `john.doe` → `john.doe1` → `john.doe2` etc.

## Initial Passwords

After onboarding, clients receive a **random secure password**. They can:

1. Reset it at login (if password reset is configured)
2. Admin can reset via Django admin: `/admin/auth/user/{id}/change/`

## Verification

After running the command, verify onboarding:

```python
# Check if customer has user and profile
from customer_data.models import CustomerProfile

profile = CustomerProfile.objects.get(contact__whatsapp_id="263771234567")
print(f"User: {profile.user}")  # Should show User object, not None
print(f"Contact: {profile.contact.whatsapp_id}")
```

Or check in Django admin:
1. Go to `/admin/customer_data/customerprofile/`
2. Search by customer name
3. Verify `User` field is populated

## Testing Client Portal Access

1. Login as client with generated username
2. Navigate to `/client/my-installation`
3. Should see all commissioned/active installations

### If Still Getting 404

Check:
1. ✓ User exists in Django admin: `/admin/auth/user/`
2. ✓ CustomerProfile exists: `/admin/customer_data/customerprofile/`
3. ✓ CustomerProfile.user is set (not NULL)
4. ✓ Customer.contact exists and is linked
5. ✓ ISR record exists with `customer` set and `installation_status` in `['commissioned', 'active']`

### Debug Endpoint

Add this to the backend to test:

```python
# In installation_systems/views.py, in my_installations method
def my_installations(self, request):
    print(f"User: {request.user}")
    print(f"Has customer_profile: {hasattr(request.user, 'customer_profile')}")
    if hasattr(request.user, 'customer_profile'):
        print(f"Customer: {request.user.customer_profile}")
    ...
```

## API Endpoints for Client Portal

### Get My Installations
```
GET /crm-api/installation-system-records/my_installations/
Authorization: Bearer {client_token}
```

Returns installations with statuses: `commissioned`, `active`

### Get Installation Detail
```
GET /crm-api/installation-system-records/{id}/
Authorization: Bearer {client_token}
```

Only returns if user is the customer

### Get My Warranties
```
GET /crm-api/warranties/?customer={customer_id}
Authorization: Bearer {client_token}
```

### Get My Orders
```
GET /crm-api/orders/?customer={customer_id}
Authorization: Bearer {client_token}
```

## Troubleshooting

### Issue: Still Getting 404 on my_installations
**Cause**: Customer profile missing or not linked to user
**Fix**: Run onboarding command or link manually

### Issue: Client can't login
**Cause**: User account not created or inactive
**Fix**: Check `/admin/auth/user/`, ensure `is_active` is checked

### Issue: Client sees empty installations list
**Cause**: No ISR records with `installation_status` in `['commissioned', 'active']`
**Fix**: Create ISR records or update status to commissioned/active

### Issue: Wrong customer name in portal
**Cause**: CustomerProfile data not synced from ISR
**Fix**: Update CustomerProfile manually or use `--force` flag with onboarding command

## Bulk Operations for Support Team

### Activate All Onboarded Clients
```python
from django.contrib.auth.models import User
from customer_data.models import CustomerProfile

# Get all customers with users
profiles = CustomerProfile.objects.filter(user__isnull=False)
for profile in profiles:
    profile.user.is_active = True
    profile.user.save()
```

### Send Password Reset Emails
```python
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

users = User.objects.filter(customerprofile__isnull=False)
for user in users:
    token = default_token_generator.make_token(user)
    reset_url = f"https://hanna.co.zw/auth/reset-password/{user.id}/{token}/"
    # Send email with reset_url
```

### List All Onboarded Clients
```python
from customer_data.models import CustomerProfile

profiles = CustomerProfile.objects.filter(
    user__isnull=False,
    user__is_active=True
).select_related('user', 'contact')

for profile in profiles:
    print(f"{profile.user.username}: {profile.contact.whatsapp_id}")
```

## Next Steps

1. **Run onboarding command** to create accounts from existing ISR
2. **Configure password reset** (if not already done)
3. **Test client portal access** with test account
4. **Send welcome emails** to onboarded clients with login credentials
5. **Monitor login activity** in `/client/dashboard`
