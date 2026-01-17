# Implementable GitHub Issues for HANNA (Week-Sized Tasks)

**Based on:** Hanna Core Scope and Functionality PDF  
**Analysis Date:** January 9, 2026  
**All issues are scoped to be completable within one week**

---

## Issue 1: Create Solar System Record (SSR) Model & Core Integration

**Priority:** Critical (Foundation for all other work)  
**Estimated Effort:** 7 days  
**Portals Affected:** All (backend foundation)

### Description
The PDF emphasizes that all portals should orbit a single master object: the **Solar System Record (SSR)**. This is currently missing. Create a unified `SolarSystemInstallation` model that serves as the digital file per installation, linking customer, equipment, installation, warranty, monitoring, and service data.

### Acceptance Criteria
- [ ] Create `SolarSystemInstallation` model with fields:
  - Installation ID (unique identifier)
  - Customer profile link
  - System size (3kW, 5kW, 6kW, 8kW, etc.)
  - System type (grid-tied, off-grid, hybrid)
  - Associated order
  - Lifecycle status
- [ ] Create relationships to existing models:
  - InstallationRequest (OneToOne)
  - SerializedItem (ManyToMany for panels, inverter, batteries)
  - Warranty (ManyToMany)
  - JobCard (ManyToMany for service history)
  - Technician (ManyToMany for assignments)
- [ ] Create migrations and migrate existing data
- [ ] Add Django admin interface for SSR management
- [ ] Create REST API endpoints (CRUD operations)
- [ ] Add role-based permissions (admin: full, client: read-only own, technician: update)
- [ ] Update existing InstallationRequest creation to also create SSR
- [ ] Write unit tests for SSR model and API

### Technical Notes
- This is the anchor for the "Solar Lifecycle Operating System"
- All future features will reference this model
- Ensure proper indexing for performance

---

## Issue 2: Implement Digital Commissioning Checklist System

**Priority:** High (Critical for technician workflow)  
**Estimated Effort:** 7 days  
**Portals Affected:** Technician, Admin

### Description
Per the PDF: "Step-by-step digital checklists: Pre-install, Installation, Commissioning" with hard control that "a job cannot be marked 'Complete' unless all required fields are submitted."

### Acceptance Criteria
- [ ] Create `CommissioningChecklistTemplate` model
  - Template name
  - Checklist type (pre-install, installation, commissioning)
  - Items list (JSON structure)
  - Required photos per item
  - Associated system type/product
- [ ] Create `InstallationChecklistEntry` model
  - Link to SSR
  - Link to template
  - Completed items (JSON with timestamps)
  - Completion status
  - Technician who completed
  - Completion timestamp
- [ ] Admin interface to create/edit checklist templates
- [ ] Create default templates:
  - Pre-installation checklist
  - Installation checklist
  - Commissioning checklist
- [ ] Technician portal UI:
  - Display checklist for assigned installation
  - Check off items as completed
  - Add notes per item
  - Upload required photos
- [ ] Implement validation: Cannot mark installation "Complete" without 100% checklist completion
- [ ] Add API endpoints for checklist operations
- [ ] Write tests for validation logic

### Technical Notes
- Store checklist items as JSON for flexibility
- Consider mobile-friendly UI for field technicians
- Ensure offline capability if possible (future enhancement)

---

## Issue 3: Add Photo Upload & Gallery to Installation Process

**Priority:** High (Required for commissioning evidence)  
**Estimated Effort:** 5 days  
**Portals Affected:** Technician, Client, Admin

### Description
Technicians must upload installation photos (equipment, site, serial numbers, test results) as part of the commissioning process. These photos become part of the SSR and installation reports.

### Acceptance Criteria
- [ ] Enhance MediaAsset model if needed for installation context
- [ ] Create `InstallationPhoto` model or relationship
  - Link to SSR
  - Photo type (before, during, after, serial_number, test_result, site)
  - Caption/description
  - Uploaded by (technician)
  - Required flag
- [ ] Technician portal UI:
  - Photo upload interface (drag-drop or camera)
  - Organize by photo type
  - Link photos to checklist items
  - Show upload progress
  - Preview uploaded photos
- [ ] Photo gallery view:
  - Technician: can upload and view
  - Client: can view installation photos (read-only)
  - Admin: can view all photos
- [ ] Validation: Mark certain photos as required (e.g., serial numbers)
- [ ] Add to SSR API response
- [ ] Mobile-responsive upload interface
- [ ] Write tests for upload and validation

### Technical Notes
- Use existing MediaAsset infrastructure
- Consider image compression/optimization
- Ensure secure storage and access control

---

## Issue 4: Serial Number Capture & Validation in Technician Portal

**Priority:** High (Equipment tracking requirement)  
**Estimated Effort:** 5 days  
**Portals Affected:** Technician, Admin

### Description
Technicians must capture equipment serial numbers during installation via barcode scanning or manual entry. Serial numbers must be validated against the product database and linked to the SSR.

### Acceptance Criteria
- [ ] Enhance technician portal with serial number entry UI:
  - Barcode scanner interface (camera-based)
  - Manual entry fallback
  - Product type selection (panel, inverter, battery, charge controller, etc.)
- [ ] Link serial numbers to SerializedItem model
- [ ] Link SerializedItem to SSR
- [ ] Validation:
  - Check if serial number exists in database
  - Verify not already assigned to another installation
  - Validate format if applicable
- [ ] Display captured serial numbers in SSR view
- [ ] Add to installation checklist (required items)
- [ ] Create barcode scanning library integration (e.g., QuaggaJS, ZXing)
- [ ] Mobile-friendly interface
- [ ] API endpoints for serial number operations
- [ ] Write tests for validation logic

### Technical Notes
- Use HTML5 camera API for barcode scanning
- Fallback to manual entry if camera unavailable
- Consider offline capability for remote sites

---

## Issue 5: Generate Downloadable Warranty Certificates & Installation Reports

**Priority:** High (Client transparency requirement)  
**Estimated Effort:** 7 days  
**Portals Affected:** Client, Admin

### Description
Per PDF: Clients should be able to download warranty certificates and installation reports. Reports should include installation photos and commissioning data.

### Acceptance Criteria
- [ ] Install PDF generation library (WeasyPrint or ReportLab)
- [ ] Create warranty certificate template:
  - Customer details
  - System specifications
  - Equipment serial numbers
  - Warranty start/end dates
  - Terms and conditions
  - Company branding
- [ ] Create installation report template:
  - Customer details
  - Installation date and technicians
  - System specifications
  - Commissioning checklist (completed items)
  - Installation photos
  - Test results
  - Sign-off section
- [ ] Backend API endpoints:
  - `/api/warranty/{id}/certificate/` - Generate warranty certificate PDF
  - `/api/installation/{id}/report/` - Generate installation report PDF
- [ ] Client portal UI:
  - "Download Warranty Certificate" button
  - "Download Installation Report" button
- [ ] Admin portal: Can generate certificates for any customer
- [ ] Cache generated PDFs for performance
- [ ] Write tests for PDF generation

### Technical Notes
- Use Django templates for PDF generation
- Include QR code linking to digital record
- Ensure proper branding (Pfungwa logo, colors)

---

## Issue 6: Build Retailer Solar Package Sales Interface

**Priority:** High (Expand sales reach)  
**Estimated Effort:** 7 days  
**Portals Affected:** Retailer, Admin

### Description
Per PDF: "Retailers sell standardized solar packages" and "submit customer orders." Build a complete sales interface for retailers to sell pre-configured solar system bundles.

### Acceptance Criteria
- [ ] Create `SolarPackage` model in admin:
  - Package name (e.g., "3kW Starter System")
  - System size
  - Included products (inverter, panels, batteries)
  - Price
  - Compatibility rules
  - Active status
- [ ] Admin interface to configure solar packages
- [ ] Create retailer portal "Solar Packages" page:
  - Display available packages
  - Package details (included equipment, price)
  - "Create Order" button
- [ ] Customer order submission form:
  - Customer details (name, phone, email, address)
  - Selected package
  - Payment method selection
  - Loan approval status (if applicable)
- [ ] Order submission workflow:
  - Create CustomerProfile if new
  - Create Order
  - Create InstallationRequest
  - Create SSR (if Issue #1 complete)
  - Send confirmation
- [ ] Order history page for retailer:
  - List all orders submitted
  - Filter by status
  - View order details
- [ ] API endpoints for package listing and order creation
- [ ] Write tests for order flow

### Technical Notes
- Implement compatibility validation (future enhancement)
- Link to payment integration (Paynow)
- Consider credit check integration for loans

---

## Issue 7: Add Installation & Warranty Tracking to Retailer Portal

**Priority:** Medium (Retailer visibility)  
**Estimated Effort:** 5 days  
**Portals Affected:** Retailer, Retailer Branch

### Description
Per PDF: Retailers should track installation status, warranty activation, and view warranty records. This provides transparency and reduces support requests.

### Acceptance Criteria
- [ ] Create "Installation Tracking" page in retailer portal:
  - List orders with installation status
  - Status indicators (Pending, Scheduled, In Progress, Completed)
  - Assigned technician
  - Scheduled date
  - Link to view details
- [ ] Installation detail view (read-only):
  - Customer info
  - System details
  - Installation progress (from SSR)
  - Photos (if completed)
- [ ] Create "Warranty Management" page:
  - List warranties for retailer's customers
  - Warranty status (Active, Expired)
  - Expiration dates
  - Active claims
- [ ] Product tracking during warranty:
  - View scanned products in/out
  - Track product movement
- [ ] Filter and search functionality
- [ ] API endpoints for tracking data
- [ ] Write tests for access control (retailer can only see their orders)

### Technical Notes
- Ensure proper permission checks
- Link to manufacturer job cards if available
- Consider notifications for status changes

---

## Issue 8: Implement Installer Payout Approval System

**Priority:** Medium (Admin financial management)  
**Estimated Effort:** 7 days  
**Portals Affected:** Admin

### Description
Per PDF: Admins should approve "installer payouts." Create a financial workflow for calculating and approving technician payments based on completed installations.

### Acceptance Criteria
- [ ] Create `InstallerPayout` model:
  - Technician
  - Related installations (ManyToMany to SSR)
  - Payout amount
  - Status (Pending, Approved, Rejected, Paid)
  - Calculation method
  - Notes
  - Created/approved dates
- [ ] Automatic payout calculation:
  - Trigger when installation marked complete
  - Calculate based on system size and rate
  - Consider quality metrics (future)
- [ ] Admin "Installer Payouts" page:
  - List pending payouts
  - Filter by technician, status, date
  - View payout details
  - Approve/reject buttons
  - Add notes
- [ ] Payout detail view:
  - Technician details
  - List of completed installations
  - Amount breakdown
  - Approval workflow
- [ ] Integration with Zoho for accounting:
  - Create bill/expense in Zoho when approved
  - Sync payment status
- [ ] Email notification to technician on approval
- [ ] Payout history view
- [ ] API endpoints for payout operations
- [ ] Write tests for calculation logic

### Technical Notes
- Define payout rates in configuration
- Consider multi-tier rates based on system size
- Ensure audit trail for financial compliance

---

## Issue 9: Add Warranty Rules & SLA Configuration to Admin Portal

**Priority:** Medium (Governance & automation)  
**Estimated Effort:** 5 days  
**Portals Affected:** Admin

### Description
Per PDF: Admins should configure warranty rules and SLA thresholds. This enables automatic warranty duration assignment and SLA violation tracking.

### Acceptance Criteria
- [ ] Create `WarrantyRule` model:
  - Product or product category
  - Warranty duration (days)
  - Terms and conditions
  - Active status
- [ ] Create `SLAThreshold` model:
  - Request type (installation, service, warranty claim)
  - Response time (hours)
  - Resolution time (hours)
  - Escalation rules
- [ ] Admin "Warranty Rules" page:
  - List rules
  - Add/edit/delete rules
  - Set duration by product
- [ ] Admin "SLA Configuration" page:
  - List SLA thresholds
  - Edit response/resolution times
  - Configure escalation
- [ ] Apply warranty rules automatically:
  - When warranty created, use rule to set end date
  - Override capability for special cases
- [ ] SLA tracking:
  - Calculate SLA status for requests
  - Flag violations
  - Send alerts when approaching deadline
- [ ] Dashboard widget showing SLA compliance
- [ ] API endpoints for configuration
- [ ] Write tests for automatic rule application

### Technical Notes
- Store SLA calculations efficiently
- Consider background task for SLA monitoring
- Add to admin dashboard for visibility

---

## Issue 10: Integrate Remote Monitoring Platform (Phase 1: Victron VRM)

**Priority:** Medium (Critical differentiator per PDF)  
**Estimated Effort:** 7 days  
**Portals Affected:** Client, Technician, Admin

### Description
Per PDF: "Integrate with inverter and battery monitoring platforms to enable automated fault detection." Start with Victron VRM as it's widely used in solar installations.

### Acceptance Criteria
- [ ] Research Victron VRM API documentation
- [ ] Create `MonitoringPlatformConfig` model:
  - Platform name (Victron VRM)
  - API credentials
  - Active status
- [ ] Create `MonitoringDevice` model:
  - Link to SSR
  - Platform
  - Device ID/serial
  - Installation ID on platform
  - Last sync timestamp
- [ ] Create `MonitoringAlert` model:
  - Device
  - Alert type (low battery, inverter error, etc.)
  - Severity
  - Message
  - Timestamp
  - Status (New, Acknowledged, Resolved)
  - Auto-created ticket (link to JobCard)
- [ ] Implement Victron VRM integration:
  - API authentication
  - Fetch device data
  - Poll for alerts
  - Webhook receiver (if supported)
- [ ] Automated fault ticket creation:
  - When alert received, create JobCard
  - Notify customer via WhatsApp
  - Assign technician based on rules
- [ ] Add monitoring ID field to SSR
- [ ] Client portal monitoring dashboard:
  - Current system status
  - Basic KPIs (power generation, battery level)
  - Alert history
- [ ] Admin view of all monitoring devices
- [ ] API endpoints for monitoring data
- [ ] Write tests for alert processing

### Technical Notes
- Start with read-only integration
- Use Celery task for periodic polling
- Consider rate limits of Victron API
- Design for multi-platform support (future: GoodWe, SolarMD)

---

## Issue 11: Branch Installer Allocation & Performance Metrics

**Priority:** Low (Operational efficiency)  
**Estimated Effort:** 7 days  
**Portals Affected:** Retailer Branch

### Description
Per PDF: Branch portal needs "installer allocation" and "regional performance metrics." Enhance the branch portal with job assignment and analytics.

### Acceptance Criteria
- [ ] Create "Assign Installer" interface in branch portal:
  - View pending installations
  - List available installers
  - Assign installer to installation
  - Set scheduled date
- [ ] Installer availability calendar:
  - View installer schedules
  - Show assigned jobs
  - Identify conflicts
- [ ] Performance metrics dashboard:
  - Installation completion rate
  - Average completion time
  - Customer satisfaction (if feedback exists)
  - Revenue by branch
  - Top performing installers
- [ ] KPI cards:
  - Installations this month
  - Pending installations
  - Completed installations
  - Customer complaints
- [ ] Date range filters for metrics
- [ ] Export reports (CSV/PDF)
- [ ] API endpoints for metrics
- [ ] Write tests for metric calculations

### Technical Notes
- Leverage existing analytics infrastructure
- Consider caching for performance
- Add comparison to previous periods

---

## Issue 12: Automatic SSR Creation on Solar Package Purchase

**Priority:** Medium (E-commerce integration)  
**Estimated Effort:** 5 days  
**Portals Affected:** Shop (Digital Shop), All

### Description
Per PDF: "Every sale = an SSR is created instantly." Implement post-order automation to create SSR and related records when a solar package is purchased.

### Acceptance Criteria
- [ ] Create post-order signal handler
- [ ] When solar package ordered:
  - [ ] Create SolarSystemInstallation (SSR)
  - [ ] Create InstallationRequest
  - [ ] Create Warranty records for included equipment
  - [ ] Grant customer portal access
  - [ ] Send confirmation email
  - [ ] Notify admin/branch for scheduling
- [ ] Implement compatibility validation:
  - Check battery ↔ inverter compatibility
  - Validate system size matches components
  - Flag incompatible orders for review
- [ ] Create `CompatibilityRule` model:
  - Product A
  - Compatible with Product B
  - Rule type (requires, incompatible)
- [ ] Admin interface for compatibility rules
- [ ] Validation during package configuration
- [ ] Order confirmation includes SSR ID
- [ ] API endpoint to check compatibility
- [ ] Write tests for automation flow

### Technical Notes
- Use Django signals (post_save on Order)
- Ensure idempotency (don't duplicate SSRs)
- Handle partial orders (non-solar items)
- Log all automatic actions for audit

---

## Summary Table

| # | Issue Title | Priority | Effort | Portals |
|---|-------------|----------|--------|---------|
| 1 | Solar System Record (SSR) Model | Critical | 7d | All |
| 2 | Digital Commissioning Checklists | High | 7d | Technician, Admin |
| 3 | Installation Photo Upload | High | 5d | Technician, Client |
| 4 | Serial Number Capture | High | 5d | Technician |
| 5 | Certificate & Report Generation | High | 7d | Client, Admin |
| 6 | Retailer Solar Package Sales | High | 7d | Retailer, Admin |
| 7 | Retailer Installation Tracking | Medium | 5d | Retailer |
| 8 | Installer Payout Approval | Medium | 7d | Admin |
| 9 | Warranty Rules & SLA Config | Medium | 5d | Admin |
| 10 | Remote Monitoring (Victron) | Medium | 7d | Client, Technician |
| 11 | Branch Performance Metrics | Low | 7d | Retailer Branch |
| 12 | Auto SSR on Purchase | Medium | 5d | Shop, All |

**Total: 12 issues, ~74 days effort**

---

## Recommended Implementation Order

### Phase 1: Foundation (Weeks 1-2)
1. Issue #1: Solar System Record (SSR) Model

### Phase 2: Technician Enablement (Weeks 3-5)
2. Issue #2: Digital Commissioning Checklists
3. Issue #3: Installation Photo Upload
4. Issue #4: Serial Number Capture

### Phase 3: Client Experience (Week 6)
5. Issue #5: Certificate & Report Generation

### Phase 4: Sales Expansion (Weeks 7-8)
6. Issue #6: Retailer Solar Package Sales
7. Issue #7: Retailer Installation Tracking

### Phase 5: Admin & Financial (Weeks 9-10)
8. Issue #8: Installer Payout Approval
9. Issue #9: Warranty Rules & SLA Config

### Phase 6: Monitoring & Automation (Weeks 11-12)
10. Issue #10: Remote Monitoring Integration
12. Issue #12: Auto SSR on Purchase

### Phase 7: Optimization (Week 13)
11. Issue #11: Branch Performance Metrics

---

## Notes for Implementation

1. **Issue #1 is mandatory first** - All other features depend on SSR
2. **Can parallelize** - Issues 2-4 can be done by different developers simultaneously
3. **Testing is critical** - Each issue must include comprehensive tests
4. **Mobile-first** - Technician portal features must work on mobile devices
5. **Security** - Ensure proper role-based access control for all features
6. **Documentation** - Update user guides as features are added
7. **Deployment** - Each issue should be deployable independently
8. **User feedback** - Pilot with small group before full rollout

---

## Alignment with PDF Vision

These 12 issues directly address the gaps identified in the PDF analysis and support the core vision:

✅ **Solar Lifecycle Operating System** - SSR anchors all workflows  
✅ **Faster sales conversion** - Retailer sales interface  
✅ **Controlled, auditable installations** - Checklists and photo evidence  
✅ **Reduced warranty risk** - Serial number tracking, proper documentation  
✅ **Long-term customer retention** - Monitoring integration, certificates  

All features orbit the SSR and maintain role-based separation of duties per the PDF requirements.
