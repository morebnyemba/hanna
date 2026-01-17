# Implementable Issues - Week 1 Sprint
## Hanna Installation Lifecycle Operating System - Phase 1

Based on the comprehensive gap analysis, here are **7 focused issues** that can be completed within one week and begin transforming Hanna into an Installation Lifecycle Operating System supporting multiple installation types: **Solar (SSI)**, **Starlink (SLI)**, **Custom Furniture (CFI)**, and **Solar+Starlink Hybrid (SSI)**.

---

## Issue 1: Create Installation System Record (ISR) Model Foundation

**Priority:** CRITICAL  
**Estimated Time:** 3-4 days  
**Type:** Backend - Data Model

### Description
Create the foundational `InstallationSystemRecord` model that will serve as the master object for tracking every installation throughout its lifecycle. This model supports multiple installation types: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid Solar+Starlink (SSI). This is the core concept from the PDF that's currently missing.

**Note:** While the PDF focuses on solar, the system already handles multiple installation types (starlink, solar, custom_furniture, hybrid) as seen in `InstallationRequest.INSTALLATION_TYPES`. This model generalizes the SSR concept to support all installation types.

### Acceptance Criteria
- [ ] Create `InstallationSystemRecord` model in a new Django app called `installation_systems`
- [ ] Include fields:
  - System identifier (auto-generated unique ID)
  - Linked customer profile (ForeignKey to CustomerProfile)
  - Linked order (ForeignKey to Order)
  - **Installation type (choices: solar, starlink, custom_furniture, hybrid)** - Matches InstallationRequest.INSTALLATION_TYPES
  - System size/capacity (DecimalField, nullable) - For solar/starlink (kW or Mbps)
  - Capacity unit (choices: kW, Mbps, units) - To support different measurement types
  - System classification (choices: residential, commercial, hybrid)
  - Installation date (DateField)
  - Installation status (choices: pending, in_progress, commissioned, active, decommissioned)
  - Commissioning date (DateField, nullable)
  - Remote monitoring ID (CharField, nullable) - For solar/starlink
  - GPS coordinates (latitude, longitude)
  - Installation address
  - Assigned technician(s) (ManyToMany to Technician)
- [ ] Create relationship: `installed_components` ManyToMany to SerializedItem
- [ ] Add timestamps (created_at, updated_at)
- [ ] Create database migrations
- [ ] Add Django admin interface for ISR
- [ ] Write model tests for all installation types

### Technical Notes
- Place in new app: `whatsappcrm_backend/installation_systems/`
- Use UUID for primary key
- Add `__str__` method returning: "ISR-{id} - {customer_name} - {installation_type} - {system_size}{unit}"
- Examples: "ISR-123 - John Doe - solar - 5kW", "ISR-456 - Jane Smith - starlink - 100Mbps", "ISR-789 - Bob Jones - custom_furniture - 3units"
- Create reverse relationships from Order, CustomerProfile, InstallationRequest
- Installation type field should match `InstallationRequest.INSTALLATION_TYPES` for consistency

### Files to Create/Modify
- `whatsappcrm_backend/installation_systems/models.py`
- `whatsappcrm_backend/installation_systems/admin.py`
- `whatsappcrm_backend/installation_systems/tests.py`
- `whatsappcrm_backend/whatsappcrm_backend/settings.py` (add app)

---

## Issue 2: Add System Bundles / Installation Packages Model

**Priority:** HIGH  
**Estimated Time:** 2-3 days  
**Type:** Backend - Data Model + API

### Description
Create a `SystemBundle` model to represent pre-configured installation packages for all installation types:
- **Solar packages:** "3kW Residential Solar Kit", "5kW Commercial Solar System"
- **Starlink packages:** "Starlink Residential Kit", "Starlink Business Kit"
- **Custom Furniture packages:** "Office Furniture Set", "Bedroom Furniture Set"
- **Hybrid packages:** "Solar + Starlink Residential Bundle"

This enables controlled offerings where retailers can only sell approved bundles across all installation types.

### Acceptance Criteria
- [ ] Create `SystemBundle` model in `products_and_services` app
- [ ] Include fields:
  - Name (e.g., "3kW Residential Solar Kit", "Starlink Business Kit", "Office Furniture Set")
  - SKU/code
  - Description
  - **Installation type (choices: solar, starlink, custom_furniture, hybrid)** - Matches InstallationRequest.INSTALLATION_TYPES
  - System capacity (DecimalField, nullable) - For solar/starlink
  - Capacity unit (choices: kW, Mbps, units)
  - Bundle classification (choices: residential, commercial, hybrid)
  - Total price
  - Is active (BooleanField)
  - Image
- [ ] Create `BundleComponent` model for components in a bundle:
  - Bundle (ForeignKey to SystemBundle)
  - Product (ForeignKey to Product)
  - Quantity
  - Is required (BooleanField)
- [ ] Add compatibility rules (battery compatible with inverter, router with dish, etc.)
- [ ] Create REST API endpoints:
  - List active bundles: `GET /crm-api/products/system-bundles/`
  - Filter by installation type: `GET /crm-api/products/system-bundles/?installation_type=solar`
  - Get bundle details: `GET /crm-api/products/system-bundles/{id}/`
  - Validate bundle compatibility: `POST /crm-api/products/system-bundles/{id}/validate/`
- [ ] Create serializers with nested bundle components
- [ ] Write API tests

### Technical Notes
- Bundle should calculate total price from components if not manually set
- Add validation rules specific to installation type:
  - **Solar:** At least one inverter, battery, and solar panel required
  - **Starlink:** At least router and dish required
  - **Custom Furniture:** At least one furniture piece required
  - **Hybrid:** Combination of solar and starlink requirements
- Add method to check if all components are in stock

### Files to Create/Modify
- `whatsappcrm_backend/products_and_services/models.py` (add models)
- `whatsappcrm_backend/products_and_services/serializers.py`
- `whatsappcrm_backend/products_and_services/views.py`
- `whatsappcrm_backend/products_and_services/urls.py`
- `whatsappcrm_backend/products_and_services/tests.py`

---

## Issue 3: Automated ISR Creation on Installation Product Sale

**Priority:** CRITICAL  
**Estimated Time:** 3-4 days  
**Type:** Backend - Business Logic + Signals

### Description
Implement automatic Installation System Record creation when an installation bundle or product is sold. This applies to **all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI). This is the first step in automating the "Sale → ISR → Installation → Warranty" pipeline described in the PDF.

**IMPORTANT:** Hanna already has AI-powered email invoice processing (`email_integration` app) that auto-creates Orders and InstallationRequests from emailed invoices using Gemini AI. This issue should **extend that existing automation** to also create ISR for all installation types.

### Acceptance Criteria
- [ ] Create Django signal handler in `installation_systems` app
- [ ] When Order is created with stage='closed_won' and contains installation products:
  - Automatically create InstallationSystemRecord
  - Detect installation type from:
    - System bundles (installation_type field)
    - Product categories (solar, starlink, furniture)
    - Product keywords in descriptions
  - Link ISR to Order and CustomerProfile
  - Extract system size/capacity from bundle or calculate from components
  - Set appropriate capacity unit (kW for solar, Mbps for starlink, units for furniture)
  - Set status to 'pending'
  - Link to existing InstallationRequest (created by email processor or manual)
- [ ] **Extend email invoice processor** in `email_integration/tasks.py`:
  - Add ISR creation when processing installation invoices
  - Detect installation type from product descriptions or line items
  - Extract system capacity from product descriptions (e.g., "5kW solar", "100Mbps starlink")
  - Link ISR to auto-generated InstallationRequest
- [ ] Add `installation_system_record` field to InstallationRequest (ForeignKey, nullable)
- [ ] Create Celery task for ISR creation (async processing)
- [ ] Send notification to admin when ISR is created (specify installation type in notification)
- [ ] Create management command to backfill ISRs for existing installation orders
- [ ] Write integration tests for all installation types

### Technical Notes
- Use `post_save` signal on Order model for manual orders
- For email-processed orders, extend `_create_order_from_invoice_data()` in `email_integration/tasks.py`
- Detection keywords by type:
  - **Solar:** panel, inverter, battery, solar, photovoltaic, PV, kW
  - **Starlink:** starlink, satellite, router, dish, Mbps
  - **Custom Furniture:** furniture, table, chair, desk, cabinet, wardrobe
  - **Hybrid:** combination of solar + starlink keywords
- Handle edge cases (partial orders, returns, mixed-type orders)
- Log all ISR creation events with installation type
- Leverage existing Gemini AI extraction for system capacity detection

### Files to Create/Modify
- `whatsappcrm_backend/installation_systems/signals.py`
- `whatsappcrm_backend/installation_systems/apps.py` (connect signals)
- `whatsappcrm_backend/installation_systems/tasks.py`
- **`whatsappcrm_backend/email_integration/tasks.py`** (extend invoice processor)
- `whatsappcrm_backend/installation_systems/management/commands/backfill_isrs.py`
- `whatsappcrm_backend/customer_data/models.py` (add ISR foreign key)
- `whatsappcrm_backend/installation_systems/tests.py`

---

## Issue 4: Commissioning Checklist Model and API

**Priority:** HIGH  
**Estimated Time:** 3 days  
**Type:** Backend - Data Model + API

### Description
Create a digital commissioning checklist system for technicians to complete during installation. This enforces the "hard control" requirement from the PDF: installations cannot be marked complete without all checklist items. **Supports all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI).

### Acceptance Criteria
- [ ] Create `CommissioningChecklist` model in `installation_systems` app:
  - Linked to InstallationSystemRecord (OneToOne)
  - Overall status (choices: not_started, in_progress, completed)
  - Technician (ForeignKey)
  - Started at, completed at timestamps
- [ ] Create `ChecklistItem` model:
  - Checklist (ForeignKey)
  - Item name/description
  - Category (choices: pre_install, installation, testing, documentation)
  - Is required (BooleanField)
  - Is completed (BooleanField)
  - Completed by (ForeignKey to User)
  - Completed at (DateTimeField)
  - Notes (TextField, optional)
  - Photo evidence (ImageField, optional)
- [ ] Create predefined checklist templates in migration for each installation type
- [ ] Create REST API endpoints:
  - Get checklist for ISR: `GET /crm-api/installation-systems/{isr_id}/checklist/`
  - Update checklist item: `PATCH /crm-api/installation-systems/checklist-items/{id}/`
  - Mark item complete: `POST /crm-api/installation-systems/checklist-items/{id}/complete/`
- [ ] Add validation: ISR status cannot be set to 'commissioned' if checklist not 100% complete
- [ ] Write tests for all installation types

### Technical Notes
Predefined checklist items by installation type:

**Solar Installation (SSI):**
- Site assessment completed
- Panel mounting verified
- Electrical connections tested
- Inverter configured
- Battery tested
- System performance test passed
- Customer training completed
- Photos uploaded
- Serial numbers recorded

**Starlink Installation (SLI):**
- Site assessment completed
- Dish mounting verified
- Router installation completed
- Cable routing checked
- Network connectivity tested
- Speed test performed
- Customer training completed
- Photos uploaded
- Serial numbers recorded

**Custom Furniture Installation (CFI):**
- Site assessment completed
- Furniture assembly verified
- Placement confirmed with customer
- Hardware tightened
- Finish inspection
- Customer acceptance signed
- Photos uploaded
- Serial numbers recorded (if applicable)

**Hybrid Installation (SSI):**
- Combination of solar and starlink checklists

### Files to Create/Modify
- `whatsappcrm_backend/installation_systems/models.py`
- `whatsappcrm_backend/installation_systems/serializers.py`
- `whatsappcrm_backend/installation_systems/views.py`
- `whatsappcrm_backend/installation_systems/urls.py`
- `whatsappcrm_backend/installation_systems/migrations/0002_checklist_templates.py`
- `whatsappcrm_backend/installation_systems/tests.py`

---

## Issue 5: Admin Portal - Installation Systems Management Dashboard

**Priority:** HIGH  
**Estimated Time:** 3 days  
**Type:** Frontend - Next.js Management Portal

### Description
Create an admin dashboard page to view and manage all Installation System Records (ISR) with filtering, search, and status tracking capabilities. **Supports all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI).

### Acceptance Criteria
- [ ] Create new page: `/admin/(protected)/installation-systems/page.tsx`
- [ ] Display table of all ISRs with columns:
  - ISR ID
  - Customer name
  - **Installation type** (Solar/Starlink/Custom Furniture/Hybrid)
  - System size/capacity with unit (kW/Mbps/units)
  - Installation status
  - Installation date
  - Technician assigned
  - Action buttons (View, Edit)
- [ ] Implement filters:
  - **Installation type** (solar, starlink, custom_furniture, hybrid)
  - Status (pending, in_progress, commissioned, active)
  - System size range
  - Date range
  - Technician
- [ ] Search by ISR ID or customer name
- [ ] Pagination (30 items per page)
- [ ] Click row to view ISR detail page
- [ ] Add to navigation menu
- [ ] Responsive design (mobile-friendly)
- [ ] Loading states and error handling
- [ ] Color-coded installation type badges for easy identification

### Technical Notes
- Use shadcn/ui Table component
- Fetch data from: `GET /crm-api/installation-systems/installation-system-records/`
- Filter endpoint: `GET /crm-api/installation-systems/installation-system-records/?installation_type=solar`
- Use React Query for data fetching and caching
- Add Excel export button (optional, bonus)
- Use different colors for installation types (e.g., yellow for solar, blue for starlink, green for furniture)

### Files to Create/Modify
- `hanna-management-frontend/app/admin/(protected)/installation-systems/page.tsx`
- `hanna-management-frontend/app/admin/(protected)/installation-systems/[id]/page.tsx` (detail view)
- `hanna-management-frontend/app/admin/(protected)/layout.tsx` (add nav item)

---

## Issue 6: Technician Portal - Commissioning Checklist Mobile UI

**Priority:** HIGH  
**Estimated Time:** 3-4 days  
**Type:** Frontend - Next.js Management Portal

### Description
Create a mobile-friendly commissioning checklist interface for technicians to complete during field installations. This addresses the "Execution Layer" requirements from the PDF. **Supports all installation types** with type-specific checklists: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI).

### Acceptance Criteria
- [ ] Create new page: `/technician/(protected)/installations/page.tsx`
- [ ] List assigned installations with status and **installation type badge**
- [ ] Click installation to view checklist: `/technician/(protected)/installations/{isr_id}/checklist/page.tsx`
- [ ] Display installation type at top of page with appropriate icon
- [ ] Display checklist grouped by category (categories vary by installation type):
  - Pre-Install Checks
  - Installation Steps
  - Testing & Verification
  - Documentation
- [ ] Each checklist item shows:
  - Description
  - Required/Optional badge
  - Checkbox to mark complete
  - Text area for notes
  - Photo upload button
- [ ] Visual progress indicator (e.g., "12/20 items completed")
- [ ] Cannot mark installation as complete unless all required items checked
- [ ] Optimized for mobile (large touch targets, easy photo upload)
- [ ] Offline capability (bonus - save locally, sync when online)
- [ ] Success message when checklist completed
- [ ] Different checklist templates load based on installation type

### Technical Notes
- Use device camera API for photo capture
- Real-time sync with backend as items are checked
- Show confirmation dialog before marking installation complete
- Use optimistic UI updates for better UX
- Load appropriate checklist template based on ISR installation_type field
- Show installation type-specific icons (sun for solar, satellite for starlink, chair for furniture)

### Files to Create/Modify
- `hanna-management-frontend/app/technician/(protected)/installations/page.tsx`
- `hanna-management-frontend/app/technician/(protected)/installations/[ssrId]/checklist/page.tsx`
- `hanna-management-frontend/app/components/CommissioningChecklistItem.tsx`
- `hanna-management-frontend/app/technician/(protected)/layout.tsx` (add nav item)

---

## Issue 7: Client Portal - My Installation System Dashboard

**Priority:** MEDIUM  
**Estimated Time:** 3 days  
**Type:** Frontend - Next.js Management Portal

### Description
Enhance the client portal to show their complete installation system information linked to their ISR, addressing the "Customer Ownership & Self-Service" requirements from the PDF. **Supports all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI).

### Acceptance Criteria
- [ ] Create new page: `/client/(protected)/my-installation/page.tsx`
- [ ] Display installation system information with type-specific content:
  - **Installation type badge** (Solar/Starlink/Custom Furniture/Hybrid)
  - System capacity with appropriate unit (kW for solar, Mbps for starlink, units for furniture)
  - Installation date
  - System components (list of installed equipment with serial numbers)
  - Warranty status and expiry dates per component
  - Installation photos gallery
  - System diagram/schematic (if available for solar/starlink)
- [ ] **Type-specific features:**
  - **Solar:** Show monitoring link (if available), energy production stats
  - **Starlink:** Show network status, speed test link
  - **Custom Furniture:** Show assembly instructions, maintenance tips
  - **Hybrid:** Show both solar and starlink features
- [ ] Add "Download Installation Report" button (generates PDF)
- [ ] Add "Download Warranty Certificate" button
- [ ] Show commissioning checklist completion status
- [ ] Link to monitoring dashboard (for solar/starlink)
- [ ] Add "Report Issue" button → creates JobCard
- [ ] Display service history
- [ ] Responsive and visually appealing
- [ ] Use appropriate icons and colors for each installation type

### Technical Notes
- Fetch ISR data from: `GET /crm-api/installation-systems/my-installation/`
- Use shadcn/ui Card components
- Image gallery with lightbox
- PDF generation can use a simple backend endpoint or client-side library
- Conditional rendering based on installation_type field
- Use different layouts/sections for different installation types

### Files to Create/Modify
- `hanna-management-frontend/app/client/(protected)/my-installation/page.tsx`
- `hanna-management-frontend/app/client/(protected)/layout.tsx` (add nav item)
- `hanna-management-frontend/app/components/client/InstallationSystemCard.tsx`
- `hanna-management-frontend/app/components/client/InstallationPhotos.tsx`
- `hanna-management-frontend/app/components/client/SolarSystemDetails.tsx` (type-specific)
- `hanna-management-frontend/app/components/client/StarlinkSystemDetails.tsx` (type-specific)
- `hanna-management-frontend/app/components/client/FurnitureSystemDetails.tsx` (type-specific)

---

## Implementation Order

For maximum impact within the week:

### Days 1-2: Backend Foundation
- Issue 1: ISR Model (Critical) - Supports all installation types
- Issue 2: System Bundles (can be parallel) - Supports all installation types

### Days 3-4: Automation & Business Logic
- Issue 3: Automated ISR Creation - Handles solar, starlink, furniture, hybrid
- Issue 4: Commissioning Checklist - Type-specific templates

### Days 5-7: Frontend Portals
- Issue 5: Admin ISR Dashboard - View all installation types
- Issue 6: Technician Checklist UI - Type-specific checklists
- Issue 7: Client Installation System View - Type-specific displays

---

## Dependencies

- Issue 3 depends on Issue 1 (ISR model must exist)
- Issue 4 depends on Issue 1 (Checklist links to ISR)
- Issue 5 depends on Issue 1 (Admin views ISRs)
- Issue 6 depends on Issue 4 (Technician completes checklist)
- Issue 7 depends on Issue 1 (Client views their ISR)

---

## Testing Strategy

Each issue should include:
1. Unit tests for models and business logic
2. API integration tests
3. Manual testing in dev environment
4. Documentation updates

---

## Success Metrics

After completing these 7 issues:
- ✅ ISR (Installation System Record) concept introduced and operational for **all installation types**
- ✅ Installation sales (Solar, Starlink, Custom Furniture, Hybrid) automatically create installation records
- ✅ Technicians can digitally commission installations with **type-specific checklists**
- ✅ Admins can track all installation systems across all types
- ✅ Clients can view their installation system details with type-specific information
- ✅ Foundation laid for remote monitoring integration (solar/starlink) (Issue 8, Week 2)
- ✅ Unified installation lifecycle management across all business lines (SSI, SLI, CFI)

---

## Next Week (Week 2) Preview

Based on Week 1 completion:
- Remote monitoring integration framework (solar and starlink)
- Automated warranty activation on commissioning (all types)
- Retailer sales portal for bundles (all types)
- Automated fault ticket creation
- Enhanced analytics and reporting by installation type
- Type-specific service workflows

