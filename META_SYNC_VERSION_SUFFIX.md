# Meta Sync Version Suffix

## Overview

This feature adds version suffixes to WhatsApp flows and message templates when syncing with Meta's WhatsApp Business API. This helps differentiate new syncs from previously synced items, particularly useful after database resets or when needing to maintain multiple versions.

## Configuration

The version suffix is configured via the `META_SYNC_VERSION_SUFFIX` setting in Django settings.

### Default Configuration

By default, the suffix is set to `v1_02`:

```python
# In whatsappcrm_backend/whatsappcrm_backend/settings.py
# Note: Must use underscores only (no dots/periods) as Meta only allows lowercase letters and underscores
META_SYNC_VERSION_SUFFIX = os.getenv('META_SYNC_VERSION_SUFFIX', 'v1_02')
```

### Environment Variable Override

You can override the default value by setting the `META_SYNC_VERSION_SUFFIX` environment variable:

```bash
# In your .env file
# Note: Use underscores instead of dots (e.g., v2_00 not v2.00)
META_SYNC_VERSION_SUFFIX=v2_00
```

Or when running Docker:

```bash
docker-compose run -e META_SYNC_VERSION_SUFFIX=v2_00 backend python manage.py sync_whatsapp_flows
```

### Important: Naming Requirements

Meta's WhatsApp API has strict naming requirements for templates and flows:
- **Only lowercase letters and underscores are allowed**
- No periods, dots, hyphens, or other special characters
- Examples of valid suffixes: `v1_02`, `v2_00`, `prod_v1`
- Examples of invalid suffixes: `v1.02`, `v2-00`, `V1_02` (uppercase)

## How It Works

### WhatsApp Flows

When creating a new WhatsApp flow, the version suffix is automatically appended to the flow name:

- **Original flow name:** `Solar Installation`
- **Synced flow name:** `Solar Installation_v1_02`

This happens in the `WhatsAppFlowService.create_flow()` method in `flows/whatsapp_flow_service.py`.

### Message Templates

When syncing notification templates, the version suffix is appended to the template name:

- **Original template name:** `new_online_order_placed`
- **Synced template name:** `new_online_order_placed_v1_02`

This happens in the `sync_meta_templates` management command in `flows/management/commands/sync_meta_templates.py`.

**Important:** When sending template messages to Meta, the system automatically appends the version suffix to the template name. This ensures that messages use the correct versioned template that was synced to Meta.

## Usage

### Syncing WhatsApp Flows

```bash
# Sync all flows with default version suffix
python manage.py sync_whatsapp_flows --all

# Sync specific flow
python manage.py sync_whatsapp_flows --flow=solar_installation

# Sync and publish
python manage.py sync_whatsapp_flows --all --publish
```

### Syncing Message Templates

```bash
# Sync all templates with default version suffix
python manage.py sync_meta_templates

# Dry run to see what would be synced
python manage.py sync_meta_templates --dry-run
```

## Console Output

When syncing, you'll see output indicating both the original and versioned names:

### Flow Sync Output
```
Processing flow: Solar Installation (Interactive)...
  Flow record updated in database
  Syncing with Meta...
  ✓ Flow synced as draft! Flow ID: 123456789
```

### Template Sync Output
```
Processing template: 'new_online_order_placed' (will be synced as 'new_online_order_placed_v1_02')...
  SUCCESS: Template 'new_online_order_placed_v1_02' created successfully. ID: 987654321
```

## Version History

When you need to create a new version (e.g., after significant changes or database issues):

1. Update the environment variable (remember to use underscores, not dots):
   ```bash
   META_SYNC_VERSION_SUFFIX=v1_03
   ```

2. Re-run the sync commands:
   ```bash
   python manage.py sync_whatsapp_flows --all
   python manage.py sync_meta_templates
   ```

This will create new flows and templates on Meta with the new version suffix, without conflicting with existing ones.

## Database Considerations

### Important Notes

- The version suffix is **only applied when syncing with Meta**, not in the local database
- Local flow names (`WhatsAppFlow.name`) and template names (`NotificationTemplate.name`) remain unchanged
- The `flow_id` and `meta_template_id` fields store the IDs returned by Meta after syncing

### Database Fields

**WhatsAppFlow model:**
- `name`: Local identifier (e.g., `solar_installation_whatsapp`)
- `friendly_name`: Display name (e.g., `Solar Installation`)
- `flow_id`: Meta's flow ID (returned after sync)

**NotificationTemplate model:**
- `name`: Local identifier (e.g., `new_online_order_placed`)
- `meta_template_id`: Meta's template ID (returned after sync)

## Troubleshooting

### Issue: Templates/Flows Already Exist on Meta

If you get errors about duplicate names on Meta, it means:
1. The items already exist with the current version suffix
2. You need to either:
   - Use a different version suffix
   - Delete the old items from Meta
   - Use the existing items (don't re-sync)

### Issue: Version Suffix Not Applied

Check:
1. The setting is correctly defined in `settings.py`
2. The environment variable is properly set (if using override)
3. You're running the sync commands from the correct directory
4. Django is loading the correct settings file

### Issue: Wrong Version Showing in Meta

This can happen if:
1. The environment variable was changed after sync
2. Multiple sync operations ran with different settings

Solution: Re-sync with the correct version suffix using `--force` flag:
```bash
python manage.py sync_whatsapp_flows --all --force
```

## Technical Details

### Code Locations

1. **Settings:** `whatsappcrm_backend/whatsappcrm_backend/settings.py`
   - Defines `META_SYNC_VERSION_SUFFIX`

2. **Flow Sync:** `whatsappcrm_backend/flows/whatsapp_flow_service.py`
   - Method: `WhatsAppFlowService.create_flow()`
   - Applies suffix when creating flows on Meta

3. **Template Sync:** `whatsappcrm_backend/flows/management/commands/sync_meta_templates.py`
   - Applies suffix when creating templates on Meta

4. **Tests:** `whatsappcrm_backend/flows/test_version_suffix.py`
   - Comprehensive test coverage for version suffix functionality

### Testing

Run the tests to verify version suffix functionality:

```bash
cd whatsappcrm_backend
python manage.py test flows.test_version_suffix
```

Expected output:
```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
......
----------------------------------------------------------------------
Ran 6 tests in 0.XXXs

OK
```

## Best Practices

1. **Consistent Versioning:** Use a consistent versioning scheme (e.g., v1_00, v1_01, v1_02)
2. **Naming Rules:** Always use underscores, never dots or other special characters
3. **Lowercase Only:** Keep all characters lowercase to comply with Meta's requirements
4. **Document Changes:** Keep track of what changed in each version
5. **Test First:** Always test with `--dry-run` before syncing templates
6. **Backup:** Before major version changes, backup your Meta configuration
7. **Clean Up:** Periodically clean up old versions on Meta to avoid clutter

## Support

For issues or questions:
1. Check the logs: `docker-compose logs backend`
2. Review the error messages in the sync command output
3. Verify your Meta App Configuration in Django admin
4. Consult Meta's WhatsApp Business API documentation
