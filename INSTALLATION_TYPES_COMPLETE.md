# Installation Types Expansion - Complete Implementation

## Overview
Successfully expanded installation request system to include 4 types with dedicated WhatsApp interactive flows and conversational fallbacks. All installation types now collect location pins after form submission.

## Installation Types

### 1. Solar Installation ✅ (Existing - Enhanced)
- **Flow Name**: `solar_installation_inquiry`
- **Interactive Flow**: `solar_installation_whatsapp` 
- **Fields**: Order number, customer info, solar capacity, schedule, address
- **Location**: Requested after submission

### 2. Starlink Installation ✅ (Existing - Enhanced)
- **Flow Name**: `starlink_installation_request`
- **Interactive Flow**: `starlink_installation_whatsapp`
- **Fields**: Order number, customer info, kit type, mount location, schedule, address
- **Location**: Requested after submission

### 3. Hybrid Installation 🆕 (NEW)
- **Flow Name**: `hybrid_installation_request`
- **Interactive Flow**: `hybrid_installation_whatsapp`
- **Fields**: 
  - Order number (optional)
  - Customer info (name, phone, alt contact)
  - Starlink kit type (standard/high_performance/roam)
  - Solar capacity (text input)
  - Mount location
  - Schedule (date, availability)
  - Address
- **Location**: Requested after submission

### 4. Custom Furniture Installation 🆕 (NEW)
- **Flow Name**: `custom_furniture_installation_request`
- **Interactive Flow**: `custom_furniture_installation_whatsapp`
- **Fields**:
  - Order number (optional)
  - Furniture type (dropdown: kitchen cabinets, bedroom suite, office furniture, living room, dining set, wardrobes, custom other)
  - Specifications (textarea)
  - Customer info (name, phone, alt contact)
  - Schedule (date, availability including full_day option)
  - Address
- **Location**: Requested after submission

## Files Created/Modified

### New Files Created ✅

1. **`flows/definitions/hybrid_installation_flow.py`**
   - Conversational (message-based) flow
   - Checks if interactive flow is published
   - Sends WhatsApp Flow or fallback message

2. **`flows/definitions/custom_furniture_installation_flow.py`**
   - Conversational (message-based) flow
   - Checks if interactive flow is published
   - Sends WhatsApp Flow or fallback message

3. **`flows/definitions/hybrid_installation_whatsapp_flow.py`** (from previous session)
   - Interactive flow definition (5 screens)
   - Version 7.3 Meta WhatsApp Flow format

4. **`flows/definitions/custom_furniture_installation_whatsapp_flow.py`** (from previous session)
   - Interactive flow definition (4 screens)
   - Version 7.3 Meta WhatsApp Flow format

### Files Modified ✅

1. **`flows/definitions/main_menu_flow.py`**
   - Changed installation submenu from button type to list type
   - Added all 4 installation types with descriptions:
     - ☀️ Solar Installation - "Solar power system setup"
     - 🛰️ Starlink Installation - "Starlink satellite internet setup"
     - ⚡ Hybrid Installation - "Combined Starlink + Solar setup"
     - 🪑 Custom Furniture - "Furniture delivery/installation"
   - Added transitions to new flows
   - Added switch_flow steps for hybrid and custom furniture

2. **`flows/management/commands/load_flows.py`**
   - Added imports for HYBRID_INSTALLATION_FLOW and CUSTOM_FURNITURE_INSTALLATION_FLOW
   - Added both flows to ALL_FLOWS list

3. **`customer_data/models.py`** (from previous session)
   - Updated InstallationRequest model with new types
   - Added enhanced location fields

4. **`flows/whatsapp_flow_response_processor.py`** (from previous session)
   - Added processors for hybrid and custom furniture
   - All processors request location pins after submission

5. **`flows/services.py`** (from previous session)
   - Enhanced location handler for installations

## Database Changes Required

### Migration Needed ⚠️
The `InstallationRequest` model has new fields that need migration:

```python
# New fields added to InstallationRequest:
- installation_type (max_length increased to 50)
- location_latitude (DecimalField)
- location_longitude (DecimalField)
- location_name (CharField)
- location_address (TextField)
- location_url (URLField)
```

## WhatsApp Flow Sync Required

### Flows to Sync ⚠️
Two new interactive flows need to be published to Meta:
1. `hybrid_installation_whatsapp`
2. `custom_furniture_installation_whatsapp`

## Deployment Steps

### 1. Run Migrations
```powershell
docker compose exec backend python manage.py makemigrations customer_data
docker compose exec backend python manage.py migrate
```

### 2. Load Conversational Flows
```powershell
docker compose exec backend python manage.py load_flows
```

### 3. Sync WhatsApp Interactive Flows
```powershell
docker compose exec backend python manage.py sync_whatsapp_flows --publish --force
```

This will:
- Upload all flow definitions to Meta
- Publish the flows to production
- Force overwrite any existing flows

### 4. Verify Installation Menu
Test the complete flow:
1. Send "menu" to WhatsApp bot
2. Select "🛠️ Request Installation"
3. Verify all 4 installation types appear in the list
4. Test each installation type:
   - Select installation type
   - Complete the interactive form
   - Verify confirmation message
   - Verify location pin request
   - Share location
   - Verify location saved in database

## Installation Submenu Structure

### Before (Button Type - 3 buttons max)
```
Installation Services
Great! Which type of installation service do you need?

[☀️ Solar]  [🛰️ Starlink]  [Go Back]
```

### After (List Type - Unlimited rows)
```
Installation Services
Great! Which type of installation service do you need?
Select an installation type

[Select Installation ▼]

Installation Types:
├─ ☀️ Solar Installation - Solar power system setup
├─ 🛰️ Starlink Installation - Starlink satellite internet setup
├─ ⚡ Hybrid Installation - Combined Starlink + Solar setup
└─ 🪑 Custom Furniture - Furniture delivery/installation

Navigation:
└─ 🔙 Back to Main Menu - Return to main menu
```

## Location Pin Collection Flow

### All Installation Types Follow Same Pattern:

1. **User submits installation form** → Interactive flow completion
2. **System sends confirmation** → "Thank you! Your [type] installation request #[ID] has been received."
3. **System requests location** → "Please share your exact installation location using WhatsApp's location pin feature..."
4. **User shares location** → Sends GPS coordinates
5. **System processes location** → Saves to database with coordinates, name, address, URL
6. **System confirms** → "Location saved: [name] at [coordinates]"

### Fields Saved:
- `location_latitude`: GPS latitude (decimal degrees)
- `location_longitude`: GPS longitude (decimal degrees)
- `location_name`: Place name from WhatsApp location
- `location_address`: Full address from WhatsApp location
- `location_url`: Google Maps URL (if available)

## Response Processors

### Processor Map (in `flows/whatsapp_flow_response_processor.py`):
```python
processor_map = {
    'solar_installation_whatsapp': _process_solar_installation,
    'starlink_installation_whatsapp': _process_starlink_installation,
    'hybrid_installation_whatsapp': _process_hybrid_installation,
    'custom_furniture_installation_whatsapp': _process_custom_furniture_installation,
    'solar_cleaning_whatsapp': _process_solar_cleaning,
    'site_inspection_whatsapp': _process_site_inspection,
    'loan_application_whatsapp': _process_loan_application,
}
```

## Testing Checklist

- [ ] Run migrations successfully
- [ ] Load conversational flows without errors
- [ ] Sync WhatsApp interactive flows to Meta
- [ ] Verify all 4 installation types appear in menu
- [ ] Test solar installation flow + location
- [ ] Test starlink installation flow + location
- [ ] Test hybrid installation flow + location
- [ ] Test custom furniture installation flow + location
- [ ] Verify location data saved correctly in database
- [ ] Test "Go Back" navigation
- [ ] Test fallback messages when flows unavailable

## Database Verification

After testing, verify installation requests in Django admin:

```python
# Should see all fields populated:
- installation_type: 'solar', 'starlink', 'hybrid', or 'custom_furniture'
- full_name, contact_phone, address
- preferred_datetime, availability
- location_latitude, location_longitude
- location_name, location_address
- status: 'pending'
```

## Architecture Notes

### Why Separate Flow Files?
- Meta WhatsApp API requires one `flow_id` per interactive flow
- Cannot use conditional branching within a single flow definition
- Each installation type needs its own JSON schema file
- Conversational flows (message-based) check which interactive flows are available

### Location Tracking Design
- Uses `conversation_context` flags to track pending location requests
- Separate flags for assessments vs installations
- Location handler intercepts location messages before normal flow processing
- Enhanced fields provide richer context than basic lat/long

### Backward Compatibility
- Legacy `latitude` and `longitude` fields retained
- New `location_*` fields are additional, not replacements
- Old installations continue working unchanged
- New installations use enhanced location tracking

## Next Steps (Optional Enhancements)

1. **Add Location Validation**
   - Verify coordinates are within service area
   - Check distance from branch locations
   - Suggest nearest branch based on location

2. **Installation Type Icons**
   - Add visual indicators in admin panel
   - Create reports grouped by type
   - Dashboard widgets for each type

3. **Scheduling Integration**
   - Check technician availability by type
   - Route optimization for installations
   - Separate calendars for different types

4. **Form Enhancements**
   - Add photo upload for furniture specifications
   - Include power capacity calculator for solar
   - Kit type availability checker for Starlink

## Summary

✅ **4 installation types** with dedicated flows  
✅ **Interactive list menu** showing all options  
✅ **Location pin collection** for all types  
✅ **Enhanced location fields** with full context  
✅ **Message-based fallbacks** when flows unavailable  
✅ **Backward compatible** with existing installations

The installation request system is now fully modular and scalable for future installation types.
