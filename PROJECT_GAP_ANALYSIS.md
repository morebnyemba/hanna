# Project Gap Analysis: HANNA vs. PDF Scope & Functionality

**Document Date:** 2026-01-09  
**Source:** Hanna Core Scope and Functionality.pdf  
**Analysis Purpose:** Identify gaps between current implementation and solar lifecycle operating system vision

---

## Executive Summary

The PDF document positions **HANNA** as a **Solar Lifecycle Operating System** rather than a generic e-commerce platform. The system should manage the complete solar installation lifecycle from sales → installation → warranty → monitoring → service → repeat business.

### Current State
HANNA has strong foundations with:
- WhatsApp CRM integration
- Product and order management
- Warranty tracking system
- Installation request management
- User role system (Admin, Technician, Manufacturer, Retailer, Branch)
- Payment processing integration

### Key Gaps Identified
1. **Missing Solar System Record (SSR)** - No central "anchor" model for solar installations
2. **Incomplete Portal Separation** - Portals not clearly separated by role
3. **No Client Portal** - Customers cannot self-serve or view their system status
4. **Limited Technician Portal** - Missing digital checklists and step-by-step workflows
5. **Incomplete Manufacturer Portal** - Limited visibility and warranty claim management
6. **No Remote Monitoring Integration** - Critical differentiator missing
7. **Digital Shop not Solar-Focused** - Not configured for solar package bundles
8. **Missing Installation Evidence Trail** - No photo upload, commissioning checklists

---

## 1. Strategic Positioning Gap

### PDF Requirement
Position HANNA as a **Solar Lifecycle Operating System** managing four core objectives:
1. Faster sales conversion
2. Controlled, auditable installations
3. Reduced warranty risk and call-outs
4. Long-term customer retention and upselling

### Current Implementation
- Generic CRM/e-commerce system
- No explicit solar focus in UI/branding
- No lifecycle tracking beyond basic order → installation → warranty

### Gap Impact: **HIGH**
Without clear solar positioning, the system doesn't enforce solar-specific workflows and constraints.

---

## 2. Solar System Record (SSR) - Core Missing Component

### PDF Requirement
A **Solar System Record (SSR)** should be the master object that all portals interact with:
- Customer profile
- System size (3kW/5kW/6kW/etc.)
- Equipment serial numbers
- Installer & technician assignments
- Installation photos & commissioning checklist
- Warranty status
- Remote monitoring ID
- Service history

### Current Implementation
**No SSR model exists.** Current related models:
- `InstallationRequest` - Tracks installation requests but not ongoing system lifecycle
- `Order` - Sales orders without solar-specific fields
- `Warranty` - Tracks warranties but not linked to complete installation record
- `SerializedItem` - Tracks individual components but not the complete system

### Gap Impact: **CRITICAL**
The SSR is the foundational concept. Without it:
- No single source of truth for an installation
- Cannot track complete system lifecycle
- Portals lack a common reference point
- Cannot correlate monitoring data with installation records

### Required Actions
1. Create `SolarSystemRecord` model with all required fields
2. Link Order, InstallationRequest, Warranty, and SerializedItems to SSR
3. Make SSR the central navigation point for all portals
4. Add SSR unique identifier visible to customers

---

## 3. Portal Role & Responsibilities Gaps

### 3.1 Admin Portal

#### PDF Requirement
**Primary Role:** Governance, oversight, risk control

**Functions:**
- Master dashboard (total installs, active warranties, fault rates)
- Approval workflows (installations, warranty claims, installer payouts)
- Configuration (product bundles, warranty rules, SLA thresholds)
- Financial linkage (Zoho/accounting)

**Critical Rule:** Admins authorize and audit, not fix problems

#### Current Implementation
✅ Admin dashboard exists with overview stats  
✅ Admin can manage technicians, manufacturers, retailers  
✅ Admin can view warranties and claims  
⚠️ Approval workflows not explicit (no pending approvals queue)  
❌ No product bundle configuration for solar packages  
❌ No SLA threshold configuration  
❌ Financial linkage limited  

#### Gap Impact: **MEDIUM**
Core admin functions exist but lack solar-specific workflows and approval processes.

---

### 3.2 Client Portal

#### PDF Requirement
**Primary Role:** Reduce inbound support, increase trust

**Functions:**
- **View:**
  - Installed system details
  - Warranty validity
  - Monitoring status (basic KPIs)
- **Raise:**
  - Fault tickets
  - Service requests
- **Download:**
  - Warranty certificates
  - Installation reports
- **Receive:**
  - Automated alerts (faults, maintenance reminders)

#### Current Implementation
❌ **No client portal exists**  
❌ Customers cannot log in to view their systems  
❌ No self-service fault reporting  
❌ No warranty certificate download  
❌ No automated alerts to customers  

#### Gap Impact: **CRITICAL**
Without a client portal, customers must contact support for all inquiries, creating unnecessary load and reducing trust.

---

### 3.3 Technician Portal

#### PDF Requirement
**Primary Role:** Field operations and data capture

**Functions:**
- Job assignments (install/service)
- Step-by-step digital checklists:
  - Pre-install checklist
  - Installation checklist
  - Commissioning checklist
- Upload requirements:
  - Photos
  - Serial numbers
  - Test results
- Log faults and resolutions

**Hard Control:** Job cannot be marked "Complete" unless all required fields submitted

#### Current Implementation
⚠️ Basic technician functionality exists  
✅ Technicians can be assigned to installations  
❌ No digital checklists  
❌ No photo upload workflow tied to installations  
❌ No commissioning checklist enforcement  
❌ Cannot enforce completion requirements  

#### Gap Impact: **HIGH**
Technicians lack guided workflows, leading to incomplete documentation and warranty liability.

---

### 3.4 Manufacturer Portal

#### PDF Requirement
**Primary Role:** Upstream accountability

**Functions:**
- **Visibility:**
  - Installed serial numbers
  - Failure rates by model
  - Warranty requests
- **Receive:**
  - Structured warranty claims (no WhatsApp chaos)
- **Provide:**
  - Firmware updates
  - Fault codes guidance
  - Repair reports linked to warranty request and customer ID
  - Scan products in/out during warranty

#### Current Implementation
✅ Manufacturer model exists  
✅ Manufacturers can be linked to products  
✅ Manufacturers can view warranty claims  
❌ No failure rate analytics by model  
❌ No structured warranty claim submission workflow  
❌ No repair report submission from manufacturers  
❌ No product scan in/out tracking during warranty  

#### Gap Impact: **MEDIUM-HIGH**
Manufacturers exist in system but lack tools for professional data-driven partnership.

---

### 3.5 Retailer Portal

#### PDF Requirement
**Primary Role:** Sales distribution engine

**Functions:**
- Sell standardized solar packages
- **Submit:**
  - Customer orders
  - Customer order history
  - Payment or loan approval confirmation
- **Track:**
  - Installation status
  - Warranty activation
  - View warranty records and reports
  - View scanned products in/out during warranty repair

**Key Constraint:** Retailers sell only pre-approved system bundles to avoid undersizing risks

#### Current Implementation
✅ Retailer and RetailerBranch models exist  
⚠️ Retailers can be managed by admin  
❌ No standardized solar package bundles  
❌ Cannot restrict retailer sales to approved bundles only  
❌ No retailer-specific order submission portal  
❌ Retailers cannot track installation status of their orders  
❌ No warranty activation visibility for retailers  

#### Gap Impact: **HIGH**
Retailer infrastructure exists but lacks solar-specific constraints and workflows.

---

### 3.6 Branch Portal

#### PDF Requirement
**Primary Role:** Decentralized execution, centralized standards

**Functions:**
- Local job tracking
- Installer allocation
- Stock visibility (if enabled)
- Regional performance metrics
- Barcode scanning in/out for warranty products

#### Current Implementation
✅ RetailerBranch model exists  
❌ No branch-specific portal  
❌ No local job tracking for branches  
❌ No stock visibility system  
❌ No barcode scanning functionality for branches  
❌ No regional performance metrics  

#### Gap Impact: **MEDIUM**
Branch infrastructure exists in data model but not exposed as functional portal.

---

## 4. Remote Monitoring Integration Gap

### PDF Requirement
**Critical Differentiator** - Integrate with inverter and battery monitoring platforms to enable:

**Automated Fault Detection:**
- Low battery health
- Grid anomalies
- Inverter errors
- System downtime

**Flow:**
1. Monitoring system flags issue
2. HANNA creates fault ticket automatically
3. Client receives notification
4. Technician is assigned
5. Resolution logged back into SSR

**Business Impact:**
- Fewer emergency calls
- Predictive maintenance
- Proof-based warranty claims
- Reduced truck rolls

### Current Implementation
❌ **No remote monitoring integration exists**  
❌ No monitoring platform API integration  
❌ No automated fault detection  
❌ No monitoring data storage  
❌ No KPI dashboard for system performance  

#### Gap Impact: **CRITICAL**
This is described as a "critical differentiator" - without it, HANNA cannot offer proactive service or predictive maintenance.

---

## 5. Digital Shop as Controlled Entry Point

### PDF Requirement
Digital Shop should:
- Sell mainly solar packages
- Loose component sales initially limited (for additional material by internal installers)
- Force compatibility logic (battery ↔ inverter ↔ system size)
- Automatically generate:
  - Installation job
  - Warranty record
  - Client portal access
  - Payment processing and e-receipt

**Every sale = SSR created instantly**

### Current Implementation
✅ Product catalog exists  
✅ Shopping cart system exists  
✅ Order creation exists  
✅ Payment processing integrated (Paynow)  
❌ No solar package bundles  
❌ No compatibility validation logic  
❌ No automatic installation job creation on purchase  
❌ No automatic warranty record creation  
❌ No automatic client portal access provisioning  
❌ SSR doesn't exist to create  

#### Gap Impact: **HIGH**
Digital shop exists but is generic e-commerce, not solar-focused with proper constraints.

---

## 6. End-to-End Data Flow Gap

### PDF Requirement
```
Digital Shop / Retailer Sale
         ↓
Solar System Record Created
         ↓
Technician Assigned
         ↓
Installation & Commissioning
         ↓
Warranty Activated
         ↓
Remote Monitoring Linked
         ↓
Ongoing Service & Upsell
```

### Current Implementation
Current flow is fragmented:
1. Order created ✅
2. Installation request created (manual) ⚠️
3. Technician assigned (manual) ⚠️
4. Installation completed (basic tracking) ⚠️
5. Warranty created (if serialized items assigned) ⚠️
6. No monitoring linkage ❌
7. No structured ongoing service ❌

#### Gap Impact: **HIGH**
Flow is not automated or enforced, leading to potential missed steps and incomplete data.

---

## 7. Data Model Gaps

### Missing Core Models

#### 7.1 SolarSystemRecord (CRITICAL)
**Purpose:** Central record for each installation
**Fields Needed:**
- Unique system ID
- Customer (FK)
- System size (e.g., 3kW, 5kW)
- Installation date
- Commissioning date
- Status (pending, active, decommissioned)
- Equipment list (linked SerializedItems)
- Installer/technician assignments
- Remote monitoring ID
- Photos and documents
- Service history

#### 7.2 SystemComponent (NEW)
**Purpose:** Link serialized items to a solar system
**Fields Needed:**
- Solar system (FK)
- Serialized item (FK)
- Component role (inverter, battery, panel, etc.)
- Installation date
- Commissioning status

#### 7.3 InstallationChecklist (NEW)
**Purpose:** Digital checklist enforcement
**Fields Needed:**
- Solar system (FK)
- Checklist type (pre-install, installation, commissioning)
- Checklist items (JSON or related model)
- Completion status
- Completed by (technician)
- Completion date
- Photos/evidence

#### 7.4 MonitoringSystem (NEW)
**Purpose:** Link to remote monitoring platforms
**Fields Needed:**
- Solar system (FK)
- Platform name (e.g., "Victron VRM", "SolarEdge")
- Platform system ID
- API credentials (encrypted)
- Last sync timestamp
- Current status

#### 7.5 MonitoringAlert (NEW)
**Purpose:** Store monitoring alerts/faults
**Fields Needed:**
- Solar system (FK)
- Alert type
- Severity
- Description
- Detected timestamp
- Auto-created job card (FK, optional)
- Resolution status

#### 7.6 SolarPackage (NEW)
**Purpose:** Pre-configured solar system bundles
**Fields Needed:**
- Package name (e.g., "3kW Residential")
- System size
- Included products (M2M)
- Compatibility rules (JSON)
- Price
- Active status

### Model Enhancements Needed

#### 7.7 InstallationRequest → Enhanced
**Add:**
- Link to SolarSystemRecord (once created)
- Installation evidence (photos)
- Commissioning checklist completion
- Cannot close until checklist complete

#### 7.8 Warranty → Enhanced
**Add:**
- Link to SolarSystemRecord
- Link to SystemComponent (specific component under warranty)
- Automatic expiry alerts

#### 7.9 Order → Enhanced
**Add:**
- Solar package (FK, if applicable)
- Auto-generate SSR flag
- Auto-generate installation job flag

#### 7.10 CustomerProfile → Enhanced
**Add:**
- Portal access enabled flag
- Alert preferences
- Preferred contact method

---

## 8. Business Logic & Workflow Gaps

### 8.1 Order to Installation Workflow
**Missing:**
- Automatic installation job creation when order is solar package
- Automatic technician assignment based on location/availability
- Email/SMS notifications to customer with expected timeline

### 8.2 Installation Completion Workflow
**Missing:**
- Checklist enforcement (cannot complete without all items)
- Automatic warranty activation when installation complete
- Automatic client portal credential creation
- Automatic monitoring system linkage

### 8.3 Warranty Claim Workflow
**Missing:**
- Approval queue for admins
- Manufacturer notification system
- Repair tracking workflow
- Product scan in/out during repair
- Completion notification to customer

### 8.4 Monitoring Alert Workflow
**Missing:**
- Automatic fault detection from monitoring API
- Auto-create job card for faults
- Customer notification of detected issues
- Technician assignment for service

### 8.5 Package Compatibility Validation
**Missing:**
- Compatibility rules engine
- Validation during cart checkout
- Prevention of incompatible component combinations

---

## 9. Frontend/Portal Gaps

### 9.1 Missing Portals
- **Client Portal** - Complete absence
- **Dedicated Technician Portal** - Partial, needs enhancement
- **Branch Portal** - Data model exists, no UI

### 9.2 Admin Portal Enhancements Needed
- Approval workflows dashboard
- Solar package configuration
- SLA configuration
- Financial dashboard (Zoho integration)
- Performance metrics by installer/branch

### 9.3 Manufacturer Portal Enhancements Needed
- Failure rate analytics
- Structured warranty claim forms
- Repair report submission
- Product scan in/out interface

### 9.4 Retailer Portal Enhancements Needed
- Order submission interface
- Installation tracking
- Warranty status view
- Restricted to approved solar packages only

---

## 10. Integration Gaps

### 10.1 Remote Monitoring Integration (CRITICAL)
**Status:** Not implemented
**Required:**
- Integration with major platforms:
  - Victron VRM
  - SolarEdge
  - Goodwe
  - Huawei FusionSolar
- API clients for each platform
- Scheduled data sync (Celery tasks)
- Alert webhook receivers
- KPI calculation and storage

### 10.2 Enhanced Zoho Integration
**Current:** Basic product sync exists
**Missing:**
- Order sync to Zoho
- Financial data sync
- Invoice generation
- Payment reconciliation

### 10.3 Notification System Enhancement
**Current:** Basic notifications exist
**Missing:**
- Customer-facing alerts (faults, maintenance reminders)
- Automated notification workflows
- Multi-channel (email, SMS, WhatsApp)

---

## 11. Security & Access Control Gaps

### 11.1 Role-Based Access Control (RBAC)
**Current:** Basic staff/superuser permissions
**Missing:**
- Granular portal-specific permissions
- Manufacturer can only see their products
- Retailer can only see their orders
- Branch can only see their region
- Technician can only see assigned jobs
- Client can only see their own systems

### 11.2 Data Privacy
**Missing:**
- Customer consent tracking for portal access
- Data access logging
- GDPR compliance features

---

## 12. Reporting & Analytics Gaps

### 12.1 Missing Reports
- Installation completion rate by technician
- Warranty claim rate by product/manufacturer
- Average resolution time for faults
- Monitoring system health dashboard
- Regional performance comparison
- Revenue by solar package type

### 12.2 Missing Dashboards
- Real-time installation pipeline (sales → install → commission)
- Active warranty overview with expiry alerts
- Fault rate trends
- Customer satisfaction metrics

---

## 13. Documentation Gaps

### 13.1 Missing User Documentation
- Client portal user guide
- Technician checklist instructions
- Manufacturer warranty claim guide
- Retailer order submission guide

### 13.2 Missing Technical Documentation
- SSR data model diagram
- End-to-end workflow diagrams
- API documentation for monitoring integrations
- Deployment guide for solar-specific features

---

## Priority Ranking

### P0 - Critical (Must Have)
1. **Solar System Record (SSR) Model** - Foundation for everything
2. **Client Portal** - Customer self-service and transparency
3. **Installation Checklist Enforcement** - Warranty protection
4. **Remote Monitoring Integration** - Critical differentiator

### P1 - High (Should Have)
5. **Solar Package Bundles** - Controlled sales
6. **Digital Shop Auto-workflows** - Order → SSR → Installation
7. **Enhanced Technician Portal** - Digital checklists and workflows
8. **Manufacturer Portal Enhancement** - Failure analytics, repair tracking
9. **Warranty Claim Approval Workflow** - Admin governance
10. **Role-Based Portal Access** - Security and proper separation

### P2 - Medium (Nice to Have)
11. **Branch Portal** - Decentralized operations
12. **Retailer Portal Enhancement** - Installation tracking
13. **Enhanced Reporting** - Analytics and trends
14. **Automated Notifications** - Customer alerts
15. **Zoho Financial Integration** - Accounting sync

### P3 - Low (Future)
16. **Predictive Maintenance** - Advanced monitoring analytics
17. **Customer Mobile App** - Native mobile experience
18. **Multi-currency Support** - International expansion
19. **Service History AI Analysis** - Pattern detection

---

## Recommended Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
1. Create Solar System Record model and migrations
2. Link existing models to SSR
3. Create basic Client Portal with view-only access
4. Implement Installation Checklist model
5. Add role-based permissions framework

### Phase 2: Core Workflows (Weeks 5-8)
6. Solar Package Bundle creation
7. Order → SSR → Installation auto-workflows
8. Technician digital checklists
9. Client portal fault reporting
10. Warranty automatic activation

### Phase 3: Monitoring & Advanced Features (Weeks 9-12)
11. Remote Monitoring Integration (start with one platform)
12. Automated fault detection and alerts
13. Manufacturer portal enhancements
14. Retailer portal enhancements
15. Admin approval workflows

### Phase 4: Optimization (Weeks 13-16)
16. Branch portal
17. Advanced analytics and reporting
18. Performance optimization
19. Documentation completion
20. User training materials

---

## Success Metrics

### Operational Metrics
- **Installation documentation completion rate:** Target 100%
- **Average time from sale to installation:** Track and reduce
- **Warranty claim resolution time:** Track and reduce
- **Customer support ticket volume:** Track and reduce via self-service

### Business Metrics
- **Customer satisfaction score:** Measure portal usage and satisfaction
- **Repeat business rate:** Track upsells and additional installations
- **Installer productivity:** Track installations per technician
- **Warranty claim rate by manufacturer:** Hold manufacturers accountable

### Technical Metrics
- **System uptime for monitoring:** Target 99.9%
- **Alert response time:** From detection to technician assignment
- **Data completeness:** Percentage of SSRs with all required fields

---

## Conclusion

HANNA has solid technical foundations but requires significant enhancements to fulfill the vision of a Solar Lifecycle Operating System. The most critical missing piece is the **Solar System Record (SSR)** as the central data model. Following that, the **Client Portal** and **Remote Monitoring Integration** are essential for achieving the strategic objectives outlined in the PDF.

The gaps identified are substantial but addressable with focused development effort. The recommended phased approach allows for incremental delivery of value while building toward the complete vision.

**Next Steps:**
1. Review and validate this analysis with stakeholders
2. Create GitHub issues based on priority ranking
3. Begin Phase 1 implementation with SSR model creation
4. Set up project tracking and success metrics
