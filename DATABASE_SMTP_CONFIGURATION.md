# Database SMTP Configuration

## Overview

SMTP settings can now be stored in the database instead of the `.env` file, making it easier to manage email configurations without restarting the application.

---

## Why Database Configuration?

**Benefits:**
- ✅ **No restart required** - Change SMTP settings without restarting Django/Celery
- ✅ **Easy management** - Configure via Django Admin interface
- ✅ **Multiple configs** - Store multiple SMTP configurations and switch between them
- ✅ **Audit trail** - Track when configurations are created/updated
- ✅ **Secure** - Passwords stored in database, not in version control
- ✅ **Fallback support** - Still supports `.env` configuration as fallback

---

## How It Works

The system checks for SMTP configuration in this order:

1. **Database** - Looks for an active `SMTPConfig` record
2. **Django Settings** - Falls back to `.env` file configuration

If an active database configuration exists, it will be used. Otherwise, the system uses the settings from `.env`.

---

## Setting Up Database SMTP Configuration

### Step 1: Access Django Admin

1. Navigate to: `https://backend.hanna.co.zw/admin/`
2. Log in with your admin credentials

### Step 2: Create SMTP Configuration

1. Go to: **Email Integration** → **SMTP Configurations**
2. Click **Add SMTP Configuration**

### Step 3: Fill in Configuration Details

**Configuration Name:**
```
Name: Primary Mail Server
```

**SMTP Server Settings:**
```
Host: mail.hanna.co.zw
Port: 587
Username: installations@hanna.co.zw
Password: [your SMTP password]
```

**Encryption:**
```
☑ Use TLS (for port 587)
☐ Use SSL (for port 465)
```

**Note:** Do not enable both TLS and SSL. Choose one based on your mail server.

**Email Settings:**
```
From Email: installations@hanna.co.zw
Timeout: 10 seconds
```

**Active Status:**
```
☑ Is Active
```

### Step 4: Save

Click **Save** - The system will automatically:
- Deactivate any other SMTP configurations
- Start using this configuration immediately
- Log the change

---

## Common Port Configurations

| Port | Encryption | When to Use |
|------|-----------|-------------|
| 587 | TLS (STARTTLS) | Most common, recommended |
| 465 | SSL | Older systems, some providers |
| 25 | None | Plain SMTP (not recommended) |

---

## Testing Your Configuration

After creating the configuration, test it:

```bash
docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
```

**Expected output if successful:**
```
1. Checking Email/SMTP Configuration...
   ℹ Using SMTP config from database: Primary Mail Server
   ✓ SMTP configuration looks valid

   Testing SMTP connection...
   ✓ Test email sent successfully to admin@example.com
```

---

## Switching Between Configurations

### Create Multiple Configurations

You can store multiple SMTP configurations (e.g., primary server, backup server):

1. Create first config: "Primary Mail Server" (active)
2. Create second config: "Backup SMTP Server" (inactive)

### Switch Configurations

To switch:
1. Go to Django Admin → SMTP Configurations
2. Edit the configuration you want to use
3. Check **Is Active**
4. Save

The system automatically deactivates other configurations.

---

## Disabling Database Configuration

To use `.env` file instead:

1. Go to Django Admin → SMTP Configurations
2. Edit the active configuration
3. Uncheck **Is Active**
4. Save

The system will fall back to `.env` settings.

---

## Security Considerations

### Password Storage

⚠️ **IMPORTANT SECURITY NOTICE:**
- Passwords are stored as **plain text** in the database by default
- Database should have proper access controls and backups
- Only admin users can access SMTP configurations
- Consider implementing field-level encryption for production use

### Best Practices

1. **Use app-specific passwords** - Generate dedicated passwords for SMTP (Gmail, Office 365)
2. **Never use main account passwords** - Always use app-specific or service-specific passwords
3. **Limit admin access** - Only trusted administrators should access SMTP configs
4. **Enable database encryption** - Encrypt database backups and consider field-level encryption
5. **Monitor changes** - Regularly review admin logs for configuration changes
6. **Rotate credentials** - Periodically update SMTP passwords
7. **Use TLS/SSL** - Always enable encryption for SMTP connections
8. **Backup configurations** - Include in database backups with proper encryption

### For Production Environments

Consider implementing:
- **Django encrypted fields** - Use libraries like `django-encrypted-model-fields`
- **Environment-based secrets** - Use secrets management services (AWS Secrets Manager, etc.)
- **Access auditing** - Log all SMTP configuration access
- **Two-factor authentication** - Require 2FA for admin access

---

## Troubleshooting

### Configuration Not Working

**Check active status:**
```bash
docker exec -it whatsappcrm_backend_app python manage.py shell
```
```python
from email_integration.models import SMTPConfig
config = SMTPConfig.objects.get_active_config()
print(f"Active config: {config}")
```

**Output should show:**
```
Active config: Primary Mail Server - mail.hanna.co.zw:587 (Active)
```

### Authentication Still Failing

**Possible causes:**
1. Wrong password in database configuration
2. Account locked or disabled
3. IP not whitelisted
4. App password required but not used

**Solutions:**
1. Edit the configuration and update the password
2. Verify account works via webmail
3. Contact email administrator
4. Generate and use app-specific password

### Falling Back to .env

If the database configuration fails, the system automatically falls back to `.env`:

```
[WARNING] No active SMTP Configuration found in database. Falling back to Django settings.
```

This ensures email continues working even if database config has issues.

---

## Migration from .env to Database

### Current State (.env file)
```env
EMAIL_HOST=mail.hanna.co.zw
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=installations@hanna.co.zw
EMAIL_HOST_PASSWORD=YourPassword
DEFAULT_FROM_EMAIL=installations@hanna.co.zw
```

### Steps to Migrate

1. **Keep .env as fallback** (don't delete it yet)

2. **Create database config** with the same settings:
   - Name: "Primary Mail Server"
   - Host: mail.hanna.co.zw
   - Port: 587
   - Use TLS: ✓
   - Username: installations@hanna.co.zw
   - Password: YourPassword
   - From Email: installations@hanna.co.zw
   - Is Active: ✓

3. **Test the configuration:**
   ```bash
   docker exec -it whatsappcrm_backend_app python manage.py validate_notification_setup --test-email
   ```

4. **Verify logs show database usage:**
   ```
   ℹ Using SMTP config from database: Primary Mail Server
   ```

5. **Monitor for a few days** to ensure everything works

6. **Optional:** Remove SMTP settings from `.env` (keep as fallback or remove)

---

## API for Programmatic Access

### Get Active Configuration

```python
from email_integration.models import SMTPConfig

# Get active config
config = SMTPConfig.objects.get_active_config()

if config:
    print(f"Using: {config.name}")
    print(f"Host: {config.host}:{config.port}")
else:
    print("No active database config, using settings")
```

### Create Configuration

```python
from email_integration.models import SMTPConfig

SMTPConfig.objects.create(
    name='New SMTP Server',
    host='smtp.example.com',
    port=587,
    username='user@example.com',
    password='password',
    use_tls=True,
    from_email='noreply@example.com',
    is_active=True
)
```

### Switch Active Configuration

```python
# Deactivate all
SMTPConfig.objects.all().update(is_active=False)

# Activate one
config = SMTPConfig.objects.get(name='Backup SMTP Server')
config.is_active = True
config.save()  # Auto-deactivates others
```

---

## Admin Actions

The Django Admin interface provides:

- **List view** - See all configurations with status
- **Edit inline** - Toggle active status directly
- **Search** - Find configurations by name, host, username
- **Filter** - Filter by active status, TLS/SSL
- **Audit** - Created/updated timestamps

---

## Best Practices

1. **Name configurations clearly** - "Primary Mail Server", "Backup SMTP", etc.
2. **Test before activating** - Create as inactive, test, then activate
3. **Keep .env as fallback** - In case database is unavailable
4. **Monitor logs** - Watch for configuration switches
5. **Document changes** - Note why configurations were changed
6. **Regular testing** - Test SMTP monthly with validation command

---

## Compatibility

- ✅ Works with existing `.env` configuration
- ✅ No code changes required in tasks
- ✅ Transparent to email sending functions
- ✅ Backward compatible
- ✅ Can switch back to `.env` anytime

---

## FAQ

**Q: Do I need to restart after changing the configuration?**
A: No! Changes are applied immediately.

**Q: Can I have multiple active configurations?**
A: No. Only one can be active at a time. The system automatically deactivates others.

**Q: What happens if I delete the active configuration?**
A: The system falls back to `.env` settings.

**Q: Is the password encrypted in the database?**
A: It's stored as plain text in the database. Use Django encryption tools for additional security.

**Q: Can I use this for multiple domains?**
A: Yes! Create separate configurations for each domain and switch as needed.

**Q: Does this work with Gmail?**
A: Yes! Use app-specific passwords for Gmail.

---

## Example Configurations

### Gmail
```
Host: smtp.gmail.com
Port: 587
Use TLS: ✓
Username: your-email@gmail.com
Password: [16-character app password]
```

### Office 365
```
Host: smtp.office365.com
Port: 587
Use TLS: ✓
Username: your-email@company.com
Password: [your password or app password]
```

### Custom Mail Server (TLS)
```
Host: mail.example.com
Port: 587
Use TLS: ✓
Username: user@example.com
Password: [your password]
```

### Custom Mail Server (SSL)
```
Host: mail.example.com
Port: 465
Use SSL: ✓
Use TLS: ☐
Username: user@example.com
Password: [your password]
```

---

## Summary

**Before:**
- SMTP settings in `.env` file
- Required restart to change
- Hard to manage multiple configs

**Now:**
- SMTP settings in database (optional)
- Change without restart
- Easy to switch between configs
- Backward compatible with `.env`

**Next Steps:**
1. Create database configuration via Django Admin
2. Test with validation command
3. Monitor logs to confirm it's working
4. Optionally remove from `.env` or keep as fallback

---

**Last Updated:** December 10, 2025
**Feature Added:** Database SMTP Configuration
**Status:** Ready to use
