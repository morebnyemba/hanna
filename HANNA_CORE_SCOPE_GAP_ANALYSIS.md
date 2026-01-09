# Hanna Core Scope Gap Analysis
## Analysis Date: January 9, 2026

This document provides a comprehensive gap analysis comparing the current Hanna implementation with the **Solar Lifecycle Operating System** vision outlined in the "Hanna Core Scope and Functionality" PDF.

---

## Executive Summary

**Current State:** Hanna is currently architected as a WhatsApp CRM with general e-commerce capabilities. It has:
- ✅ Basic customer management
- ✅ Product catalog and order management
- ✅ Warranty tracking system
- ✅ Multiple portals (Admin, Client, Technician, Manufacturer, Retailer, Branch)
- ✅ WhatsApp flow automation
- ⚠️ Limited solar-specific workflow
- ❌ No centralized Solar System Record (SSR)
- ❌ No remote monitoring integration
- ❌ Incomplete installation workflow tracking

**Target State:** Solar Lifecycle Operating System managing:
1. Sales → Installation → Warranty → Monitoring → Service → Repeat Business

---

## Critical Missing Concept: Solar System Record (SSR)

### What the PDF Requires:
A **unique digital file per installation** that serves as the master object containing:
- Customer profile
- System size (3kW/5kW/6kW/etc.)
- Equipment serial numbers
- Installer & technician assignments
- Installation photos & commissioning checklist
- Warranty status
- Remote monitoring ID
- Service history

### Current State:
- ✅ `InstallationRequest` model exists but lacks comprehensive tracking
- ✅ `Order` and `OrderItem` models exist
- ✅ `SerializedItem` tracks individual products by serial number
- ✅ `Warranty` model links to serialized items
- ❌ No unified "Solar System Record" model that aggregates all lifecycle data
- ❌ No system size/capacity tracking field
- ❌ No commissioning checklist model
- ❌ No remote monitoring integration fields
- ❌ No installation photo gallery linked to installations

### Impact:
**HIGH** - This is the foundational concept. Without SSR, the system cannot achieve the strategic vision.

---

## Portal Analysis

### 3.1 Admin Portal - System Control Tower

#### PDF Requirements:
**Primary Role:** Governance, oversight, risk control

**Functions:**
- Master dashboard: total installs, active warranties, fault rates
- Approval of: new installations, warranty claims, installer payouts
- Configuration of: product bundles, warranty rules, SLA thresholds
- Financial linkage (Zoho/accounting layer)

#### Current Implementation:
**Frontend:** 
- Next.js: `/admin/(protected)/dashboard` ✅
- React: `Dashboard.jsx`, `AdminOverviewPage.jsx` ✅

**Capabilities:**
- ✅ Dashboard with stats (contacts, conversations, warranties, job cards)
- ✅ Warranty claim management (`AdminWarrantyClaimsPage.jsx`)
- ✅ User management (`AdminUsersPage.jsx`)
- ✅ Product management
- ✅ Technician management (`AdminTechniciansPage.jsx`)
- ✅ Manufacturer management (`AdminManufacturersPage.jsx`)
- ✅ Retailer management (`AdminRetailersPage.jsx`)
- ✅ Installation requests view (`InstallationRequestsPage.jsx`)
- ✅ Zoho integration exists
- ⚠️ Limited approval workflows (no explicit approval UI for installations)
- ❌ No product bundle configuration UI
- ❌ No warranty rules configuration
- ❌ No SLA threshold configuration
- ❌ No installer payout approval system
- ❌ No fault rate analytics

**Gap Assessment:** MODERATE - Core structure exists but lacks solar-specific governance features.

---

### 3.2 Client Portal - Customer Ownership & Self-Service

#### PDF Requirements:
**Primary Role:** Reduce inbound support and increase trust

**Functions:**
- View: installed system details, warranty validity, monitoring status (basic KPIs)
- Raise: fault tickets, service requests
- Download: warranty certificates, installation reports
- Receive: automated alerts (faults, maintenance reminders)

#### Current Implementation:
**Frontend:** Next.js `/client/(protected)/dashboard`

**Capabilities:**
- ✅ Dashboard with device monitoring (inverters, Starlink)
- ✅ Real-time metrics (battery level, power output, signal strength, temperature)
- ✅ Orders page (`/client/(protected)/orders`)
- ✅ Shop page (`/client/(protected)/shop`)
- ✅ Settings page
- ✅ Monitoring page with device status
- ⚠️ Mock data for device monitoring (not connected to real monitoring API)
- ❌ No warranty certificate download
- ❌ No installation report download
- ❌ No fault ticket submission UI from client portal
- ❌ No service request submission
- ❌ No automated alert system visible to client

**Gap Assessment:** MODERATE - Good UI foundation but lacks real monitoring integration and key self-service functions.

---

### 3.3 Technician Portal - Execution Layer

#### PDF Requirements:
**Primary Role:** Field operations and data capture

**Functions:**
- Job assignments (install/service)
- Step-by-step digital checklists: pre-install, installation, commissioning
- Upload: photos, serial numbers, test results
- Log faults and resolutions
- **Hard control:** Job cannot be marked "Complete" unless all required fields submitted

#### Current Implementation:
**Frontend:** Next.js `/technician/(protected)/dashboard`

**Capabilities:**
- ✅ Dashboard with technician-specific stats
- ✅ Job card tracking (open, completed)
- ✅ Installation tracking (pending, completed in period)
- ✅ Analytics endpoint (`/crm-api/analytics/technician/`)
- ✅ `Technician` model with types (installer, factory, callout)
- ✅ `JobCard` model with status tracking
- ✅ `InstallationRequest` model with technician assignment
- ❌ No digital checklist implementation
- ❌ No photo upload workflow within technician portal
- ❌ No test results capture form
- ❌ No commissioning checklist
- ❌ No hard validation preventing completion without required fields
- ❌ No mobile-optimized field app

**Gap Assessment:** HIGH - Structure exists but critical field execution tools are missing.

---

### 3.4 Manufacturer Portal - Warranty & Product Intelligence

#### PDF Requirements:
**Primary Role:** Upstream accountability

**Functions:**
- Visibility into: installed serial numbers, failure rates by model, warranty requests
- Receive: structured warranty claims (no WhatsApp chaos)
- Provide: firmware updates, fault codes guidance, repair reports linked to warranty
- Scan products in and out brought on warranty

#### Current Implementation:
**Frontend:** Next.js `/manufacturer/(protected)/dashboard`

**Capabilities:**
- ✅ Dashboard with warranty metrics
- ✅ Job cards page (`/manufacturer/(protected)/job-cards`)
- ✅ Warranty claims page (`/manufacturer/(protected)/warranty-claims`)
- ✅ Warranties page (`/manufacturer/(protected)/warranties`)
- ✅ Product tracking page (`/manufacturer/(protected)/product-tracking`)
- ✅ Barcode scanner (`/manufacturer/(protected)/barcode-scanner`)
- ✅ Check-in/out page (`/manufacturer/(protected)/check-in-out`)
- ✅ Analytics page with fault analytics
- ✅ `Manufacturer` model with user relationship
- ✅ Serial number tracking via `SerializedItem`
- ⚠️ Limited failure rate analytics (basic AI insights exist)
- ❌ No firmware update delivery system
- ❌ No fault code library/guidance system
- ❌ No repair report template system

**Gap Assessment:** MODERATE - Good foundation, needs enhancement of analytics and knowledge sharing.

---

### 3.5 Retailer Portal - Sales Distribution Engine

#### PDF Requirements:
**Primary Role:** Expand reach without operational chaos

**Functions:**
- Sell standardized solar packages
- Submit: customer orders, customer order history, payment/loan approval confirmation
- Track: installation status, warranty activation
- View: warranty records and reports, scanned products in/out during warranty repair
- **Key constraint:** Retailers sell only pre-approved system bundles

#### Current Implementation:
**Frontend:** Next.js `/retailer/(protected)/dashboard`

**Capabilities:**
- ✅ Retailer dashboard exists
- ✅ Branch management page (`/retailer/(protected)/branches`)
- ✅ `Retailer` model with company details
- ✅ `RetailerBranch` model for multi-location retailers
- ❌ No order submission UI for retailers
- ❌ No product catalog restricted to system bundles
- ❌ No installation status tracking view
- ❌ No warranty activation view
- ❌ No customer order history view
- ❌ No warranty repair tracking view

**Gap Assessment:** HIGH - Basic structure exists but lacks all key sales functions.

---

### 3.6 Branch Portal - Operational Visibility

#### PDF Requirements:
**Primary Role:** Decentralized execution, centralized standards

**Functions:**
- Local job tracking
- Installer allocation
- Stock visibility (if enabled)
- Regional performance metrics
- Barcode scanning in/out of branch products moving through warranty process

#### Current Implementation:
**Frontend:** Next.js `/retailer-branch/(protected)/dashboard`

**Capabilities:**
- ✅ Branch dashboard
- ✅ Order dispatch page (`/retailer-branch/(protected)/order-dispatch`)
- ✅ Check-in/out page (`/retailer-branch/(protected)/check-in-out`)
- ✅ Inventory page (`/retailer-branch/(protected)/inventory`)
- ✅ History page (`/retailer-branch/(protected)/history`)
- ✅ Add serial page (`/retailer-branch/(protected)/add-serial`)
- ✅ Barcode scanning capability exists
- ⚠️ Limited to product tracking, not job tracking
- ❌ No installer allocation UI
- ❌ No regional performance dashboard

**Gap Assessment:** MODERATE - Good product tracking, needs job management features.

---

## 4. Remote Monitoring Integration (Critical Differentiator)

### PDF Requirements:
Integration with inverter and battery monitoring platforms to enable:
- Automated fault detection (low battery health, grid anomalies, inverter errors, system downtime)
- Workflow: Monitoring flags issue → Hanna creates fault ticket → Client notified → Technician assigned → Resolution logged

**Business Impact:**
- Fewer emergency calls
- Predictive maintenance
- Proof-based warranty claims
- Reduced truck rolls

### Current Implementation:
- ✅ Client portal has monitoring UI (inverters and Starlink)
- ✅ Mock data for device metrics (battery, power, signal, temperature)
- ❌ No actual integration with inverter monitoring APIs
- ❌ No automated fault detection
- ❌ No automatic ticket creation from monitoring alerts
- ❌ No monitoring platform configuration in admin
- ❌ No remote monitoring ID field in installation records

**Gap Assessment:** CRITICAL - This is a key differentiator that doesn't exist yet.

---

## 5. Digital Shop as Controlled Entry Point

### PDF Requirements:
The Digital Shop should:
- Sell mainly solar packages
- Limit loose component sales (only for additional material by internal installers)
- Force compatibility logic (battery ↔ inverter ↔ system size)
- Automatically generate: installation job, warranty record, client portal access, payment processing
- **Every sale = an SSR is created instantly**

### Current Implementation:
**Frontend:** Next.js `/shop` and React `OrdersPage.jsx`

**Capabilities:**
- ✅ Product catalog exists
- ✅ Order creation capability
- ✅ Payment integration (Paynow)
- ✅ Product categories system
- ✅ Serial number assignment to orders
- ⚠️ No explicit "solar package" product type
- ❌ No compatibility validation logic
- ❌ No automatic installation job creation on sale
- ❌ No automatic warranty record creation
- ❌ No automatic client portal account creation
- ❌ No system bundle restriction logic
- ❌ No SSR creation on sale

**Gap Assessment:** HIGH - E-commerce exists but lacks solar-specific automation.

---

## 6. End-to-End Data Flow Analysis

### PDF Required Flow:
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

### Current Flow Capability:
```
✅ Order Creation (Digital Shop/Retailer)
        ↓
❌ No SSR Creation (manual InstallationRequest possible)
        ↓
⚠️ Technician Assignment (manual via InstallationRequest)
        ↓
❌ No Digital Commissioning Process
        ↓
⚠️ Warranty Creation (manual)
        ↓
❌ No Monitoring Linkage
        ↓
⚠️ Service via JobCard (reactive, not proactive)
```

**Gap Assessment:** CRITICAL - Flow is fragmented with many manual steps.

---

## Technical Infrastructure Assessment

### Backend (Django)
**Strengths:**
- ✅ Modular app structure
- ✅ RESTful API with DRF
- ✅ JWT authentication
- ✅ Celery for background tasks
- ✅ Django Channels for WebSockets
- ✅ Comprehensive models for warranty, customers, products
- ✅ Serial number tracking
- ✅ Barcode scanning support
- ✅ Zoho integration
- ✅ WhatsApp flow automation

**Gaps:**
- ❌ No monitoring integration app
- ❌ No commissioning checklist models
- ❌ No SSR (Solar System Record) model
- ❌ No automated workflow orchestration for sales → installation → warranty
- ❌ No product bundle/package model
- ❌ No compatibility validation rules engine

### Frontend - React Dashboard (Vite)
**Purpose:** Internal admin/operations dashboard

**Strengths:**
- ✅ Real-time conversation management
- ✅ Flow builder/editor
- ✅ Contact management
- ✅ Analytics dashboard
- ✅ Order management
- ✅ Installation request viewing

**Gaps:**
- ❌ No SSR management interface
- ❌ No commissioning workflow UI
- ❌ No approval workflow interfaces

### Frontend - Next.js Management Portal
**Purpose:** Role-based portals for different stakeholders

**Strengths:**
- ✅ Well-structured multi-portal architecture
- ✅ Clean separation of admin/client/technician/manufacturer/retailer/branch
- ✅ Modern UI with Tailwind and shadcn/ui
- ✅ TypeScript for type safety
- ✅ Authentication and authorization

**Gaps:**
- ❌ Missing solar-specific workflows in all portals
- ❌ No SSR views
- ❌ No monitoring integration displays (except mock client dashboard)
- ❌ Incomplete retailer sales workflows

---

## Priority Gap Categories

### 1. CRITICAL (System Architecture) - Week 1-2 Focus
These gaps prevent the system from being a "Solar Lifecycle Operating System":

1. **Solar System Record (SSR) Model** - The foundational concept
2. **Automated Sale-to-Installation Workflow** - The critical pipeline
3. **Remote Monitoring Integration Framework** - The differentiator

### 2. HIGH (Core Functionality) - Week 3-4 Focus
These gaps limit operational efficiency:

1. **Digital Commissioning Checklist** - Quality assurance
2. **Technician Field Tools** - Mobile-friendly job execution
3. **Retailer Sales Portal** - Revenue expansion
4. **Product Bundle System** - Controlled offerings

### 3. MEDIUM (Enhanced Features) - Month 2 Focus
These gaps reduce competitive advantage:

1. **Fault Analytics & Predictive Maintenance** - Intelligence
2. **Client Self-Service Tools** - Support reduction
3. **Manufacturer Product Intelligence** - Partnership value

### 4. LOW (Optimization) - Month 3+ Focus
These are nice-to-haves:

1. **Advanced reporting and dashboards**
2. **Mobile apps (native)**
3. **Multi-language support**

---

## Recommendations for 1-Week Implementation Sprints

Given the constraint that issues must be completable within a week, we should focus on incremental improvements that build toward the vision rather than attempting the full transformation at once.

### Recommended Approach:
1. Start with data model enhancements (SSR foundation)
2. Add automation triggers between existing models
3. Enhance portal UIs with missing views
4. Integrate external monitoring APIs
5. Build workflow orchestration layer

Each issue should be scoped to:
- Take 3-5 days for an experienced developer
- Have clear acceptance criteria
- Not break existing functionality
- Move incrementally toward the SSR vision

---

## Next Steps

The following document `IMPLEMENTABLE_ISSUES_WEEK1.md` will contain 5-7 specific, actionable issues that can be completed within one week and begin closing these gaps.

