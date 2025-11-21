# WhatsApp Message Template Fix Guide

## Problem

Three message templates were being rejected by WhatsApp's Business API with the error:
```
INVALID_FORMAT: Your template has incorrect parameters (e.g. parameters are 
missing brackets or parameter contains text instead of numerals).
```

### Affected Templates
- `hanna_human_handover_flow_v1_02`
- `hanna_invoice_processed_successfully_v1_02`
- `hanna_message_send_failure_v1_02`

## Root Cause

The templates contained Jinja2 expressions that are not compatible with WhatsApp's template format:

1. **Default value expressions**: `{{ var or 'default text' }}`
2. **Jinja2 filters**: `{{ var|format(...) }}`, `{{ var|title }}`
3. **Conditional expressions**: `{{ "%.2f"|format(var) if var else '0.00' }}`
4. **Nested attributes**: `{{ contact.name or contact.whatsapp_id }}`

When the `sync_meta_templates` command processes these templates, the regex pattern:
```python
jinja_pattern = r'\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}'
```

Only matches simple variable names. It doesn't match expressions with `or`, `|`, `if`, etc.

### Example of What Went Wrong

**OLD Template (Rejected):**
```
Contact *{{ related_contact.name or related_contact.whatsapp_id }}* requires assistance.
Reason: {{ error or 'Unknown error' }}
```

**What WhatsApp Received:**
```
Contact *{{ related_contact.name or related_contact.whatsapp_id }}* requires assistance.
Reason: {{ error or 'Unknown error' }}
```
(No variables extracted, literal text remained → **REJECTED**)

**NEW Template (Accepted):**
```
Contact *{{ related_contact_name }}* requires assistance.
Reason: {{ error_details }}
```

**What WhatsApp Receives:**
```
Contact *{{1}}* requires assistance.
Reason: {{2}}
```
(Clean numeric placeholders → **ACCEPTED**)

## Solution

### 1. Template Changes

Simplified the three affected templates to use only simple variable placeholders:

#### `hanna_human_handover_flow`
- **Before**: `{{ related_contact.name or related_contact.whatsapp_id }}`
- **After**: `{{ related_contact_name }}`

- **Before**: `{{ template_context.last_bot_message or 'User requested help...' }}`
- **After**: `{{ last_bot_message }}`

#### `hanna_message_send_failure`
- **Before**: `{{ related_contact.name or related_contact.whatsapp_id }}`
- **After**: `{{ related_contact_name }}`

- **Before**: `{{ template_context.message.error_details or 'Unknown error' }}`
- **After**: `{{ error_details }}`

#### `hanna_invoice_processed_successfully`
- **Before**: `{{ attachment.sender }}`, `{{ attachment.filename }}`
- **After**: `{{ sender }}`, `{{ filename }}`

- **Before**: `{{ "%.2f"|format(order.amount) if order.amount is not none else '0.00' }}`
- **After**: `{{ order_amount }}`

- **Before**: `{{ customer.full_name or customer.contact_name }}`
- **After**: `{{ customer_name }}`

### 2. Code Changes

Updated the code that calls these templates to provide the simplified variables:

#### In `notifications/services.py` (line 56):
```python
if related_contact:
    render_context['contact'] = str(related_contact)
    # Add related_contact_name for templates that need it
    render_context['related_contact_name'] = related_contact.name or related_contact.whatsapp_id
```

#### In `email_integration/tasks.py` (lines 577-585):
```python
template_context={
    'attachment': attachment_dict, 'order': order_dict, 'customer': customer_dict,
    # Flattened variables for simplified template
    'sender': attachment_dict['sender'],
    'filename': attachment_dict['filename'],
    'order_number': order_dict['order_number'],
    'order_amount': f"{order_dict['amount']:.2f}",
    'customer_name': customer_dict['full_name'] or customer_dict['contact_name']
}
```

## How to Apply the Fix

### Step 1: Update Database Templates
Run the management command to update templates in the database:
```bash
cd whatsappcrm_backend
python manage.py load_notification_templates
```

Or use the definitions-based command if available:
```bash
python manage.py loaddata flows/management/commands/definitions.py
```

### Step 2: Sync to WhatsApp
Sync the updated templates to Meta's WhatsApp Business API:
```bash
python manage.py sync_meta_templates
```

Or run in dry-run mode first to preview:
```bash
python manage.py sync_meta_templates --dry-run
```

### Step 3: Verify
Check the Meta Business Manager to confirm the templates are approved:
1. Log into Meta Business Manager
2. Navigate to WhatsApp Business Account → Message Templates
3. Check status of the three templates (should be "APPROVED")

## Best Practices for Future Templates

To avoid similar issues in the future:

### ✅ DO:
- Use simple variable placeholders: `{{ variable_name }}`
- Flatten nested attributes in calling code: `contact_name` instead of `contact.name`
- Provide default values in Python code, not templates
- Apply formatting in Python before passing to template

### ❌ DON'T:
- Use `or` expressions: `{{ var or 'default' }}`
- Use Jinja2 filters: `{{ var|title }}`, `{{ var|format(...) }}`
- Use conditionals: `{{ var if condition else 'default' }}`
- Use nested attributes: `{{ contact.name }}`
- Include literal strings in variable expressions

### Example of Good Template Design

**Template:**
```
Hello {{ customer_name }}!
Your order #{{ order_number }} for ${{ order_total }} is confirmed.
Status: {{ order_status }}
```

**Calling Code:**
```python
queue_notifications_to_users(
    template_name='order_confirmation',
    template_context={
        'customer_name': customer.get_full_name() or customer.contact.name or 'Valued Customer',
        'order_number': order.order_number,
        'order_total': f"{order.amount:.2f}",
        'order_status': order.status.upper()
    }
)
```

## Testing

Run the tests to verify template rendering:
```bash
cd whatsappcrm_backend
python manage.py test notifications.test_template_rendering
```

## References

- [WhatsApp Business API Template Guidelines](https://developers.facebook.com/docs/whatsapp/message-templates/guidelines)
- [WhatsApp Template Components](https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components)
