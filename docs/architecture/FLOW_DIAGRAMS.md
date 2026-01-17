# WhatsApp Flow Diagrams

This document provides visual representations of all WhatsApp flows.

## Site Inspection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        SITE INSPECTION FLOW                      │
└─────────────────────────────────────────────────────────────────┘

Screen 1: WELCOME
├─ Title: "Site Assessment"
├─ Message: "Let's schedule a site assessment..."
└─ Action: Navigate to PERSONAL_INFO
    └─ Payload: All fields initialized to empty/default

Screen 2: PERSONAL_INFO
├─ Inputs:
│   ├─ assessment_full_name (TextInput, required)
│   └─ assessment_preferred_day (TextInput, required)
└─ Action: Navigate to COMPANY_INFO
    └─ Payload: Carries forward full_name + preferred_day

Screen 3: COMPANY_INFO
├─ Input:
│   └─ assessment_company_name (TextInput, required)
│       Helper: "Enter N/A if not applicable"
└─ Action: Navigate to LOCATION_INFO
    └─ Payload: Carries forward all previous + company_name

Screen 4: LOCATION_INFO
├─ Input:
│   └─ assessment_address (TextInput, required)
└─ Action: Navigate to CONTACT_INFO
    └─ Payload: Carries forward all previous + address

Screen 5: CONTACT_INFO (Terminal)
├─ Input:
│   └─ assessment_contact_info (TextInput, phone, required)
└─ Action: COMPLETE
    └─ Payload: ALL DATA
        ├─ assessment_full_name
        ├─ assessment_preferred_day
        ├─ assessment_company_name
        ├─ assessment_address
        └─ assessment_contact_info

Backend Processing:
├─ Generate assessment ID (SA-XXXXX)
├─ Create SiteAssessmentRequest
├─ Create/Update CustomerProfile
└─ Send confirmation message with assessment ID
```

---

## Loan Application Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     LOAN APPLICATION FLOW                        │
└─────────────────────────────────────────────────────────────────┘

Screen 1: WELCOME
├─ Title: "Loan Application"
├─ Message: "Welcome to our loan application service..."
└─ Action: Navigate to LOAN_TYPE
    └─ Payload: All fields initialized

Screen 2: LOAN_TYPE
├─ Input:
│   └─ loan_type (RadioButtons, required)
│       Options:
│       ├─ cash_loan: "💵 Cash Loan"
│       └─ product_loan: "📦 Product Loan"
└─ Action: Navigate to PERSONAL_INFO
    └─ Payload: Carries forward loan_type

Screen 3: PERSONAL_INFO
├─ Inputs:
│   ├─ loan_applicant_name (TextInput, required)
│   └─ loan_national_id (TextInput, required)
└─ Action: Navigate to EMPLOYMENT_INFO
    └─ Payload: Carries forward all previous + name + ID

Screen 4: EMPLOYMENT_INFO
├─ Inputs:
│   ├─ loan_employment_status (RadioButtons, required)
│   │   Options: employed, self_employed, unemployed (Other)
│   └─ loan_monthly_income (TextInput, number, required)
└─ Action: Navigate to LOAN_DETAILS
    └─ Payload: Carries forward all previous + employment + income

Screen 5: LOAN_DETAILS (Terminal)
├─ Inputs:
│   ├─ loan_request_amount (TextInput, number, optional)
│   │   Helper: "For Cash Loan: Enter amount. For Product: Enter 0"
│   └─ loan_product_interest (TextInput, optional)
│       Helper: "For Product Loan: Enter product name. For Cash: N/A"
└─ Action: COMPLETE
    └─ Payload: ALL DATA
        ├─ loan_type
        ├─ loan_applicant_name
        ├─ loan_national_id
        ├─ loan_employment_status
        ├─ loan_monthly_income
        ├─ loan_request_amount
        └─ loan_product_interest

Backend Processing:
├─ Interpret data based on loan_type:
│   ├─ If cash_loan: Use loan_request_amount
│   └─ If product_loan: Use loan_product_interest
├─ Create LoanApplication
├─ Create/Update CustomerProfile
└─ Send confirmation message with application details
```

---

## Solar Cleaning Flow (Fixed)

```
┌─────────────────────────────────────────────────────────────────┐
│                      SOLAR CLEANING FLOW                         │
│                    (Data Persistence Fixed)                      │
└─────────────────────────────────────────────────────────────────┘

Screen 1: WELCOME
└─ Action: Navigate to CUSTOMER_INFO
    └─ Payload: All 8 fields initialized

Screen 2: CUSTOMER_INFO
├─ Inputs:
│   ├─ full_name (TextInput, required)
│   └─ contact_phone (TextInput, phone, required)
└─ Action: Navigate to ROOF_DETAILS
    └─ Payload: NEW FORMAT ✓
        ├─ full_name: ${form.full_name}
        ├─ contact_phone: ${form.contact_phone}
        └─ + ALL OTHER FIELDS (from ${data.*})

Screen 3: ROOF_DETAILS
├─ Input:
│   └─ roof_type (RadioButtons, required)
│       Options: tile, ibr_metal, flat_concrete, other
└─ Action: Navigate to PANEL_DETAILS
    └─ Payload: CARRIES ALL DATA ✓
        ├─ full_name: ${data.full_name}
        ├─ contact_phone: ${data.contact_phone}
        ├─ roof_type: ${form.roof_type}
        └─ + remaining fields

Screen 4: PANEL_DETAILS
├─ Inputs:
│   ├─ panel_type (RadioButtons, required)
│   │   Options: monocrystalline, polycrystalline, not_sure
│   └─ panel_count (TextInput, number, required)
└─ Action: Navigate to SCHEDULE
    └─ Payload: CARRIES ALL DATA ✓
        ├─ Previous data
        ├─ panel_type: ${form.panel_type}
        └─ panel_count: ${form.panel_count}

Screen 5: SCHEDULE
├─ Inputs:
│   ├─ preferred_date (DatePicker, required)
│   └─ availability (RadioButtons, required)
│       Options: morning, afternoon
└─ Action: Navigate to LOCATION
    └─ Payload: CARRIES ALL DATA ✓
        ├─ All previous data
        ├─ preferred_date: ${form.preferred_date}
        └─ availability: ${form.availability}

Screen 6: LOCATION (Terminal)
├─ Input:
│   └─ address (TextInput, required)
└─ Action: COMPLETE
    └─ Payload: ALL 8 FIELDS ✓
        ├─ full_name
        ├─ contact_phone
        ├─ roof_type
        ├─ panel_type
        ├─ panel_count
        ├─ preferred_date
        ├─ availability
        └─ address: ${form.address}

Backend Processing:
├─ Create SolarCleaningRequest with all data
├─ Create/Update CustomerProfile
└─ Send confirmation message
    ├─ Customer name
    ├─ Panel count and type
    ├─ Roof type
    ├─ Location and date
    └─ Reference number
```

---

## Solar Installation Flow (With Order Verification)

```
┌─────────────────────────────────────────────────────────────────┐
│                   SOLAR INSTALLATION FLOW                        │
│                 (Order Verification Added)                       │
└─────────────────────────────────────────────────────────────────┘

Screen Flow:
1. WELCOME → 2. INSTALLATION_TYPE → 3. ORDER_INFO → 
4. SALES_INFO → 5. CUSTOMER_INFO → 6. SCHEDULE → 7. LOCATION

Screen 3: ORDER_INFO (Key Screen)
├─ Inputs:
│   ├─ order_number (TextInput, required)
│   │   Helper: "e.g., HAN-12345, 12345/PO, AV01/0034506"
│   └─ branch (RadioButtons, required)
│       Options: Harare, Bulawayo, Mutare, Other
└─ Note: Order number will be verified in backend

Backend Processing:
├─ ⚠️ ORDER VERIFICATION STEP:
│   ├─ Query: Order.objects.get(order_number=order_number)
│   ├─ If FOUND:
│   │   ├─ Link order to installation request
│   │   ├─ Add ✅ to confirmation message
│   │   └─ Continue processing
│   └─ If NOT FOUND:
│       ├─ Send error message to user:
│       │   "❌ Order Verification Failed
│       │    The order number '[number]' could not be found.
│       │    Please verify and try again..."
│       ├─ Mark flow_response.is_processed = False
│       └─ Do NOT create installation request
│
├─ Create InstallationRequest (if order valid)
│   ├─ associated_order = verified_order
│   ├─ order_number = user_input
│   └─ ... other fields
│
└─ Send confirmation message
    ├─ Shows order verification status
    ├─ All installation details
    └─ Reference number
```

---

## Data Flow Patterns

### Superset Pattern (Fixed in Solar Cleaning)

```
BEFORE (Buggy):
Screen 1: {a, b} → Payload: {a, b, c:"", d:"", e:""}
Screen 2: {c, d} → Payload: {c, d, e:""}  ❌ Lost a, b!
Screen 3: {e}    → Payload: {e}          ❌ Lost everything!

AFTER (Fixed):
Screen 1: {a, b} → Payload: {a:$form.a, b:$form.b, c:"", d:"", e:""}
Screen 2: {c, d} → Payload: {a:$data.a, b:$data.b, c:$form.c, d:$form.d, e:""}
Screen 3: {e}    → Payload: {a:$data.a, b:$data.b, c:$data.c, d:$data.d, e:$form.e}
                   ✓ All data preserved!
```

### Variable References

```
${form.field_name}  → Current screen input
${data.field_name}  → Previous screen data (passed in payload)

Example Navigation Payload:
{
  "field_from_form": "${form.field_from_form}",    // Just collected
  "field_from_prev": "${data.field_from_prev}",    // From previous screens
  "not_yet_set": "${data.not_yet_set}"             // Will be set later
}
```

---

## Backend Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              WHATSAPP FLOW RESPONSE PROCESSING                   │
└─────────────────────────────────────────────────────────────────┘

1. Receive Flow Completion
   ├─ WhatsApp sends webhook
   ├─ Contains flow_token and response_data
   └─ Includes all collected data in payload

2. Create Flow Response Record
   ├─ WhatsAppFlowResponse.objects.create()
   ├─ Store flow_token and response_data
   └─ Mark as is_processed=False initially

3. Route to Appropriate Processor
   ├─ processor_map = {
   │     'site_inspection_whatsapp': _process_site_inspection,
   │     'loan_application_whatsapp': _process_loan_application,
   │     'solar_installation_whatsapp': _process_solar_installation,
   │     'solar_cleaning_whatsapp': _process_solar_cleaning,
   │     'starlink_installation_whatsapp': _process_starlink_installation
   │   }
   └─ Call: processor(flow_response, contact, response_data)

4. Processor Execution
   ├─ Extract data from response_data['data']
   ├─ Validate required fields
   ├─ Perform business logic:
   │   ├─ Order verification (if applicable)
   │   ├─ Generate IDs (if needed)
   │   └─ Convert data types
   ├─ Get or create CustomerProfile
   ├─ Create business entity:
   │   ├─ SiteAssessmentRequest
   │   ├─ LoanApplication
   │   ├─ InstallationRequest
   │   └─ SolarCleaningRequest
   └─ Return (success: bool, notes: str)

5. Send Confirmation Message
   ├─ Build personalized message
   ├─ Include all relevant details
   ├─ Add reference number
   └─ send_whatsapp_message(contact.whatsapp_id, ...)

6. Update Flow Response Record
   ├─ Set is_processed = success
   ├─ Set processing_notes = notes
   ├─ Set processed_at = now() if success
   └─ Save record

7. Return Result
   └─ Return WhatsAppFlowResponse instance
```

---

## Error Handling

```
┌─────────────────────────────────────────────────────────────────┐
│                      ERROR SCENARIOS                             │
└─────────────────────────────────────────────────────────────────┘

Scenario 1: Missing Required Fields
├─ Validation: Check all([field1, field2, ...])
├─ If fails:
│   ├─ Return (False, "Missing required fields: ...")
│   └─ flow_response.is_processed = False
└─ No confirmation message sent

Scenario 2: Invalid Order Number (Solar Installation)
├─ Validation: Order.objects.get(order_number=...)
├─ If DoesNotExist:
│   ├─ Send error message to user:
│   │   "❌ Order Verification Failed..."
│   ├─ Return (False, "Order verification failed")
│   └─ flow_response.is_processed = False
└─ Installation request NOT created

Scenario 3: Data Type Conversion Errors
├─ Try: float(loan_monthly_income)
├─ Except (ValueError, TypeError):
│   └─ Use default value (e.g., 0)
└─ Continue processing (don't fail)

Scenario 4: Message Send Failure
├─ send_whatsapp_message() fails
├─ Entity is already created
├─ Processing marked as successful
└─ Message failure is logged but doesn't affect flow

General Pattern:
try:
    # Processing logic
    return True, notes
except Exception as e:
    error_msg = f"Error: {e}"
    logger.error(error_msg, exc_info=True)
    return False, error_msg
```

---

## Confirmation Message Templates

### Site Inspection
```
Thank you, {name}! 🙏

Your site assessment request has been successfully submitted.

*Details:*
📋 Assessment ID: {assessment_id}
📍 Location: {address}
📅 Preferred Day: {preferred_day}
🏢 Company: {company_name} (if provided)

Our team will contact you at {contact_info} to confirm the assessment schedule.

Reference: {assessment_id}
```

### Loan Application (Cash)
```
Thank you, {name}! 🙏

Your loan application has been successfully submitted for review.

*Application Details:*
💰 Loan Type: Cash Loan
💵 Amount Requested: ${amount} USD
👤 Employment: {employment_status}
💼 Monthly Income: ${monthly_income} USD

Our finance team will review your application and contact you within 24-48 hours.

Reference: #{application_id}
```

### Solar Installation (With Order Verification)
```
Thank you, {name}! 🙏

Your solar installation request has been successfully submitted.

*Details:*
📋 Order: {order_number} ✅ Order verified
🏢 Branch: {branch}
📍 Location: {address}
📅 Preferred Date: {preferred_date}
⏰ Time: {availability}
👤 Sales Rep: {sales_person}

Our installation team will contact you at {contact_phone}.

Alternative Contact: {alt_contact_name} ({alt_contact_phone})

Reference: #{installation_request_id}
```

---

## Testing Flow

```
Test Suite Organization:
├─ test_new_flow_definitions.py (Structure Tests)
│   ├─ FlowStructureValidationTest
│   │   ├─ test_site_inspection_flow_structure
│   │   ├─ test_loan_application_flow_structure
│   │   └─ test_solar_cleaning_flow_data_persistence
│   ├─ FlowDataFieldsTest
│   │   ├─ test_site_inspection_required_fields
│   │   ├─ test_loan_application_required_fields
│   │   └─ test_solar_cleaning_required_fields
│   └─ FlowCompletionActionTest
│       ├─ test_site_inspection_completion_has_payload
│       ├─ test_loan_application_completion_has_payload
│       └─ test_solar_cleaning_completion_has_payload
│
└─ test_flow_processors.py (Backend Tests)
    ├─ SiteInspectionProcessorTest
    │   ├─ test_process_site_inspection_success
    │   └─ test_process_site_inspection_missing_fields
    ├─ LoanApplicationProcessorTest
    │   ├─ test_process_cash_loan_success
    │   └─ test_process_product_loan_success
    ├─ SolarInstallationProcessorTest
    │   ├─ test_process_with_valid_order
    │   └─ test_process_with_invalid_order
    └─ SolarCleaningProcessorTest
        └─ test_process_solar_cleaning_with_confirmation
```

---

This diagram document provides a complete visual reference for understanding all WhatsApp flows, their data flow patterns, backend processing, error handling, and testing structure.
