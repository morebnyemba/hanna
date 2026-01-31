# Quick Start: Client Onboarding Command

## In One Command

```bash
# Test first (see what would happen)
python manage.py onboard_clients_from_isr --dry-run

# Then execute (creates User accounts and CustomerProfile links)
python manage.py onboard_clients_from_isr
```

## What It Does

The management command `onboard_clients_from_isr` solves the **404 error on client portal** by:

1. **Finding all customers** from ISR records with status `commissioned` or `active`
2. **Creating User accounts** for each customer with auto-generated username and password
3. **Linking CustomerProfile** to the User so client portal endpoint works
4. **Preventing duplicates** - won't recreate if user already exists

## Example Output

```
======================================================================
CLIENT ONBOARDING FROM ISR RECORDS
======================================================================

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
======================================================================
```

## How to Use

### From Backend Directory

```bash
cd whatsappcrm_backend

# Preview changes (DRY RUN)
python manage.py onboard_clients_from_isr --dry-run

# Apply changes
python manage.py onboard_clients_from_isr
```

### From Docker Container

```bash
# Preview
docker-compose exec backend python manage.py onboard_clients_from_isr --dry-run

# Apply
docker-compose exec backend python manage.py onboard_clients_from_isr
```

## Command Options

```bash
# Dry run (preview only, no changes)
python manage.py onboard_clients_from_isr --dry-run

# Force update existing profiles with new user links
python manage.py onboard_clients_from_isr --force

# Filter by specific statuses
python manage.py onboard_clients_from_isr --status commissioned
python manage.py onboard_clients_from_isr --status commissioned,active,in_progress

# Combine options
python manage.py onboard_clients_from_isr --dry-run --status commissioned --force
```

## Generated Credentials

Usernames are generated from customer email or WhatsApp ID:
- Email: `john.doe@example.com` → `john.doe`
- WhatsApp: `263771234567` → `client_263771234567`

Passwords are **randomly generated** - clients must:
1. Use password reset at login
2. Or admin can reset in Django admin

## Verification

After running, verify onboarding succeeded:

### Check in Django Admin

1. Go to `/admin/auth/user/` - should see new users with onboarded customers
2. Go to `/admin/customer_data/customerprofile/` - check that `User` field is populated
3. Go to `/admin/installation_systems/installationsystemrecord/` - verify customer has ISR records

### Test Client Login

1. Get a generated username (e.g., `john.doe`)
2. Go to `/client/login`
3. Reset password with "Forgot Password"
4. Login and navigate to `/client/my-installation`
5. Should see their installations (no more 404!)

### API Test

```bash
# Get auth token for client user
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john.doe","password":"RESET_PASSWORD"}'

# Test my_installations endpoint
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/crm-api/installation-systems/installation-system-records/my_installations/
```

Should return 200 with list of installations (not 404).

## Troubleshooting

### Command not found
```
Error: "Unknown command: 'onboard_clients_from_isr'"
```
**Fix**: 
- Verify file exists: `ls whatsappcrm_backend/customer_data/management/commands/onboard_clients_from_isr.py`
- Verify `__init__.py` files exist in:
  - `whatsappcrm_backend/customer_data/management/`
  - `whatsappcrm_backend/customer_data/management/commands/`

### No ISR records
```
Processing 0 unique customers...
```
**Fix**: Create ISR records first and set `installation_status` to `commissioned` or `active`

### Users already exist
```
[1/25]   Existing profile: 263771234567
```
**Solution**: This is normal - means user already onboarded. Use `--force` to update.

## Full Documentation

See `CLIENT_ONBOARDING_GUIDE.md` in the root directory for comprehensive guide.
