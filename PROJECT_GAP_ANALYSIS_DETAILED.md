# HANNA Project Gap Analysis: Current vs Core Scope Document

**Analysis Date:** January 9, 2026  
**Document Reference:** Hanna Core Scope and Functionality.pdf  
**Reviewer:** GitHub Copilot AI Agent

## Executive Summary

This analysis compares the current HANNA system implementation against the core scope document that positions HANNA as a **Solar Lifecycle Operating System**. The system should manage sales → installation → warranty → monitoring → service → repeat business cycles.

### Key Finding: Missing Solar System Record (SSR)

The PDF emphasizes that **every portal should orbit a single master object: the Solar System Record (SSR)** - a unique digital file per installation. Currently, HANNA has:
- ✅ `InstallationRequest` model (basic tracking)
- ✅ `Warranty` model (linked to SerializedItem)
- ✅ `JobCard` model (service tracking)
- ❌ **No unified SSR that links all lifecycle data together**

## Portal-by-Portal Analysis

### 1. Admin Portal ✅ (MOSTLY COMPLETE)

**Current Implementation:**
- ✅ Master dashboard with stats
- ✅ Installation management
- ✅ Warranty claims approval
- ✅ Product configuration
- ✅ User management
- ✅ Analytics and monitoring

**Gaps:**
1. ❌ **Installer Payout Approval System** - No financial workflow for approving technician payments
2. ❌ **Warranty Rules Configuration UI** - No admin interface to set warranty duration rules by product
3. ❌ **SLA Threshold Configuration** - No configurable SLA (Service Level Agreement) settings
4. ❌ **Enhanced Zoho Financial Linkage** - Basic integration exists but not comprehensive enough for installer payouts

**Backend Status:** Strong foundation exists

---

### 2. Client Portal ✅ (COMPLETE)

**Current Implementation:**
- ✅ View installed system details (via orders/monitoring)
- ✅ Monitoring status
- ✅ Raise service requests
- ✅ Shop interface
- ✅ Order history

**Gaps:**
1. ❌ **Download Warranty Certificates** - No PDF generation/download feature
2. ❌ **Download Installation Reports** - No installation completion report with photos/commissioning data
3. ⚠️ **Fault Ticket Raising** - Service requests exist but may need dedicated fault ticket workflow

**Backend Status:** Service request models exist, need certificate generation

---

### 3. Technician Portal ⚠️ (SIGNIFICANT GAPS)

**Current Implementation:**
- ✅ Dashboard
- ✅ Installation history
- ✅ Check-in/out tracking
- ✅ Job assignments (implicit through installation requests)

**Critical Gaps (High Priority):**
1. ❌ **Digital Commissioning Checklist System**
   - Pre-installation checklist
   - Installation checklist
   - Commissioning checklist
   - **Hard control:** Job cannot be marked complete without all fields
   
2. ❌ **Photo Upload Interface**
   - Installation photos (before/during/after)
   - Equipment serial number photos
   - Site photos
   - Test result documentation

3. ❌ **Serial Number Capture**
   - Barcode scanning for equipment
   - Manual serial number entry
   - Validation against product database

4. ❌ **Test Results Upload**
   - Voltage readings
   - System performance metrics
   - Grid connection tests
   - Battery performance tests

5. ❌ **Installation Completion Workflow**
   - Cannot mark "Complete" without:
     - All checklist items checked
     - Required photos uploaded
     - Serial numbers recorded
     - Test results submitted

**Backend Status:** Models exist (`InstallationRequest`, `SerializedItem`) but need enhancement for checklists and media

---

### 4. Manufacturer Portal ✅ (WELL IMPLEMENTED)

**Current Implementation:**
- ✅ Dashboard with failure rates
- ✅ Product management
- ✅ Barcode scanner
- ✅ Product tracking
- ✅ Job cards system
- ✅ Warranty claims visibility
- ✅ Scan products in/out

**Minor Gaps:**
1. ⚠️ **Firmware Update Distribution** - May need dedicated firmware management if not present
2. ⚠️ **Fault Code Library** - Searchable database of fault codes and resolutions

**Backend Status:** Excellent implementation

---

### 5. Retailer Portal ⚠️ (MAJOR GAPS)

**Current Implementation:**
- ✅ Dashboard
- ✅ Branch management

**Critical Gaps:**
1. ❌ **Solar Package Sales Interface**
   - Pre-configured solar system bundles (3kW, 5kW, 6kW, 8kW)
   - Compatibility validation (inverter ↔ battery ↔ panels)
   - Standardized pricing

2. ❌ **Customer Order Submission**
   - Order creation for customers
   - Payment confirmation tracking
   - Loan approval confirmation

3. ❌ **Order History View**
   - Complete order history per branch
   - Customer order tracking

4. ❌ **Installation Status Tracking**
   - View status of submitted orders
   - Track installation progress

5. ❌ **Warranty Management**
   - View warranty activations
   - Access warranty records
   - View product movement during warranty repairs

**Backend Status:** Models exist but need dedicated retailer sales workflow

---

### 6. Retailer Branch Portal ⚠️ (MODERATE GAPS)

**Current Implementation:**
- ✅ Dashboard
- ✅ Order dispatch
- ✅ Check-in/out
- ✅ Inventory management
- ✅ History tracking
- ✅ Add serial numbers

**Gaps:**
1. ❌ **Installer Allocation Interface** - Assign installers to jobs from branch level
2. ❌ **Regional Performance Metrics** - Branch-specific KPIs (completion rates, customer satisfaction, revenue)

**Backend Status:** Good foundation, needs UI enhancements

---

## Core System Gaps (Backend & Architecture)

### 1. Solar System Record (SSR) - CRITICAL GAP ⚠️

**What's Missing:**
The system lacks a unified **Solar System Record** that serves as the master object linking:
- Customer profile
- System specifications (3kW/5kW/6kW/etc.)
- Equipment serial numbers (panels, inverter, batteries)
- Installer & technician assignments
- Installation photos & commissioning checklist
- Warranty status
- Remote monitoring ID
- Service history

**Current State:**
- Data is fragmented across `InstallationRequest`, `Warranty`, `SerializedItem`, `JobCard`
- No single "System Installation" model

**Recommendation:**
Create a new `SolarSystemInstallation` model that:
```python
class SolarSystemInstallation(models.Model):
    """
    The master Solar System Record (SSR) - a unique digital file per installation.
    All portals interact with this record with role-based permissions.
    """
    # Core Identity
    installation_id = models.CharField(unique=True)  # e.g., SSR-2026-001
    customer = models.ForeignKey(CustomerProfile)
    associated_order = models.ForeignKey(Order)
    
    # System Specifications
    system_size = models.CharField(choices=SYSTEM_SIZES)  # 3kW, 5kW, 6kW, 8kW
    system_type = models.CharField()  # Grid-tied, Off-grid, Hybrid
    
    # Equipment
    serialized_items = models.ManyToManyField(SerializedItem)  # Panels, inverter, batteries
    
    # Installation Lifecycle
    installation_request = models.OneToOneField(InstallationRequest)
    assigned_technicians = models.ManyToManyField(Technician)
    commissioning_checklist = models.JSONField()  # Structured checklist data
    installation_photos = models.ManyToManyField(MediaAsset)
    
    # Warranty
    warranties = models.ManyToManyField(Warranty)
    
    # Monitoring
    remote_monitoring_id = models.CharField()
    monitoring_platform = models.CharField()  # Victron, Goodwe, etc.
    
    # Service History
    job_cards = models.ManyToManyField(JobCard)
    
    # Status
    lifecycle_status = models.CharField()  # Ordered, Installing, Commissioned, Active, Service, Closed
```

---

### 2. Remote Monitoring Integration - MISSING ⚠️

**PDF Requirement:**
"Hanna should integrate with inverter and battery monitoring platforms to enable automated fault detection."

**Expected Flow:**
1. Monitoring system flags an issue
2. Hanna creates a fault ticket automatically
3. Client receives notification
4. Technician is assigned
5. Resolution logged back into the SSR

**Current State:**
- ❌ No integration with Victron VRM, GoodWe, SolarMD, or other monitoring platforms
- ❌ No automated fault detection
- ❌ No webhook listeners for monitoring alerts

**Required:**
- API integrations with monitoring platforms
- Webhook receivers for alerts
- Automated ticket creation
- Notification system (partially exists)

---

### 3. Digital Shop Integration - PARTIAL ⚠️

**PDF Requirement:**
"Every sale = an SSR is created instantly"

**Current State:**
- ✅ Digital shop exists (client portal)
- ✅ Orders are created
- ⚠️ No automatic SSR creation
- ⚠️ Limited compatibility validation
- ⚠️ No automatic warranty record creation on purchase

**Needed:**
- Post-order signal to create SSR
- Compatibility validation engine (battery ↔ inverter ↔ system size)
- Automatic warranty activation

---

### 4. Commissioning Checklist System - MISSING ❌

**PDF Requirement:**
"Step-by-step digital checklists: Pre-install, Installation, Commissioning"

**Current State:**
- ❌ No checklist models
- ❌ No checklist UI in technician portal

**Required Backend:**
```python
class CommissioningChecklistTemplate(models.Model):
    """Template for installation checklists"""
    name = models.CharField()  # "5kW Solar Installation Checklist"
    checklist_type = models.CharField()  # pre-install, install, commissioning
    items = models.JSONField()  # List of checklist items
    system_type = models.ForeignKey(Product)  # Link to system packages

class InstallationChecklistEntry(models.Model):
    """Actual checklist filled by technician"""
    solar_system = models.ForeignKey(SolarSystemInstallation)
    template = models.ForeignKey(CommissioningChecklistTemplate)
    completed_items = models.JSONField()
    photos = models.ManyToManyField(MediaAsset)
    completion_status = models.CharField()
    completed_by = models.ForeignKey(Technician)
    completed_at = models.DateTimeField()
```

---

### 5. Certificate Generation - MISSING ❌

**PDF Requirement:**
- Warranty certificates (downloadable by clients)
- Installation reports (with photos and commissioning data)

**Current State:**
- ❌ No PDF generation
- ❌ No certificate templates

**Required:**
- PDF generation library (e.g., WeasyPrint, ReportLab)
- Certificate templates
- API endpoints for certificate download
- Storage of generated certificates

---

## Prioritized Issues for Implementation (Week-Sized Tasks)

Based on the user's requirement that issues must be **completable within one week** and the PDF's core principles, here are prioritized implementable tasks:

### Priority 1: Core SSR Foundation (Week 1-2)

**Issue 1: Create Solar System Record (SSR) Model & Basic Integration**
- Create `SolarSystemInstallation` model
- Migrate existing `InstallationRequest` data
- Link to Customer, Order, Warranty
- Add basic admin interface
- Create API endpoints for SSR CRUD

**Scope:** Backend only, foundation for all other features  
**Effort:** 5-7 days

---

### Priority 2: Technician Portal Enhancements (Week 3-5)

**Issue 2: Implement Digital Commissioning Checklist System**
- Create `CommissioningChecklistTemplate` model
- Create `InstallationChecklistEntry` model
- Build technician UI for checklist completion
- Add pre-install, installation, commissioning templates
- Implement "cannot complete without all items" validation

**Scope:** Backend models + Technician portal UI  
**Effort:** 7 days

**Issue 3: Add Photo Upload to Installation Process**
- Enhance technician portal with photo upload
- Link photos to SSR
- Create photo gallery view
- Add photo requirements per checklist item
- Implement validation (required photos)

**Scope:** Frontend + Backend media handling  
**Effort:** 5 days

**Issue 4: Serial Number Capture & Validation**
- Add serial number entry to technician portal
- Implement barcode scanning in mobile-friendly UI
- Link serial numbers to SerializedItem and SSR
- Add validation against product database

**Scope:** Frontend + Backend validation  
**Effort:** 5 days

---

### Priority 3: Client Portal Enhancements (Week 6)

**Issue 5: Warranty Certificate & Installation Report Generation**
- Install PDF generation library
- Create warranty certificate template
- Create installation report template (with photos)
- Add download endpoints
- Add "Download Certificate" to client portal

**Scope:** Backend PDF generation + Client portal UI  
**Effort:** 7 days

---

### Priority 4: Retailer Portal Development (Week 7-8)

**Issue 6: Build Retailer Solar Package Sales Interface**
- Create "Solar Packages" (3kW, 5kW, 6kW, 8kW) configuration in admin
- Build retailer portal sales UI
- Add customer order submission form
- Implement payment/loan confirmation tracking
- Create order history view

**Scope:** Backend + Retailer portal complete buildout  
**Effort:** 7 days

**Issue 7: Add Installation Tracking to Retailer Portal**
- Add installation status view to retailer portal
- Show warranty activation status
- Display product tracking during warranty
- Link to SSR data (read-only)

**Scope:** Frontend dashboard + API integration  
**Effort:** 5 days

---

### Priority 5: Admin Portal Financial & Configuration (Week 9-10)

**Issue 8: Installer Payout Approval System**
- Create `InstallerPayout` model
- Add payout calculation based on completed installations
- Build admin approval workflow UI
- Integrate with Zoho for accounting
- Add payout history view

**Scope:** Backend + Admin portal UI  
**Effort:** 7 days

**Issue 9: Warranty Rules & SLA Configuration**
- Create `WarrantyRule` model (duration by product)
- Create `SLAThreshold` model (response times, resolution times)
- Build admin configuration UI
- Implement automatic warranty duration assignment
- Add SLA violation alerts

**Scope:** Backend configuration + Admin UI  
**Effort:** 5 days

---

### Priority 6: Remote Monitoring Integration (Week 11-12)

**Issue 10: Integrate Remote Monitoring Platform (Phase 1: Victron VRM)**
- Research Victron VRM API
- Create monitoring integration models
- Implement webhook receiver for alerts
- Create automatic fault ticket generation
- Add monitoring ID to SSR
- Build basic monitoring dashboard in client portal

**Scope:** Backend integration + API webhooks  
**Effort:** 7 days (per platform)

---

### Priority 7: Branch & Retailer Enhancements (Week 13)

**Issue 11: Branch Installer Allocation & Performance Metrics**
- Add installer allocation UI to retailer-branch portal
- Create regional performance dashboard
- Add KPI tracking (completion rates, customer satisfaction)
- Implement branch-level analytics

**Scope:** Frontend dashboards + Backend analytics  
**Effort:** 7 days

---

### Priority 8: Digital Shop SSR Auto-Creation (Week 14)

**Issue 12: Automatic SSR Creation on Solar Package Purchase**
- Add post-order signal handler
- Implement compatibility validation engine
- Auto-create SSR when solar package purchased
- Auto-create warranty records
- Auto-generate installation request
- Grant client portal access

**Scope:** Backend automation + validation logic  
**Effort:** 5 days

---

## Summary of Recommended Issues

| Priority | Issue | Effort | Portal(s) Affected |
|----------|-------|--------|-------------------|
| 1 | Create Solar System Record (SSR) Model | 7 days | All (foundation) |
| 2 | Digital Commissioning Checklist System | 7 days | Technician |
| 3 | Photo Upload for Installations | 5 days | Technician |
| 4 | Serial Number Capture & Validation | 5 days | Technician |
| 5 | Certificate & Report Generation | 7 days | Client, Admin |
| 6 | Retailer Solar Package Sales Interface | 7 days | Retailer |
| 7 | Installation Tracking for Retailers | 5 days | Retailer |
| 8 | Installer Payout Approval System | 7 days | Admin |
| 9 | Warranty Rules & SLA Configuration | 5 days | Admin |
| 10 | Remote Monitoring Integration (Victron) | 7 days | Client, Technician |
| 11 | Branch Performance & Allocation | 7 days | Retailer Branch |
| 12 | Auto SSR Creation on Purchase | 5 days | Shop, All |

**Total: 12 issues, ~74 days of work (14-15 weeks if done sequentially, or 7-8 weeks with 2 parallel tracks)**

---

## Architectural Recommendations

### 1. Implement SSR First
All other features depend on the Solar System Record being the central hub.

### 2. Follow PDF's Data Flow
```
Digital Shop/Retailer Sale
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

### 3. Role-Based SSR Access
- **Admin:** Full access, approval authority
- **Client:** Read-only view of their own SSR
- **Technician:** Can update installation progress, checklists, photos
- **Manufacturer:** View warranty and failure data
- **Retailer:** View orders and installation status
- **Branch:** Operational execution

### 4. Hard Controls (Per PDF)
- Technician cannot mark job complete without all required fields
- Retailers can only sell pre-approved system bundles
- All installations must have SSR
- No undocumented installations

---

## Conclusion

The current HANNA system has **excellent foundation** with all 6 portals in place and strong backend infrastructure. The main gaps are:

1. **No unified Solar System Record (SSR)** - the missing "anchor workflow"
2. **Technician portal lacks commissioning checklists and photo upload**
3. **Retailer portal is underdeveloped** - needs sales interface
4. **No remote monitoring integration**
5. **Missing certificate/report generation**
6. **No installer payout or SLA configuration**

The 12 recommended issues address these gaps and align HANNA with the PDF's vision of a comprehensive **Solar Lifecycle Operating System**.
