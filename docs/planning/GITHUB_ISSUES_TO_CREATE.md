# Quick Reference: Issues to Create for Installation System Transformation

This document provides a quick reference for the **7 GitHub issues** that should be created to align Hanna with the Installation Lifecycle Operating System vision from the PDF. **Supports multiple installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid Solar+Starlink (SSI).

---

## ✅ Ready to Create - Week 1 Sprint (UPDATE: Mostly Implemented)

**Implementation Note:** As of January 17, 2026, Issues 1, 3, and 4 are **fully implemented**. Issues 5-7 have backend complete but frontend not started. Issue 2 is partially implemented (solar only).

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for detailed status.

### Issue #1: Create Installation System Record (ISR) Model Foundation ✅ IMPLEMENTED
**Labels:** `backend`, `critical`, `data-model`, `multi-type`  
**Assignees:** Backend team  
**Estimated:** 3-4 days  
**Status:** ✅ **COMPLETE** (100%)

**Description:**
Create the foundational `InstallationSystemRecord` model that serves as the master object for tracking every installation throughout its lifecycle. Supports **all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI). This is THE core concept from the PDF that's currently missing.

**Implementation Details:**
- ✅ Django app created: `whatsappcrm_backend/installation_systems/`
- ✅ `InstallationSystemRecord` model with all required fields
- ✅ All relationships: Customer, Order, Technicians, Components, Warranties, JobCards
- ✅ Multi-type support with flexible capacity units
- ✅ Database migrations applied
- ✅ Admin interface implemented
- ✅ Tests written and passing
- ✅ **BONUS:** Photo tracking, payout system, branch models also implemented

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 1 for full details.

---

### Issue #2: Add System Bundles / Installation Packages Model 🚧 PARTIAL
**Labels:** `backend`, `high-priority`, `data-model`, `api`, `multi-type`  
**Assignees:** Backend team  
**Estimated:** 2-3 days  
**Status:** 🚧 **PARTIAL** (25% - Solar only)

**Description:**
Create models and APIs for pre-configured installation packages for **all installation types**: Solar packages (e.g., "3kW Residential Kit"), Starlink packages (e.g., "Starlink Business Kit"), Custom Furniture packages (e.g., "Office Furniture Set"), and Hybrid packages. This enables controlled offerings where retailers sell only approved bundles.

**Implementation Details:**
- ✅ `SolarPackage` model exists in `products_and_services` app
- ✅ `SolarPackageProduct` through model for components
- ❌ Generic `SystemBundle` model NOT created (solar-specific only)
- ❌ `BundleComponent` model NOT created
- ❌ No support for starlink/furniture/hybrid bundles
- ❌ REST API endpoints NOT created

**Remaining Work:**
- Create generalized `SystemBundle` model replacing `SolarPackage`
- Add `installation_type` and `capacity_unit` fields
- Create REST API endpoints for bundle management

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 2 for full details.

---

### Issue #3: Automated ISR Creation on Installation Product Sale ✅ IMPLEMENTED
**Labels:** `backend`, `critical`, `automation`, `business-logic`, `multi-type`  
**Assignees:** Backend team  
**Estimated:** 3-4 days  
**Status:** ✅ **COMPLETE** (100%)

**Description:**
Implement automatic Installation System Record creation when an installation bundle is sold. This applies to **all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI). This automates the first step in the "Sale → ISR → Installation → Warranty" pipeline from the PDF.

**Implementation Details:**
- ✅ Django signal handlers in `installation_systems/signals.py`
- ✅ `create_installation_system_record()` - Auto-creates ISR from InstallationRequest
- ✅ `update_installation_system_record_status()` - Status synchronization
- ✅ Installation type detection logic with legacy type mapping
- ✅ Automatic capacity unit assignment based on type
- ✅ Links ISR to Order, Customer, InstallationRequest, Technicians
- ✅ Celery tasks for email notifications
- ✅ Tests for all installation types

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 3 for full details.

---

### Issue #4: Commissioning Checklist Model and API ✅ IMPLEMENTED
**Labels:** `backend`, `high-priority`, `data-model`, `api`, `multi-type`  
**Assignees:** Backend team  
**Estimated:** 3 days  
**Status:** ✅ **COMPLETE** (100%)

**Description:**
Create a digital commissioning checklist system for technicians. **Supports all installation types** with type-specific checklists (Solar, Starlink, Custom Furniture, Hybrid). This enforces the PDF requirement: "A job cannot be marked 'Complete' unless all required fields are submitted."

**Implementation Details:**
- ✅ `CommissioningChecklistTemplate` model with JSON items array
- ✅ `InstallationChecklistEntry` model with completion tracking
- ✅ Type-specific templates (pre_install, installation, commissioning)
- ✅ REST API endpoints for template & entry CRUD
- ✅ **Hard validation:** Cannot commission ISR without 100% checklist completion
- ✅ Completion percentage auto-calculation
- ✅ Photo requirement tracking per checklist item
- ✅ Management command to seed default templates
- ✅ Tests for all installation types

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 4 for full details.

---

### Issue #5: Admin Portal - Installation Systems Management Dashboard 🚧 PARTIAL
**Labels:** `frontend`, `high-priority`, `admin-portal`, `nextjs`, `multi-type`  
**Assignees:** Frontend team  
**Estimated:** 3 days  
**Status:** 🚧 **PARTIAL** (50% - Backend only)

**Description:**
Create an admin dashboard to view and manage all Installation System Records. **Supports all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), Hybrid (SSI). Addresses the "System Control Tower" function from the PDF.

**Implementation Details:**
- ✅ Backend APIs complete at `/crm-api/admin-panel/installation-system-records/`
- ✅ All endpoints: List, detail, update, statistics, report generation
- ✅ Filtering by type, status, classification, customer, order
- ✅ Search functionality ready
- ❌ Next.js pages NOT created
- ❌ Table view UI NOT created
- ❌ Filters UI NOT created
- ❌ Detail view page NOT created

**Remaining Work:**
- Create Next.js pages in `hanna-management-frontend/app/admin/(protected)/installation-systems/`
- Build table view component with filtering
- Build detail view page with status updates

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 5 for full details.

---

### Issue #6: Technician Portal - Commissioning Checklist Mobile UI 🚧 PARTIAL
**Labels:** `frontend`, `high-priority`, `technician-portal`, `nextjs`, `mobile`, `multi-type`  
**Assignees:** Frontend team  
**Estimated:** 3-4 days  
**Status:** 🚧 **PARTIAL** (50% - Backend only)

**Description:**
Create a mobile-friendly commissioning checklist interface for technicians. **Supports all installation types** with type-specific checklists. This addresses the "Execution Layer" requirements: "Step-by-step digital checklists: pre-install, installation, commissioning."

**Implementation Details:**
- ✅ Backend APIs complete at `/api/installation-systems/`
- ✅ Assigned installations endpoint
- ✅ Checklist entry endpoints with item update
- ✅ Photo upload API with multipart support
- ✅ Required photos status validation
- ❌ Next.js pages NOT created
- ❌ Installation list UI NOT created
- ❌ Checklist completion UI NOT created
- ❌ Photo upload interface NOT created
- ❌ Mobile optimization NOT done

**Remaining Work:**
- Create Next.js pages in `hanna-management-frontend/app/technician/(protected)/installations/`
- Build mobile-first checklist completion interface
- Implement camera integration for photo upload

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 6 for full details.

---

### Issue #7: Client Portal - My Installation System Dashboard 🚧 PARTIAL
**Labels:** `frontend`, `medium-priority`, `client-portal`, `nextjs`, `multi-type`  
**Assignees:** Frontend team  
**Estimated:** 3 days  
**Status:** 🚧 **PARTIAL** (50% - Backend only)

**Description:**
Enhance client portal to show complete installation system information linked to their ISR. **Supports all installation types** with type-specific displays. Addresses "Customer Ownership & Self-Service" requirements from the PDF.

**Implementation Details:**
- ✅ Backend API complete at `/api/installation-systems/installation-system-records/my_installations/`
- ✅ Returns only client's own active/commissioned installations
- ✅ Includes all related data (technicians, components, warranties, job cards)
- ✅ Photo gallery API ready
- ✅ Report generation endpoint ready
- ❌ Next.js pages NOT created
- ❌ System info display NOT created
- ❌ Type-specific features NOT implemented
- ❌ Photo gallery UI NOT created
- ❌ Download buttons NOT created

**Remaining Work:**
- Create Next.js pages in `hanna-management-frontend/app/client/(protected)/my-installation/`
- Build installation overview with type-specific displays
- Implement photo gallery component
- Add report download functionality

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 7 for full details.

---

## 📋 How to Use This Document

### For Creating GitHub Issues:

1. Create each issue in GitHub with the **title**, **labels**, and **assignees** listed above
2. Copy the **Description** and **Why Important/Critical** sections into the issue body
3. Copy the **What to Build** section as the acceptance criteria checklist
4. Add **Reference** link to the detailed document
5. Set estimated time in issue
6. Add to "Week 1 Sprint" milestone/project

### For Team Communication:

Share this document with the team and emphasize:
- These 7 issues transform Hanna from a generic CRM into an **Installation Lifecycle Operating System**
- They support **all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), Hybrid (SSI)
- They're scoped to be completable within one week
- They build upon each other (see dependencies in full document)
- Success = Foundation for remote monitoring, predictive maintenance, and scalable operations across all business lines

---

## 🎯 Actual Outcomes (As of January 17, 2026)

### ✅ COMPLETED (Backend)
- ✅ **Installation System Record (ISR)** - Core concept fully operational for all types
- ✅ **Automated Installation Tracking** - No manual record creation (solar, starlink, furniture, hybrid)
- ✅ **Digital Commissioning** - Type-specific quality assurance enforced with hard validation
- ✅ **Foundation for Monitoring** - Remote monitoring ID field ready for integration
- ✅ **Unified Lifecycle Management** - Complete backend across all installation business lines
- ✅ **Photo Evidence System** - Type-specific photo requirements with validation
- ✅ **Installer Payout System** - Complete payout workflow with approval tracking
- ✅ **Branch Management** - Installer assignment and availability tracking

### 🚧 PARTIALLY COMPLETED
- 🚧 **System Bundles** - Solar packages exist, needs generalization for all types
- 🚧 **Admin Visibility** - APIs ready, dashboard UI not started
- 🚧 **Technician Tools** - APIs ready, mobile UI not started
- 🚧 **Client Transparency** - APIs ready, portal pages not started

### ❌ NOT COMPLETED
- ❌ **Frontend Dashboards** - No UI pages created (all APIs ready)

### 📊 Summary
- **Backend:** 95% Complete ✅
- **Frontend:** 0% Complete ❌
- **Overall:** 70% Complete 🚧

**Key Achievement:** Backend infrastructure is production-ready. Primary gap is frontend implementation.

---

## 📚 Supporting Documents

- **Implementation Status:** [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- **Technical Details:** [../architecture/ISR_IMPLEMENTATION_STATUS.md](../architecture/ISR_IMPLEMENTATION_STATUS.md)
- **Backend Documentation:** [../../whatsappcrm_backend/installation_systems/README.md](../../whatsappcrm_backend/installation_systems/README.md)
- **Detailed Issue Specs:** `IMPLEMENTABLE_ISSUES_WEEK1.md`

---

## 🚀 Week 2 Preview (Next Sprint)

### High Priority (Complete Backend Gaps)
1. **Generalize System Bundles** - Replace SolarPackage with SystemBundle supporting all types
2. **Zoho Payout Sync** - Complete the integration stub
3. **Bundle REST APIs** - Create API endpoints for bundle management

### High Priority (Frontend Implementation)
4. **Technician Checklist UI** - Mobile-first checklist completion interface
5. **Admin ISR Dashboard** - List, filter, detail, status update pages
6. **Client Installation View** - Customer-facing installation details

### Medium Priority (Future Features)
7. **Remote Monitoring Integration** - Inverter and Starlink API connections
8. **Automated Warranty Activation** - Trigger on commissioning completion
9. **Retailer Sales Portal** - Bundle selection for retailers
10. **Automated Fault Detection** - Proactive issue identification
11. **Enhanced Analytics** - Installation type breakdown and trends

---

## ❓ Questions or Clarifications?

Refer to:
1. `HANNA_CORE_SCOPE_GAP_ANALYSIS.md` for detailed gap analysis
2. `IMPLEMENTABLE_ISSUES_WEEK1.md` for full acceptance criteria
3. Original PDF for strategic vision

---

**Last Updated:** January 10, 2026  
**Status:** ✅ Ready for Issue Creation  
**Scope:** Multi-type installation support (Solar SSI, Starlink SLI, Custom Furniture CFI, Hybrid SSI)
