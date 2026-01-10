# Quick Reference: Issues to Create for Installation System Transformation

This document provides a quick reference for the **7 GitHub issues** that should be created to align Hanna with the Installation Lifecycle Operating System vision from the PDF. **Supports multiple installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid Solar+Starlink (SSI).

---

## ✅ Ready to Create - Week 1 Sprint

### Issue #1: Create Installation System Record (ISR) Model Foundation
**Labels:** `backend`, `critical`, `data-model`, `multi-type`  
**Assignees:** Backend team  
**Estimated:** 3-4 days

**Description:**
Create the foundational `InstallationSystemRecord` model that serves as the master object for tracking every installation throughout its lifecycle. Supports **all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI). This is THE core concept from the PDF that's currently missing.

**Why Critical:**
Without ISR, we cannot achieve the strategic vision of an Installation Lifecycle Operating System. Every sale, installation, warranty, and service event should orbit around an ISR, regardless of installation type.

**What to Build:**
- New Django app: `installation_systems`
- `InstallationSystemRecord` model with:
  - Installation type field (solar, starlink, custom_furniture, hybrid)
  - Fields for customer, order, system size/capacity, status, technicians, components, monitoring ID
  - Flexible capacity units (kW for solar, Mbps for starlink, units for furniture)
- Database migrations
- Admin interface
- Tests for all installation types

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 1 for full details.

---

### Issue #2: Add System Bundles / Installation Packages Model
**Labels:** `backend`, `high-priority`, `data-model`, `api`, `multi-type`  
**Assignees:** Backend team  
**Estimated:** 2-3 days

**Description:**
Create models and APIs for pre-configured installation packages for **all installation types**: Solar packages (e.g., "3kW Residential Kit"), Starlink packages (e.g., "Starlink Business Kit"), Custom Furniture packages (e.g., "Office Furniture Set"), and Hybrid packages. This enables controlled offerings where retailers sell only approved bundles.

**Why Important:**
The PDF emphasizes retailers should "sell only pre-approved system bundles to avoid undersizing risks." This provides standardization and quality control across all installation types.

**What to Build:**
- `SystemBundle` model with installation_type field (name, capacity, price, components, type)
- `BundleComponent` model (links products to bundles)
- Type-specific compatibility validation rules (solar: inverter+battery+panel, starlink: router+dish, etc.)
- REST API endpoints for bundles with installation type filtering
- Tests for all types

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 2 for full details.

---

### Issue #3: Automated ISR Creation on Installation Product Sale
**Labels:** `backend`, `critical`, `automation`, `business-logic`, `multi-type`  
**Assignees:** Backend team  
**Estimated:** 3-4 days

**Description:**
Implement automatic Installation System Record creation when an installation bundle is sold. This applies to **all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI). This automates the first step in the "Sale → ISR → Installation → Warranty" pipeline from the PDF.

**Why Critical:**
The PDF states: "Every sale = an ISR is created instantly." This eliminates manual steps and ensures no installation goes untracked, regardless of type.

**What to Build:**
- Django signal handler on Order model
- Installation type detection logic (from product keywords, bundles, categories)
- Celery task for async ISR creation (all types)
- Link ISR to Order, Customer, InstallationRequest
- Extend email invoice processor to create ISR
- Notification to admin when ISR created (specify type)
- Management command to backfill existing orders (all types)
- Tests for solar, starlink, furniture, hybrid

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 3 for full details.

---

### Issue #4: Commissioning Checklist Model and API
**Labels:** `backend`, `high-priority`, `data-model`, `api`, `multi-type`  
**Assignees:** Backend team  
**Estimated:** 3 days

**Description:**
Create a digital commissioning checklist system for technicians. **Supports all installation types** with type-specific checklists (Solar, Starlink, Custom Furniture, Hybrid). This enforces the PDF requirement: "A job cannot be marked 'Complete' unless all required fields are submitted."

**Why Important:**
Digital checklists protect warranties, limit liability, and ensure quality. The PDF emphasizes "hard control" - no shortcuts allowed.

**What to Build:**
- `CommissioningChecklist` model linked to ISR
- `ChecklistItem` model with categories, completion tracking, photo upload
- **Type-specific predefined checklist templates** (solar: inverter/battery checks, starlink: network tests, furniture: assembly verification)
- REST API for checklist CRUD
- Validation preventing ISR commissioning without 100% completion
- Tests for all installation types

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 4 for full details.

---

### Issue #5: Admin Portal - Installation Systems Management Dashboard
**Labels:** `frontend`, `high-priority`, `admin-portal`, `nextjs`, `multi-type`  
**Assignees:** Frontend team  
**Estimated:** 3 days

**Description:**
Create an admin dashboard to view and manage all Installation System Records. **Supports all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), Hybrid (SSI). Addresses the "System Control Tower" function from the PDF.

**Why Important:**
Admins need visibility into all installations across all types with filtering by installation type. This provides the governance layer for the entire installation lifecycle business.

**What to Build:**
- Next.js page: `/admin/(protected)/installation-systems/`
- Table view with ISR ID, customer, **installation type**, size, status, technician
- Filters (installation type, status, date range, technician)
- Search functionality
- Detail view page
- Responsive design
- Color-coded type badges
- Navigation menu integration

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 5 for full details.

---

### Issue #6: Technician Portal - Commissioning Checklist Mobile UI
**Labels:** `frontend`, `high-priority`, `technician-portal`, `nextjs`, `mobile`, `multi-type`  
**Assignees:** Frontend team  
**Estimated:** 3-4 days

**Description:**
Create a mobile-friendly commissioning checklist interface for technicians. **Supports all installation types** with type-specific checklists. This addresses the "Execution Layer" requirements: "Step-by-step digital checklists: pre-install, installation, commissioning."

**Why Important:**
The PDF emphasizes field data capture with photo upload, serial numbers, and test results. This tool empowers technicians and ensures quality across all installation types.

**What to Build:**
- Next.js page: `/technician/(protected)/installations/`
- Installation list with type badges
- Checklist view with grouping (varies by type: pre-install, installation, testing, docs)
- Checkbox, notes, photo upload per item
- Progress indicator
- Cannot complete installation without all required items
- Mobile-optimized (large touch targets, camera integration)
- Different checklists load based on installation type

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 6 for full details.

---

### Issue #7: Client Portal - My Installation System Dashboard
**Labels:** `frontend`, `medium-priority`, `client-portal`, `nextjs`, `multi-type`  
**Assignees:** Frontend team  
**Estimated:** 3 days

**Description:**
Enhance client portal to show complete installation system information linked to their ISR. **Supports all installation types** with type-specific displays. Addresses "Customer Ownership & Self-Service" requirements from the PDF.

**Why Important:**
The PDF states clients should "View installed system details, warranty validity, monitoring status" and "Download warranty certificates, installation reports." This builds trust and reduces support calls.

**What to Build:**
- Next.js page: `/client/(protected)/my-installation/`
- Display system info with **installation type badge and icon**
- Type-specific features (solar: monitoring, starlink: speed test, furniture: maintenance tips)
- Installation photos gallery
- Download buttons (installation report, warranty certificate)
- "Report Issue" button to create JobCard
- Service history
- Link to monitoring dashboard (for solar/starlink)

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

## 🎯 Expected Outcomes After Week 1

By completing these 7 issues:

✅ **Installation System Record (ISR)** - Core concept operational for all types  
✅ **Automated Installation Tracking** - No manual record creation (solar, starlink, furniture, hybrid)  
✅ **Digital Commissioning** - Type-specific quality assurance enforced  
✅ **Admin Visibility** - All installation systems tracked centrally with type filtering  
✅ **Technician Tools** - Field execution made easy with appropriate checklists  
✅ **Client Transparency** - Installation ownership visible with type-specific displays  
✅ **Foundation for Monitoring** - Ready for Week 2 integration (solar/starlink)  
✅ **Unified Lifecycle Management** - Across all installation business lines (SSI, SLI, CFI)

---

## 📚 Supporting Documents

- **Full Gap Analysis:** `HANNA_CORE_SCOPE_GAP_ANALYSIS.md`
- **Detailed Issue Specs:** `IMPLEMENTABLE_ISSUES_WEEK1.md`
- **Original PDF Vision:** "Hanna Core Scope and Functionality.pdf"

---

## 🚀 Week 2 Preview (Next Sprint)

After Week 1 foundation is complete:
- **Issue #8:** Remote monitoring integration framework (solar and starlink)
- **Issue #9:** Automated warranty activation on commissioning (all types)
- **Issue #10:** Retailer sales portal for installation bundles (all types)
- **Issue #11:** Automated fault ticket creation from monitoring
- **Issue #12:** Enhanced analytics dashboard by installation type

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
