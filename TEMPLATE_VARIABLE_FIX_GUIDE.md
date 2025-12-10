# Template Variable Fix Guide

## Overview

This document explains the fixes made to WhatsApp notification templates to ensure compatibility with Meta's WhatsApp Business API.

## Problem Statement

Meta's WhatsApp Business API requires templates to use simple numbered placeholders (`{{1}}`, `{{2}}`, etc.) when synced to their platform. However, our templates were using Jinja2 syntax that is not supported by Meta:

- **Nested attributes**: `{{ contact.name }}`, `{{ order.customer.contact.name }}`
- **Or expressions**: `{{ contact.name or contact.whatsapp_id }}`
- **Filters**: `{{ new_status|title }}`, `{{ loan_type|replace('_', ' ') }}`
- **Conditionals**: `{% if condition %}...{% endif %}`
- **Loops**: `{% for item in items %}...{% endfor %}`

When these templates were synced to Meta, they would be rejected with an `INVALID_FORMAT` error.

## Solution

We implemented a two-part solution:

### 1. Simplified Template Variables

All templates now use simple variable names without any Jinja2 logic:

**Before:**
```jinja2
A new order has been placed by *{{ contact.name or contact.whatsapp_id }}*.

*Items Ordered:*
{% for item in cart_items %}- {{ item.quantity }} x {{ item.name }}
{% endfor %}

Status: {{ new_status|title }}
```

**After:**
```jinja2
A new order has been placed by *{{ contact_name }}*.

*Items Ordered:*
{{ cart_items_list }}

Status: {{ new_status }}
```

### 2. Python-Based Variable Flattening

The `notifications/services.py` now contains comprehensive logic to:
- Flatten nested objects
- Handle default values (replacing `or` expressions)
- Apply formatting (replacing filters)
- Render conditional sections
- Format lists (replacing loops)

## Templates Fixed

All 15 notification templates have been updated:

1. `hanna_new_order_created` - Order creation notifications
2. `hanna_new_online_order_placed` - Online order notifications
3. `hanna_order_payment_status_updated` - Payment status updates
4. `hanna_assessment_status_updated` - Assessment status updates
5. `hanna_new_installation_request` - Installation requests
6. `hanna_new_starlink_installation_request` - Starlink installations
7. `hanna_new_solar_cleaning_request` - Solar cleaning requests
8. `hanna_admin_order_and_install_created` - Admin-created orders
9. `hanna_new_site_assessment_request` - Site assessment requests
10. `hanna_job_card_created_successfully` - Job card creation
11. `hanna_human_handover_flow` - Human handover notifications
12. `hanna_new_placeholder_order_created` - Placeholder orders
13. `hanna_message_send_failure` - Message send failures
14. `hanna_admin_24h_window_reminder` - 24-hour window reminders
15. `hanna_invoice_processed_successfully` - Invoice processing

## Files Modified

- `whatsappcrm_backend/flows/definitions/load_notification_templates.py` - Template definitions
- `whatsappcrm_backend/flows/management/commands/definitions.py` - Template definitions for sync
- `whatsappcrm_backend/notifications/services.py` - Variable flattening logic

## Variable Mapping Reference

### Contact Variables
- `contact.name or contact.whatsapp_id` → `contact_name`
- `related_contact.name or related_contact.whatsapp_id` → `related_contact_name`
- `recipient.first_name or recipient.username` → `recipient_name`

### Order Variables
- `created_order_details.order_number` → `order_number`
- `created_order_details.amount` → `order_amount`
- `order.name` → `order_name`
- `order.customer.get_full_name or order.customer.contact.name` → `customer_name`

### Conditional Sections
- `{% if install_alt_name %}...{% endif %}` → `install_alt_contact_line` (empty if not applicable)
- `{% if install_location_pin.latitude %}...{% endif %}` → `install_location_pin_line`
- `{% if resolution_notes %}...{% endif %}` → `resolution_notes_section`
- `{% if loan_request_amount %}...{% endif %}` → `loan_amount_line`

### Filters Replaced
- `|title` → Applied in Python with `.title()`
- `|replace('_', ' ')` → Applied in Python with `.replace('_', ' ')`
- `|lower` → Applied in Python with `.lower()`
- `"%.2f"|format(amount)` → Applied in Python with f-string formatting

### List Rendering
- `{% for item in cart_items %}...{% endfor %}` → `cart_items_list` (pre-formatted string)

## Validation

Run the validation script to ensure templates are Meta-compatible:

```bash
python validate_templates.py
```

Expected output:
```
✅ All templates are valid and Meta-compatible!
✅ No problematic patterns found.
```

## Testing Templates

### Local Testing (with Django)
```bash
cd whatsappcrm_backend
python manage.py test notifications.test_template_rendering
```

### Syncing to Meta
```bash
# Preview changes
python manage.py sync_meta_templates --dry-run

# Actual sync
python manage.py sync_meta_templates
```

### Verifying in Meta Business Manager
1. Log into [Meta Business Manager](https://business.facebook.com/)
2. Navigate to WhatsApp Business Account → Message Templates
3. Check that all templates have "APPROVED" status
4. Verify no templates show "REJECTED" or "INVALID_FORMAT" errors

## Best Practices for Future Templates

### ✅ DO:
- Use simple variable placeholders: `{{ variable_name }}`
- Flatten nested data in Python before passing to template
- Handle defaults in Python: `name = contact.name or contact.whatsapp_id`
- Apply formatting in Python: `amount = f"{order.amount:.2f}"`
- Keep templates simple and readable

### ❌ DON'T:
- Use `or` expressions: `{{ var or 'default' }}`
- Use Jinja2 filters: `{{ var|title }}`
- Use conditionals: `{% if condition %}...{% endif %}`
- Nest attributes: `{{ contact.name }}`
- Include literal strings: `{{ 'text' }}`
- Use loops: `{% for item in items %}...{% endfor %}`

## Troubleshooting

### Template Rejected by Meta

If a template is rejected:

1. Check the error message in Meta Business Manager
2. Run `python validate_templates.py` to check for problematic patterns
3. Verify the template definition in `definitions.py`
4. Check that calling code provides all required variables
5. Review the variable flattening logic in `services.py`

### Missing Variables

If variables are not rendering:

1. Check that the calling code provides the variable in `template_context`
2. Verify the variable name matches what's used in the template
3. Check the flattening logic in `services.py` for that variable
4. Use Django shell to test rendering:
   ```python
   from notifications.utils import render_template_string
   template = "Hello {{ name }}"
   context = {"name": "John"}
   result = render_template_string(template, context)
   print(result)  # Should print: Hello John
   ```

## Related Documentation

- [WhatsApp Message Templates Guidelines](https://developers.facebook.com/docs/whatsapp/message-templates/guidelines)
- [WhatsApp Template Components](https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components)
- Previous fix: `ISSUE_RESOLUTION_TEMPLATE_FIX.md`
- Previous fix: `PR_SUMMARY_TEMPLATE_FIX.md`

## Summary

All notification templates have been updated to use Meta-compatible variable syntax. The templates are simpler and more maintainable, with all logic moved to Python code. This ensures:

✅ Templates will be accepted by Meta's WhatsApp Business API  
✅ Notifications will be delivered successfully  
✅ Templates are easier to understand and maintain  
✅ Better separation of concerns (templates for structure, Python for logic)
