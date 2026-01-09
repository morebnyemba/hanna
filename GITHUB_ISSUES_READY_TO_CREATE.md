# Quick Reference: 12 GitHub Issues to Create

Copy and paste each issue below directly into GitHub's issue creation form.

---

## Issue 1: Create Solar System Record (SSR) Model & Core Integration

**Labels:** `enhancement`, `backend`, `priority: critical`, `effort: 7 days`

**Description:**

The PDF emphasizes that all portals should orbit a single master object: the **Solar System Record (SSR)**. This is currently missing. Create a unified `SolarSystemInstallation` model that serves as the digital file per installation, linking customer, equipment, installation, warranty, monitoring, and service data.

**Acceptance Criteria:**
- [ ] Create `SolarSystemInstallation` model with fields: Installation ID, Customer, System size, System type, Associated order, Lifecycle status
- [ ] Create relationships to: InstallationRequest, SerializedItem, Warranty, JobCard, Technician
- [ ] Create migrations and migrate existing data
- [ ] Add Django admin interface for SSR management
- [ ] Create REST API endpoints (CRUD operations)
- [ ] Add role-based permissions (admin: full, client: read-only own, technician: update)
- [ ] Update existing InstallationRequest creation to also create SSR
- [ ] Write unit tests for SSR model and API

**Technical Notes:**
This is the anchor for the "Solar Lifecycle Operating System". All future features will reference this model.

**Dependencies:** None (foundation issue)

**Effort:** 7 days

---

## Issue 2: Implement Digital Commissioning Checklist System

**Labels:** `enhancement`, `backend`, `frontend`, `technician-portal`, `priority: high`, `effort: 7 days`

**Description:**

Per the PDF: "Step-by-step digital checklists: Pre-install, Installation, Commissioning" with hard control that "a job cannot be marked 'Complete' unless all required fields are submitted."

**Acceptance Criteria:**
- [ ] Create `CommissioningChecklistTemplate` model (name, type, items, required photos, system type)
- [ ] Create `InstallationChecklistEntry` model (link to SSR, template, completed items, status, technician, timestamp)
- [ ] Admin interface to create/edit checklist templates
- [ ] Create default templates: Pre-installation, Installation, Commissioning
- [ ] Technician portal UI: Display checklist, check off items, add notes, upload photos
- [ ] Implement validation: Cannot mark "Complete" without 100% checklist completion
- [ ] Add API endpoints for checklist operations
- [ ] Write tests for validation logic

**Technical Notes:**
Store checklist items as JSON for flexibility. Consider mobile-friendly UI.

**Dependencies:** Issue #1 (SSR Model)

**Effort:** 7 days

---

## Issue 3: Add Photo Upload & Gallery to Installation Process

**Labels:** `enhancement`, `frontend`, `technician-portal`, `client-portal`, `priority: high`, `effort: 5 days`

**Description:**

Technicians must upload installation photos (equipment, site, serial numbers, test results) as part of the commissioning process. These photos become part of the SSR and installation reports.

**Acceptance Criteria:**
- [ ] Create `InstallationPhoto` model or relationship (link to SSR, type, caption, uploaded by, required flag)
- [ ] Technician portal UI: Photo upload (drag-drop/camera), organize by type, link to checklist, preview
- [ ] Photo gallery view: Technician (upload/view), Client (view), Admin (view all)
- [ ] Validation: Mark certain photos as required
- [ ] Add to SSR API response
- [ ] Mobile-responsive upload interface
- [ ] Write tests for upload and validation

**Technical Notes:**
Use existing MediaAsset infrastructure. Consider image compression.

**Dependencies:** Issue #1 (SSR Model), Issue #2 (Checklists - for linking)

**Effort:** 5 days

---

## Issue 4: Serial Number Capture & Validation in Technician Portal

**Labels:** `enhancement`, `frontend`, `technician-portal`, `priority: high`, `effort: 5 days`

**Description:**

Technicians must capture equipment serial numbers during installation via barcode scanning or manual entry. Serial numbers must be validated against the product database and linked to the SSR.

**Acceptance Criteria:**
- [ ] Technician portal serial number entry UI: Barcode scanner, manual entry, product type selection
- [ ] Link serial numbers to SerializedItem and SSR
- [ ] Validation: Check existence, verify not already assigned, validate format
- [ ] Display captured serial numbers in SSR view
- [ ] Add to installation checklist (required items)
- [ ] Integrate barcode scanning library (QuaggaJS/ZXing)
- [ ] Mobile-friendly interface
- [ ] API endpoints for serial number operations
- [ ] Write tests for validation logic

**Technical Notes:**
Use HTML5 camera API for barcode scanning with manual entry fallback.

**Dependencies:** Issue #1 (SSR Model)

**Effort:** 5 days

---

## Issue 5: Generate Downloadable Warranty Certificates & Installation Reports

**Labels:** `enhancement`, `backend`, `frontend`, `client-portal`, `admin-portal`, `priority: high`, `effort: 7 days`

**Description:**

Per PDF: Clients should be able to download warranty certificates and installation reports. Reports should include installation photos and commissioning data.

**Acceptance Criteria:**
- [ ] Install PDF generation library (WeasyPrint or ReportLab)
- [ ] Create warranty certificate template (customer, system, serial numbers, dates, T&C, branding)
- [ ] Create installation report template (customer, date, technicians, specs, checklist, photos, test results)
- [ ] Backend API endpoints: `/api/warranty/{id}/certificate/`, `/api/installation/{id}/report/`
- [ ] Client portal UI: "Download Warranty Certificate" and "Download Installation Report" buttons
- [ ] Admin portal: Can generate certificates for any customer
- [ ] Cache generated PDFs for performance
- [ ] Write tests for PDF generation

**Technical Notes:**
Include QR code linking to digital record. Ensure Pfungwa branding.

**Dependencies:** Issue #1 (SSR Model), Issue #2 (Checklists for report data), Issue #3 (Photos for report)

**Effort:** 7 days

---

## Issue 6: Build Retailer Solar Package Sales Interface

**Labels:** `enhancement`, `backend`, `frontend`, `retailer-portal`, `admin-portal`, `priority: high`, `effort: 7 days`

**Description:**

Per PDF: "Retailers sell standardized solar packages" and "submit customer orders." Build a complete sales interface for retailers to sell pre-configured solar system bundles.

**Acceptance Criteria:**
- [ ] Create `SolarPackage` model: name, system size, included products, price, compatibility rules, active status
- [ ] Admin interface to configure solar packages
- [ ] Retailer portal "Solar Packages" page: Display packages, details, "Create Order" button
- [ ] Customer order submission form: customer details, package, payment method, loan approval
- [ ] Order submission workflow: Create CustomerProfile, Order, InstallationRequest, SSR, send confirmation
- [ ] Order history page: List orders, filter, view details
- [ ] API endpoints for package listing and order creation
- [ ] Write tests for order flow

**Technical Notes:**
Link to payment integration (Paynow). Consider compatibility validation engine.

**Dependencies:** Issue #1 (SSR Model)

**Effort:** 7 days

---

## Issue 7: Add Installation & Warranty Tracking to Retailer Portal

**Labels:** `enhancement`, `frontend`, `retailer-portal`, `priority: medium`, `effort: 5 days`

**Description:**

Per PDF: Retailers should track installation status, warranty activation, and view warranty records. This provides transparency and reduces support requests.

**Acceptance Criteria:**
- [ ] "Installation Tracking" page: List orders with status, technician, date, link to details
- [ ] Installation detail view (read-only): Customer, system, progress, photos
- [ ] "Warranty Management" page: List warranties, status, expiration, claims
- [ ] Product tracking during warranty: View scanned products in/out
- [ ] Filter and search functionality
- [ ] API endpoints for tracking data
- [ ] Write tests for access control (retailer sees only their orders)

**Technical Notes:**
Ensure proper permission checks. Link to manufacturer job cards if available.

**Dependencies:** Issue #1 (SSR Model), Issue #6 (Retailer Sales)

**Effort:** 5 days

---

## Issue 8: Implement Installer Payout Approval System

**Labels:** `enhancement`, `backend`, `frontend`, `admin-portal`, `priority: medium`, `effort: 7 days`

**Description:**

Per PDF: Admins should approve "installer payouts." Create a financial workflow for calculating and approving technician payments based on completed installations.

**Acceptance Criteria:**
- [ ] Create `InstallerPayout` model: technician, installations, amount, status, method, notes, dates
- [ ] Automatic payout calculation on installation completion
- [ ] Admin "Installer Payouts" page: List pending, filter, view details, approve/reject, add notes
- [ ] Payout detail view: technician, installations list, amount breakdown, approval workflow
- [ ] Zoho integration: Create bill/expense when approved, sync payment status
- [ ] Email notification to technician on approval
- [ ] Payout history view
- [ ] API endpoints for payout operations
- [ ] Write tests for calculation logic

**Technical Notes:**
Define payout rates in configuration. Consider multi-tier rates. Ensure audit trail.

**Dependencies:** Issue #1 (SSR Model)

**Effort:** 7 days

---

## Issue 9: Add Warranty Rules & SLA Configuration to Admin Portal

**Labels:** `enhancement`, `backend`, `frontend`, `admin-portal`, `priority: medium`, `effort: 5 days`

**Description:**

Per PDF: Admins should configure warranty rules and SLA thresholds. This enables automatic warranty duration assignment and SLA violation tracking.

**Acceptance Criteria:**
- [ ] Create `WarrantyRule` model: product/category, duration, T&C, active status
- [ ] Create `SLAThreshold` model: request type, response time, resolution time, escalation rules
- [ ] Admin "Warranty Rules" page: List, add/edit/delete, set duration by product
- [ ] Admin "SLA Configuration" page: List thresholds, edit times, configure escalation
- [ ] Apply warranty rules automatically: Use rule to set end date on warranty creation
- [ ] SLA tracking: Calculate status, flag violations, send alerts near deadline
- [ ] Dashboard widget showing SLA compliance
- [ ] API endpoints for configuration
- [ ] Write tests for automatic rule application

**Technical Notes:**
Consider background task for SLA monitoring. Add to admin dashboard.

**Dependencies:** None (configuration feature)

**Effort:** 5 days

---

## Issue 10: Integrate Remote Monitoring Platform (Phase 1: Victron VRM)

**Labels:** `enhancement`, `backend`, `integration`, `client-portal`, `priority: medium`, `effort: 7 days`

**Description:**

Per PDF: "Integrate with inverter and battery monitoring platforms to enable automated fault detection." Start with Victron VRM.

**Acceptance Criteria:**
- [ ] Research Victron VRM API documentation
- [ ] Create `MonitoringPlatformConfig` model: platform name, credentials, active
- [ ] Create `MonitoringDevice` model: SSR link, platform, device ID, installation ID, last sync
- [ ] Create `MonitoringAlert` model: device, type, severity, message, timestamp, status, ticket link
- [ ] Implement Victron VRM integration: Auth, fetch data, poll alerts, webhook receiver
- [ ] Automated fault ticket creation: Create JobCard, notify customer, assign technician
- [ ] Add monitoring ID field to SSR
- [ ] Client portal monitoring dashboard: Status, KPIs, alert history
- [ ] Admin view of all monitoring devices
- [ ] API endpoints for monitoring data
- [ ] Write tests for alert processing

**Technical Notes:**
Use Celery for periodic polling. Design for multi-platform support.

**Dependencies:** Issue #1 (SSR Model)

**Effort:** 7 days

---

## Issue 11: Branch Installer Allocation & Performance Metrics

**Labels:** `enhancement`, `frontend`, `retailer-branch-portal`, `priority: low`, `effort: 7 days`

**Description:**

Per PDF: Branch portal needs "installer allocation" and "regional performance metrics." Enhance with job assignment and analytics.

**Acceptance Criteria:**
- [ ] "Assign Installer" interface: View pending installs, list installers, assign, set date
- [ ] Installer availability calendar: View schedules, assigned jobs, identify conflicts
- [ ] Performance metrics dashboard: Completion rate, avg time, customer satisfaction, revenue
- [ ] KPI cards: Installs this month, pending, completed, complaints
- [ ] Date range filters for metrics
- [ ] Export reports (CSV/PDF)
- [ ] API endpoints for metrics
- [ ] Write tests for metric calculations

**Technical Notes:**
Leverage existing analytics. Consider caching. Add period comparison.

**Dependencies:** Issue #1 (SSR Model)

**Effort:** 7 days

---

## Issue 12: Automatic SSR Creation on Solar Package Purchase

**Labels:** `enhancement`, `backend`, `automation`, `priority: medium`, `effort: 5 days`

**Description:**

Per PDF: "Every sale = an SSR is created instantly." Implement post-order automation to create SSR and related records when a solar package is purchased.

**Acceptance Criteria:**
- [ ] Create post-order signal handler
- [ ] When solar package ordered: Create SSR, InstallationRequest, Warranties, grant portal access, send confirmation, notify admin/branch
- [ ] Implement compatibility validation: Battery ↔ inverter, system size matches components
- [ ] Create `CompatibilityRule` model: Product A, Compatible with B, rule type
- [ ] Admin interface for compatibility rules
- [ ] Validation during package configuration
- [ ] Order confirmation includes SSR ID
- [ ] API endpoint to check compatibility
- [ ] Write tests for automation flow

**Technical Notes:**
Use Django signals. Ensure idempotency. Handle partial orders. Log actions.

**Dependencies:** Issue #1 (SSR Model), Issue #6 (Solar Packages)

**Effort:** 5 days

---

## Implementation Order

1. **Week 1-2:** Issue #1 (SSR - Foundation)
2. **Week 3-5:** Issues #2, #3, #4 (Technician Portal) - Can parallelize
3. **Week 6:** Issue #5 (Certificates)
4. **Week 7-8:** Issues #6, #7 (Retailer Portal)
5. **Week 9-10:** Issues #8, #9 (Admin)
6. **Week 11-12:** Issues #10, #12 (Monitoring & Automation)
7. **Week 13:** Issue #11 (Branch Metrics)

**Total: ~74 days sequential, or 7-10 weeks with parallel development**

---

## Labels to Create in GitHub

- `priority: critical`
- `priority: high`
- `priority: medium`
- `priority: low`
- `effort: 5 days`
- `effort: 7 days`
- `admin-portal`
- `client-portal`
- `technician-portal`
- `retailer-portal`
- `retailer-branch-portal`
- `manufacturer-portal`
- `backend`
- `frontend`
- `integration`
- `automation`
