# Remaining WhatsApp Templates That Need Fixing

## Overview
After fixing the 3 templates that were explicitly rejected by WhatsApp, **10 additional templates** have been identified with similar problematic patterns that will cause rejection when synced to Meta's WhatsApp Business API.

## Status Summary
- ✅ **Fixed (3)**: Ready for WhatsApp sync
- ⚠️ **Needs Fixing (10)**: Will be rejected by WhatsApp if synced
- ✅ **No Issues (2)**: Safe to sync

---

## ✅ Templates Already Fixed (3)

### 1. hanna_human_handover_flow ✅
- **Status**: Fixed in commit `f4df0a5`
- **Changes**: Removed `or` expressions, flattened variables
- **Ready to sync**: Yes

### 2. hanna_message_send_failure ✅
- **Status**: Fixed in commit `f4df0a5`
- **Changes**: Removed `or` expressions, flattened variables
- **Ready to sync**: Yes

### 3. hanna_invoice_processed_successfully ✅
- **Status**: Fixed in commit `f4df0a5`
- **Changes**: Removed format filters, conditionals, flattened variables
- **Ready to sync**: Yes

---

## ⚠️ Templates That Need Fixing (10)

### 1. hanna_new_order_created
**Priority**: High (likely to be synced soon)

**Issues**:
```python
# Line 16
{{ order.customer.get_full_name or order.customer.contact.name }}

# Line 18-19 (nested attributes)
{{ order.name }}
{{ order.order_number }}

# Line 20
{{ order.amount or '0.00' }}
```

**Required Changes**:
- Flatten `order_customer_name` (handle `or` in Python)
- Flatten `order_name`, `order_number`
- Flatten `order_amount` (format in Python)

**Calling Code**: Check `customer_data` signals

---

### 2. hanna_new_online_order_placed
**Priority**: CRITICAL (uses unsupported `{% for %}` loop)

**Issues**:
```python
# Line 29
{{ contact.name or contact.whatsapp_id }}

# Line 32-33 (nested attributes)
{{ created_order_details.order_number }}
{{ created_order_details.amount }}

# Lines 42-43 (UNSUPPORTED BY WHATSAPP)
{% for item in cart_items %}- {{ item.quantity }} x {{ item.name }}
{% endfor %}
```

**Required Changes**:
- Flatten all variables
- **Remove `{% for %}` loop** - WhatsApp doesn't support loops!
- Build cart items list as a single string in Python before passing to template

**Calling Code**: Check flows that create online orders

---

### 3. hanna_new_installation_request
**Priority**: High (complex template with multiple issues)

**Issues**:
```python
# Line 70
{{ contact.name or contact.whatsapp_id }}

# Line 74-75
{{ order_number or 'N/A' }}
{{ assessment_number or 'N/A' }}

# Line 81 (UNSUPPORTED CONDITIONAL + FILTER)
{% if install_alt_name and install_alt_name|lower != 'n/a' %}
- Alt. Contact: {{ install_alt_name }} ({{ install_alt_phone }})
{% endif %}

# Line 83-84 (UNSUPPORTED CONDITIONAL)
{% if install_location_pin and install_location_pin.latitude %}
- Location Pin: https://www.google.com/maps/search/?api=1&query={{ install_location_pin.latitude }},{{ install_location_pin.longitude }}
{% endif %}

# Line 85
{{ install_availability|title }}
```

**Required Changes**:
- Flatten `contact_name` (handle `or` in Python)
- Flatten `order_number`, `assessment_number` (default to 'N/A' in Python)
- Remove `{% if %}` blocks - build text conditionally in Python
- Remove `|title` filter - apply `.title()` in Python
- Flatten all nested attributes

**Calling Code**: Check installation request flows

---

### 4. hanna_new_starlink_installation_request
**Priority**: Medium

**Issues**:
```python
# Line 94
{{ contact.name or contact.whatsapp_id }}

# Line 100 (UNSUPPORTED CONDITIONAL)
{% if install_location_pin and install_location_pin.latitude %}
- Location Pin: ...
{% endif %}

# Line 103, 106
{{ install_availability|title }}
{{ install_kit_type|title }}
```

**Required Changes**:
- Same pattern as `hanna_new_installation_request`
- Flatten variables, remove conditionals, remove filters

---

### 5. hanna_new_solar_cleaning_request
**Priority**: Medium

**Issues**:
```python
# Line 116
{{ contact.name or contact.whatsapp_id }}

# Line 123-125
{{ cleaning_roof_type|title }}
{{ cleaning_panel_type|title }}
{{ cleaning_availability|title }}

# Line 126-127 (UNSUPPORTED CONDITIONAL)
{% if cleaning_location_pin and cleaning_location_pin.latitude %}
...
{% endif %}
```

**Required Changes**:
- Flatten variables, remove conditionals, remove filters

---

### 6. hanna_admin_order_and_install_created
**Priority**: Medium

**Issues**:
```python
# Line 136
{{ contact.name or contact.username }}

# Line 137
{{ target_contact.0.name or customer_whatsapp_id }}
```

**Required Changes**:
- Flatten `admin_name` (handle `or` in Python)
- Flatten `customer_name` (handle list index and `or` in Python)

---

### 7. hanna_new_site_assessment_request
**Priority**: Medium

**Issues**:
```python
# Line 148
{{ contact.name or contact.whatsapp_id }}
```

**Required Changes**:
- Flatten `contact_name` (handle `or` in Python)

---

### 8. hanna_job_card_created_successfully
**Priority**: Low (email integration, less frequently used)

**Issues**:
```python
# Lines 166-170 (nested attributes)
{{ job_card.job_card_number }}
{{ customer.first_name }} {{ customer.last_name }}
{{ job_card.product_description }}
{{ job_card.product_serial_number }}
{{ job_card.reported_fault }}
```

**Required Changes**:
- Flatten all nested attributes

**Calling Code**: Check `email_integration/tasks.py`

---

### 9. hanna_new_placeholder_order_created
**Priority**: Low

**Issues**:
```python
# Line 191
{{ contact.name or contact.whatsapp_id }}
```

**Required Changes**:
- Flatten `contact_name` (handle `or` in Python)

---

### 10. hanna_admin_24h_window_reminder
**Priority**: Low

**Issues**:
```python
# Line 211
{{ recipient.first_name or recipient.username }}
```

**Required Changes**:
- Flatten `recipient_name` (handle `or` in Python)

---

## ✅ Templates Without Issues (2)

### 1. hanna_order_payment_status_updated ✅
- Uses only simple variables: `{{ order_name }}`, `{{ order_number }}`, `{{ new_status }}`
- **Status**: Safe to sync as-is

### 2. hanna_assessment_status_updated ✅
- Uses only simple variables: `{{ assessment_id }}`, `{{ new_status }}`
- **Status**: Safe to sync as-is

---

## Implementation Strategy

### Phase 1: Critical Templates (Week 1)
Fix templates with **unsupported features** that will definitely break:
1. `hanna_new_online_order_placed` - Has `{% for %}` loop
2. `hanna_new_installation_request` - Has `{% if %}` blocks
3. `hanna_new_starlink_installation_request` - Has `{% if %}` blocks
4. `hanna_new_solar_cleaning_request` - Has `{% if %}` blocks

### Phase 2: High Priority Templates (Week 2)
Fix frequently used templates:
1. `hanna_new_order_created`
2. `hanna_admin_order_and_install_created`
3. `hanna_new_site_assessment_request`

### Phase 3: Lower Priority Templates (Week 3)
Fix remaining templates:
1. `hanna_job_card_created_successfully`
2. `hanna_new_placeholder_order_created`
3. `hanna_admin_24h_window_reminder`

---

## Testing Checklist

For each template fix:
- [ ] Identify where the template is called
- [ ] Update calling code to provide flattened variables
- [ ] Test template rendering with sample data
- [ ] Verify sync conversion produces clean `{{1}}`, `{{2}}` placeholders
- [ ] Test actual notification delivery (if possible)
- [ ] Update both `definitions.py` and `load_notification_templates.py`

---

## Quick Reference: Common Patterns

### Pattern: `{{ var or 'default' }}`
```python
# BEFORE (template)
{{ contact.name or contact.whatsapp_id }}

# AFTER (template)
{{ contact_name }}

# Calling code
template_context['contact_name'] = contact.name or contact.whatsapp_id
```

### Pattern: `{{ var|title }}`
```python
# BEFORE (template)
{{ status|title }}

# AFTER (template)
{{ status }}

# Calling code
template_context['status'] = status.title()
```

### Pattern: `{% if condition %}`
```python
# BEFORE (template)
{% if location %}
- Location: {{ location }}
{% endif %}

# AFTER (template)
{{ location_text }}

# Calling code
template_context['location_text'] = f"- Location: {location}" if location else ""
```

### Pattern: Nested attributes
```python
# BEFORE (template)
{{ order.customer.name }}

# AFTER (template)
{{ customer_name }}

# Calling code
template_context['customer_name'] = order.customer.name
```

---

## Conclusion

**Total Work Remaining**: 10 templates need fixing before they can be synced to WhatsApp.

**Estimated Effort**: 2-3 weeks (assuming 2-3 templates per week with testing)

**Risk if Not Fixed**: These templates will be rejected by WhatsApp when synced, causing notification failures.

**Recommendation**: Prioritize Phase 1 templates immediately due to critical unsupported features (`{% for %}` and `{% if %}`).
