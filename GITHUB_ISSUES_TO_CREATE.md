# Quick Reference: Issues to Create for Solar Transformation

This document provides a quick reference for the **7 GitHub issues** that should be created to align Hanna with the Solar Lifecycle Operating System vision from the PDF.

---

## ✅ Ready to Create - Week 1 Sprint

### Issue #1: Create Solar System Record (SSR) Model Foundation
**Labels:** `backend`, `critical`, `data-model`  
**Assignees:** Backend team  
**Estimated:** 3-4 days

**Description:**
Create the foundational `SolarSystemRecord` model that serves as the master object for tracking every solar installation throughout its lifecycle. This is THE core concept from the PDF that's currently missing.

**Why Critical:**
Without SSR, we cannot achieve the strategic vision of a Solar Lifecycle Operating System. Every sale, installation, warranty, and service event should orbit around an SSR.

**What to Build:**
- New Django app: `solar_installations`
- `SolarSystemRecord` model with fields for customer, order, system size, status, technicians, components, monitoring ID
- Database migrations
- Admin interface
- Tests

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 1 for full details.

---

### Issue #2: Add System Bundles / Solar Packages Model
**Labels:** `backend`, `high-priority`, `data-model`, `api`  
**Assignees:** Backend team  
**Estimated:** 2-3 days

**Description:**
Create models and APIs for pre-configured solar packages (e.g., "3kW Residential Kit", "5kW Commercial System"). This enables controlled offerings where retailers sell only approved bundles.

**Why Important:**
The PDF emphasizes retailers should "sell only pre-approved system bundles to avoid undersizing risks." This provides standardization and quality control.

**What to Build:**
- `SystemBundle` model (name, capacity, price, components)
- `BundleComponent` model (links products to bundles)
- Compatibility validation rules
- REST API endpoints for bundles
- Tests

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 2 for full details.

---

### Issue #3: Automated SSR Creation on Solar Product Sale
**Labels:** `backend`, `critical`, `automation`, `business-logic`  
**Assignees:** Backend team  
**Estimated:** 3-4 days

**Description:**
Implement automatic Solar System Record creation when a solar bundle is sold. This automates the first step in the "Sale → SSR → Installation → Warranty" pipeline from the PDF.

**Why Critical:**
The PDF states: "Every sale = an SSR is created instantly." This eliminates manual steps and ensures no installation goes untracked.

**What to Build:**
- Django signal handler on Order model
- Celery task for async SSR creation
- Link SSR to Order, Customer, InstallationRequest
- Notification to admin when SSR created
- Management command to backfill existing orders
- Tests

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 3 for full details.

---

### Issue #4: Commissioning Checklist Model and API
**Labels:** `backend`, `high-priority`, `data-model`, `api`  
**Assignees:** Backend team  
**Estimated:** 3 days

**Description:**
Create a digital commissioning checklist system for technicians. This enforces the PDF requirement: "A job cannot be marked 'Complete' unless all required fields are submitted."

**Why Important:**
Digital checklists protect warranties, limit liability, and ensure quality. The PDF emphasizes "hard control" - no shortcuts allowed.

**What to Build:**
- `CommissioningChecklist` model linked to SSR
- `ChecklistItem` model with categories, completion tracking, photo upload
- Predefined checklist templates
- REST API for checklist CRUD
- Validation preventing SSR commissioning without 100% completion
- Tests

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 4 for full details.

---

### Issue #5: Admin Portal - SSR Management Dashboard
**Labels:** `frontend`, `high-priority`, `admin-portal`, `nextjs`  
**Assignees:** Frontend team  
**Estimated:** 3 days

**Description:**
Create an admin dashboard to view and manage all Solar System Records with filtering, search, and status tracking. Addresses the "System Control Tower" function from the PDF.

**Why Important:**
Admins need visibility into "total installs, active warranties, fault rates" as stated in the PDF. This provides the governance layer.

**What to Build:**
- Next.js page: `/admin/(protected)/solar-systems/`
- Table view with SSR ID, customer, size, status, technician
- Filters (status, date range, technician)
- Search functionality
- Detail view page
- Responsive design
- Navigation menu integration

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 5 for full details.

---

### Issue #6: Technician Portal - Commissioning Checklist Mobile UI
**Labels:** `frontend`, `high-priority`, `technician-portal`, `nextjs`, `mobile`  
**Assignees:** Frontend team  
**Estimated:** 3-4 days

**Description:**
Create a mobile-friendly commissioning checklist interface for technicians. This addresses the "Execution Layer" requirements: "Step-by-step digital checklists: pre-install, installation, commissioning."

**Why Important:**
The PDF emphasizes field data capture with photo upload, serial numbers, and test results. This tool empowers technicians and ensures quality.

**What to Build:**
- Next.js page: `/technician/(protected)/installations/`
- Checklist view with grouping (pre-install, installation, testing, docs)
- Checkbox, notes, photo upload per item
- Progress indicator
- Cannot complete installation without all required items
- Mobile-optimized (large touch targets, camera integration)

**Reference:** See `IMPLEMENTABLE_ISSUES_WEEK1.md` Issue 6 for full details.

---

### Issue #7: Client Portal - My Solar System Dashboard
**Labels:** `frontend`, `medium-priority`, `client-portal`, `nextjs`  
**Assignees:** Frontend team  
**Estimated:** 3 days

**Description:**
Enhance client portal to show complete solar system information linked to their SSR. Addresses "Customer Ownership & Self-Service" requirements from the PDF.

**Why Important:**
The PDF states clients should "View installed system details, warranty validity, monitoring status" and "Download warranty certificates, installation reports." This builds trust and reduces support calls.

**What to Build:**
- Next.js page: `/client/(protected)/my-system/`
- Display system capacity, installation date, components, warranties
- Installation photos gallery
- Download buttons (installation report, warranty certificate)
- "Report Issue" button to create JobCard
- Service history
- Link to monitoring dashboard

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
- These 7 issues transform Hanna from a generic CRM into a **Solar Lifecycle Operating System**
- They're scoped to be completable within one week
- They build upon each other (see dependencies in full document)
- Success = Foundation for remote monitoring, predictive maintenance, and scalable operations

---

## 🎯 Expected Outcomes After Week 1

By completing these 7 issues:

✅ **Solar System Record (SSR)** - Core concept operational  
✅ **Automated Installation Tracking** - No manual record creation  
✅ **Digital Commissioning** - Quality assurance enforced  
✅ **Admin Visibility** - All solar systems tracked centrally  
✅ **Technician Tools** - Field execution made easy  
✅ **Client Transparency** - System ownership visible  
✅ **Foundation for Monitoring** - Ready for Week 2 integration  

---

## 📚 Supporting Documents

- **Full Gap Analysis:** `HANNA_CORE_SCOPE_GAP_ANALYSIS.md`
- **Detailed Issue Specs:** `IMPLEMENTABLE_ISSUES_WEEK1.md`
- **Original PDF Vision:** "Hanna Core Scope and Functionality.pdf"

---

## 🚀 Week 2 Preview (Next Sprint)

After Week 1 foundation is complete:
- **Issue #8:** Remote monitoring integration framework
- **Issue #9:** Automated warranty activation on commissioning
- **Issue #10:** Retailer sales portal for solar bundles
- **Issue #11:** Automated fault ticket creation from monitoring
- **Issue #12:** Enhanced fault analytics dashboard

---

## ❓ Questions or Clarifications?

Refer to:
1. `HANNA_CORE_SCOPE_GAP_ANALYSIS.md` for detailed gap analysis
2. `IMPLEMENTABLE_ISSUES_WEEK1.md` for full acceptance criteria
3. Original PDF for strategic vision

---

**Last Updated:** January 9, 2026  
**Status:** ✅ Ready for Issue Creation
