# Quick Test Guide - WhatsApp Flow Fixes

## What Was Fixed
Fixed validation errors preventing "Loan Application" and "Solar Panel Cleaning Request" flows from publishing to Meta.

## Changes Summary
1. ✅ Removed unsupported `input-type: "number"` (changed to `input-type: "text"`)
2. ✅ Fixed type mismatch in loan application payload initialization
3. ✅ All 7 WhatsApp flows now pass validation

## Testing the Fixes

### Step 1: Sync the Fixed Flows

```bash
cd whatsappcrm_backend

# Sync Loan Application flow
python manage.py sync_whatsapp_flows --flow loan_application --publish

# Sync Solar Cleaning flow
python manage.py sync_whatsapp_flows --flow solar_cleaning --publish
```

### Expected Output
Both commands should complete successfully without validation errors:
```
✓ Flow synced and published! Flow ID: 25161592953504621
✓ Flow synced and published! Flow ID: 1583302476187088
```

### Step 2: Test in WhatsApp

#### Loan Application Flow
1. Send trigger message to your WhatsApp Business number (e.g., "apply for loan")
2. Flow should present the interactive form
3. Complete each screen:
   - Welcome → Start Application
   - Loan Type → Select Cash Loan or Product Loan → Continue
   - Personal Info → Enter name and ID → Continue
   - **Employment Info** → Enter employment status and monthly income → Continue ✅
   - Loan Details → Enter amount and product interest → Submit

**Critical Test**: The flow should **NOT crash** at the Employment Info screen anymore!

#### Solar Cleaning Flow
1. Send trigger message (e.g., "solar cleaning")
2. Complete the flow:
   - Welcome → Get Started
   - Customer Info → Enter name and phone → Continue
   - Roof Details → Select roof type → Continue
   - **Panel Details** → Select panel type and enter count → Continue ✅
   - Schedule → Pick date and time → Continue
   - Location → Enter address → Submit

**Critical Test**: The panel count field should accept numeric input properly.

### Step 3: Verify Backend Processing

Check that numeric values are being received and processed correctly:

```bash
# Check Django logs for flow responses
tail -f /path/to/django/logs

# Or query the database
python manage.py shell
>>> from flows.models import WhatsAppFlowResponse
>>> responses = WhatsAppFlowResponse.objects.filter(
...     whatsapp_flow__name__in=['loan_application_whatsapp', 'solar_cleaning_whatsapp']
... ).order_by('-created_at')[:5]
>>> for r in responses:
...     print(r.response_data)
```

### Troubleshooting

#### If sync still fails:
1. Check Meta app configuration is active:
   ```python
   python manage.py shell
   >>> from meta_integration.models import MetaAppConfig
   >>> config = MetaAppConfig.objects.get_active_config()
   >>> print(f"Using: {config.name}")
   ```

2. Verify API credentials are valid

3. Check for network/firewall issues blocking Meta API

#### If flow works but data not saved:
- Check `flows/whatsapp_flow_response_processor.py` for proper handling
- Verify numeric string parsing:
  ```python
  monthly_income = float(data.get('loan_monthly_income', '0'))
  panel_count = int(data.get('panel_count', '0'))
  ```

## Success Criteria
✅ Both flows sync without errors
✅ Both flows publish successfully
✅ Employment Info screen doesn't crash in Loan Application flow
✅ Panel count field works in Solar Cleaning flow
✅ All data is received and processed correctly

## Documentation
- Full analysis: `WHATSAPP_FLOW_VALIDATION_FIX.md`
- Updated guide: `WHATSAPP_FLOW_FIX_SUMMARY.md`

## Support
If you encounter issues:
1. Check the error logs from sync command
2. Verify flow JSON structure in the database
3. Test with Meta's Flow Builder tool
4. Review Meta's API error responses for specific validation failures
