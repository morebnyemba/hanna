# Implementable Issues - Week 1 Sprint
## Hanna Solar Lifecycle Operating System - Phase 1

Based on the comprehensive gap analysis, here are **7 focused issues** that can be completed within one week and begin transforming Hanna into a Solar Lifecycle Operating System.

---

## Issue 1: Create Solar System Record (SSR) Model Foundation

**Priority:** CRITICAL  
**Estimated Time:** 3-4 days  
**Type:** Backend - Data Model

### Description
Create the foundational `SolarSystemRecord` model that will serve as the master object for tracking every solar installation throughout its lifecycle. This is the core concept from the PDF that's currently missing.

### Acceptance Criteria
- [ ] Create `SolarSystemRecord` model in a new Django app called `solar_installations`
- [ ] Include fields:
  - System identifier (auto-generated unique ID)
  - Linked customer profile (ForeignKey to CustomerProfile)
  - Linked order (ForeignKey to Order)
  - System size/capacity in kW (DecimalField)
  - System type (choices: residential, commercial, hybrid)
  - Installation date (DateField)
  - Installation status (choices: pending, in_progress, commissioned, active, decommissioned)
  - Commissioning date (DateField, nullable)
  - Remote monitoring ID (CharField, nullable)
  - GPS coordinates (latitude, longitude)
  - Installation address
  - Assigned technician(s) (ManyToMany to Technician)
- [ ] Create relationship: `installed_components` ManyToMany to SerializedItem
- [ ] Add timestamps (created_at, updated_at)
- [ ] Create database migrations
- [ ] Add Django admin interface for SSR
- [ ] Write model tests

### Technical Notes
- Place in new app: `whatsappcrm_backend/solar_installations/`
- Use UUID for primary key
- Add `__str__` method returning: "SSR-{id} - {customer_name} - {system_size}kW"
- Create reverse relationships from Order, CustomerProfile

### Files to Create/Modify
- `whatsappcrm_backend/solar_installations/models.py`
- `whatsappcrm_backend/solar_installations/admin.py`
- `whatsappcrm_backend/solar_installations/tests.py`
- `whatsappcrm_backend/whatsappcrm_backend/settings.py` (add app)

---

## Issue 2: Add System Bundles / Solar Packages Model

**Priority:** HIGH  
**Estimated Time:** 2-3 days  
**Type:** Backend - Data Model + API

### Description
Create a `SystemBundle` model to represent pre-configured solar packages (e.g., "3kW Residential Solar Kit", "5kW Commercial Solar System") as required by the PDF. This enables controlled offerings where retailers can only sell approved bundles.

### Acceptance Criteria
- [ ] Create `SystemBundle` model in `products_and_services` app
- [ ] Include fields:
  - Name (e.g., "3kW Residential Solar Kit")
  - SKU/code
  - Description
  - System capacity (DecimalField in kW)
  - Bundle type (choices: residential, commercial, hybrid)
  - Total price
  - Is active (BooleanField)
  - Image
- [ ] Create `BundleComponent` model for components in a bundle:
  - Bundle (ForeignKey to SystemBundle)
  - Product (ForeignKey to Product)
  - Quantity
  - Is required (BooleanField)
- [ ] Add compatibility rules (battery compatible with inverter, etc.)
- [ ] Create REST API endpoints:
  - List active bundles: `GET /crm-api/products/system-bundles/`
  - Get bundle details: `GET /crm-api/products/system-bundles/{id}/`
  - Validate bundle compatibility: `POST /crm-api/products/system-bundles/{id}/validate/`
- [ ] Create serializers with nested bundle components
- [ ] Write API tests

### Technical Notes
- Bundle should calculate total price from components if not manually set
- Add validation to ensure bundle has at least one inverter, battery, and solar panel
- Add method to check if all components are in stock

### Files to Create/Modify
- `whatsappcrm_backend/products_and_services/models.py` (add models)
- `whatsappcrm_backend/products_and_services/serializers.py`
- `whatsappcrm_backend/products_and_services/views.py`
- `whatsappcrm_backend/products_and_services/urls.py`
- `whatsappcrm_backend/products_and_services/tests.py`

---

## Issue 3: Automated SSR Creation on Solar Product Sale

**Priority:** CRITICAL  
**Estimated Time:** 3-4 days  
**Type:** Backend - Business Logic + Signals

### Description
Implement automatic Solar System Record creation when a solar bundle or solar installation is sold. This is the first step in automating the "Sale → SSR → Installation → Warranty" pipeline described in the PDF.

**IMPORTANT:** Hanna already has AI-powered email invoice processing (`email_integration` app) that auto-creates Orders and InstallationRequests from emailed invoices using Gemini AI. This issue should **extend that existing automation** to also create SSR when the invoice contains solar products.

### Acceptance Criteria
- [ ] Create Django signal handler in `solar_installations` app
- [ ] When Order is created with stage='closed_won' and contains solar products:
  - Automatically create SolarSystemRecord
  - Link SSR to Order and CustomerProfile
  - Extract system size from bundle or calculate from components
  - Set status to 'pending'
  - Link to existing InstallationRequest (created by email processor or manual)
- [ ] **Extend email invoice processor** in `email_integration/tasks.py`:
  - Add SSR creation when processing solar invoices
  - Extract system capacity from product descriptions or line items
  - Link SSR to auto-generated InstallationRequest
- [ ] Add `solar_system_record` field to InstallationRequest (ForeignKey, nullable)
- [ ] Create Celery task for SSR creation (async processing)
- [ ] Send notification to admin when SSR is created
- [ ] Create management command to backfill SSRs for existing solar orders
- [ ] Write integration tests

### Technical Notes
- Use `post_save` signal on Order model for manual orders
- For email-processed orders, extend `_create_order_from_invoice_data()` in `email_integration/tasks.py`
- Check if order contains products in solar categories or system bundles
- Detect solar keywords in product descriptions (panel, inverter, battery, solar kit)
- Handle edge cases (partial orders, returns)
- Log all SSR creation events
- Leverage existing Gemini AI extraction for system capacity detection

### Files to Create/Modify
- `whatsappcrm_backend/solar_installations/signals.py`
- `whatsappcrm_backend/solar_installations/apps.py` (connect signals)
- `whatsappcrm_backend/solar_installations/tasks.py`
- **`whatsappcrm_backend/email_integration/tasks.py`** (extend invoice processor)
- `whatsappcrm_backend/solar_installations/management/commands/backfill_ssrs.py`
- `whatsappcrm_backend/customer_data/models.py` (add SSR foreign key)
- `whatsappcrm_backend/solar_installations/tests.py`

---

## Issue 4: Commissioning Checklist Model and API

**Priority:** HIGH  
**Estimated Time:** 3 days  
**Type:** Backend - Data Model + API

### Description
Create a digital commissioning checklist system for technicians to complete during installation. This enforces the "hard control" requirement from the PDF: installations cannot be marked complete without all checklist items.

### Acceptance Criteria
- [ ] Create `CommissioningChecklist` model in `solar_installations` app:
  - Linked to SolarSystemRecord (OneToOne)
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
- [ ] Create predefined checklist templates in migration
- [ ] Create REST API endpoints:
  - Get checklist for SSR: `GET /crm-api/solar-installations/{ssr_id}/checklist/`
  - Update checklist item: `PATCH /crm-api/solar-installations/checklist-items/{id}/`
  - Mark item complete: `POST /crm-api/solar-installations/checklist-items/{id}/complete/`
- [ ] Add validation: SSR status cannot be set to 'commissioned' if checklist not 100% complete
- [ ] Write tests

### Technical Notes
- Predefined checklist items include:
  - Site assessment completed
  - Panel mounting verified
  - Electrical connections tested
  - Inverter configured
  - Battery tested
  - System performance test passed
  - Customer training completed
  - Photos uploaded
  - Serial numbers recorded

### Files to Create/Modify
- `whatsappcrm_backend/solar_installations/models.py`
- `whatsappcrm_backend/solar_installations/serializers.py`
- `whatsappcrm_backend/solar_installations/views.py`
- `whatsappcrm_backend/solar_installations/urls.py`
- `whatsappcrm_backend/solar_installations/migrations/0002_checklist_templates.py`
- `whatsappcrm_backend/solar_installations/tests.py`

---

## Issue 5: Admin Portal - SSR Management Dashboard

**Priority:** HIGH  
**Estimated Time:** 3 days  
**Type:** Frontend - Next.js Management Portal

### Description
Create an admin dashboard page to view and manage all Solar System Records with filtering, search, and status tracking capabilities.

### Acceptance Criteria
- [ ] Create new page: `/admin/(protected)/solar-systems/page.tsx`
- [ ] Display table of all SSRs with columns:
  - SSR ID
  - Customer name
  - System size (kW)
  - Installation status
  - Installation date
  - Technician assigned
  - Action buttons (View, Edit)
- [ ] Implement filters:
  - Status (pending, in_progress, commissioned, active)
  - System size range
  - Date range
  - Technician
- [ ] Search by SSR ID or customer name
- [ ] Pagination (30 items per page)
- [ ] Click row to view SSR detail page
- [ ] Add to navigation menu
- [ ] Responsive design (mobile-friendly)
- [ ] Loading states and error handling

### Technical Notes
- Use shadcn/ui Table component
- Fetch data from: `GET /crm-api/solar-installations/solar-system-records/`
- Use React Query for data fetching and caching
- Add Excel export button (optional, bonus)

### Files to Create/Modify
- `hanna-management-frontend/app/admin/(protected)/solar-systems/page.tsx`
- `hanna-management-frontend/app/admin/(protected)/solar-systems/[id]/page.tsx` (detail view)
- `hanna-management-frontend/app/admin/(protected)/layout.tsx` (add nav item)

---

## Issue 6: Technician Portal - Commissioning Checklist Mobile UI

**Priority:** HIGH  
**Estimated Time:** 3-4 days  
**Type:** Frontend - Next.js Management Portal

### Description
Create a mobile-friendly commissioning checklist interface for technicians to complete during field installations. This addresses the "Execution Layer" requirements from the PDF.

### Acceptance Criteria
- [ ] Create new page: `/technician/(protected)/installations/page.tsx`
- [ ] List assigned installations with status
- [ ] Click installation to view checklist: `/technician/(protected)/installations/{ssr_id}/checklist/page.tsx`
- [ ] Display checklist grouped by category:
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

### Technical Notes
- Use device camera API for photo capture
- Real-time sync with backend as items are checked
- Show confirmation dialog before marking installation complete
- Use optimistic UI updates for better UX

### Files to Create/Modify
- `hanna-management-frontend/app/technician/(protected)/installations/page.tsx`
- `hanna-management-frontend/app/technician/(protected)/installations/[ssrId]/checklist/page.tsx`
- `hanna-management-frontend/app/components/CommissioningChecklistItem.tsx`
- `hanna-management-frontend/app/technician/(protected)/layout.tsx` (add nav item)

---

## Issue 7: Client Portal - My Solar System Dashboard

**Priority:** MEDIUM  
**Estimated Time:** 3 days  
**Type:** Frontend - Next.js Management Portal

### Description
Enhance the client portal to show their complete solar system information linked to their SSR, addressing the "Customer Ownership & Self-Service" requirements from the PDF.

### Acceptance Criteria
- [ ] Create new page: `/client/(protected)/my-system/page.tsx`
- [ ] Display solar system information:
  - System capacity (kW)
  - Installation date
  - System components (list of installed equipment with serial numbers)
  - Warranty status and expiry dates per component
  - Installation photos gallery
  - System diagram/schematic (if available)
- [ ] Add "Download Installation Report" button (generates PDF)
- [ ] Add "Download Warranty Certificate" button
- [ ] Show commissioning checklist completion status
- [ ] Link to monitoring dashboard
- [ ] Add "Report Issue" button → creates JobCard
- [ ] Display service history
- [ ] Responsive and visually appealing

### Technical Notes
- Fetch SSR data from: `GET /crm-api/solar-installations/my-solar-system/`
- Use shadcn/ui Card components
- Image gallery with lightbox
- PDF generation can use a simple backend endpoint or client-side library

### Files to Create/Modify
- `hanna-management-frontend/app/client/(protected)/my-system/page.tsx`
- `hanna-management-frontend/app/client/(protected)/layout.tsx` (add nav item)
- `hanna-management-frontend/app/components/client/SolarSystemCard.tsx`
- `hanna-management-frontend/app/components/client/InstallationPhotos.tsx`

---

## Implementation Order

For maximum impact within the week:

### Days 1-2: Backend Foundation
- Issue 1: SSR Model (Critical)
- Issue 2: System Bundles (can be parallel)

### Days 3-4: Automation & Business Logic
- Issue 3: Automated SSR Creation
- Issue 4: Commissioning Checklist

### Days 5-7: Frontend Portals
- Issue 5: Admin SSR Dashboard
- Issue 6: Technician Checklist UI
- Issue 7: Client Solar System View

---

## Dependencies

- Issue 3 depends on Issue 1 (SSR model must exist)
- Issue 4 depends on Issue 1 (Checklist links to SSR)
- Issue 5 depends on Issue 1 (Admin views SSRs)
- Issue 6 depends on Issue 4 (Technician completes checklist)
- Issue 7 depends on Issue 1 (Client views their SSR)

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
- ✅ SSR concept introduced and operational
- ✅ Solar sales automatically create installation records
- ✅ Technicians can digitally commission installations
- ✅ Admins can track all solar systems
- ✅ Clients can view their system details
- ✅ Foundation laid for remote monitoring integration (Issue 8, Week 2)

---

## Next Week (Week 2) Preview

Based on Week 1 completion:
- Remote monitoring integration framework
- Automated warranty activation on commissioning
- Retailer sales portal for bundles
- Automated fault ticket creation
- Enhanced analytics and reporting

