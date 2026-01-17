# Suggested GitHub Issues to Align with PDF Scope

**Generated:** 2026-01-09  
**Based on:** Hanna Core Scope and Functionality.pdf  
**Source Analysis:** PROJECT_GAP_ANALYSIS.md

This document provides a comprehensive list of GitHub issues to transform HANNA into a Solar Lifecycle Operating System as outlined in the PDF document.

---

## Quick Summary

**Total Issues:** 20  
**P0 (Critical):** 4 issues - Foundation for solar lifecycle management  
**P1 (High):** 7 issues - Core workflows and portals  
**P2 (Medium):** 5 issues - Enhanced features and integrations  
**P3 (Low):** 4 issues - Future enhancements  

**Estimated Timeline:** 4-5 months with dedicated team  
**Recommended Team:** 2-3 backend + 2 frontend engineers

---

## Priority P0 - Critical Issues (Must Have First)

These 4 issues form the foundation of the Solar Lifecycle Operating System:

### 1. Solar System Record (SSR) Model
**Create the central "anchor" for all solar installations**
- New model: `SolarSystemRecord` with system size, status, monitoring ID
- Link to existing: Order, InstallationRequest, Warranty, SerializedItem
- API endpoints for SSR management
- **Impact:** Foundation for all other features

### 2. Client Portal
**Enable customer self-service**
- View solar systems and status
- Check warranty validity
- Raise fault tickets
- Download certificates/reports
- **Impact:** Reduce support load, increase transparency

### 3. Installation Checklists
**Enforce completion requirements for warranty protection**
- Digital checklists (pre-install, installation, commissioning)
- Photo evidence requirement
- Cannot complete without all items
- **Impact:** Warranty protection, quality assurance

### 4. Remote Monitoring Integration
**Automated fault detection (critical differentiator)**
- Integrate with platforms (Victron, SolarEdge, etc.)
- Auto-detect faults → create tickets
- Customer notifications
- Real-time KPIs in client portal
- **Impact:** Proactive service, reduced emergencies

---

## Priority P1 - High Issues (Should Have Next)

### 5. Solar Package Bundles
**Pre-configured packages with compatibility rules**
- Package management system
- Compatibility validation (battery ↔ inverter ↔ size)
- Restrict digital shop to approved packages

### 6. Order-to-SSR Automation
**Auto-create installation pipeline**
- Order → SSR → Installation → Checklists → Portal access
- Automatic technician assignment
- Customer welcome email

### 7. Enhanced Technician Portal
**Mobile-first field operations**
- Mobile-optimized UI
- Barcode scanning
- Offline support
- Customer signature capture

### 8. Manufacturer Portal
**Data-driven partnership**
- Failure rate analytics
- Warranty claim management
- Repair workflow with scan in/out
- Serial number lookup

### 9. Warranty Approval Workflow
**Admin governance**
- Pending claims queue
- Approve/reject with reasons
- Notifications to all parties

### 10. Role-Based Access Control
**Secure portal separation**
- Granular permissions by role
- Data isolation (clients see only their data)
- Audit logging

### 11. System Component Model
**Link serialized items to systems**
- Track individual components in SSR
- Component-level warranties
- Replacement history

---

## Priority P2 - Medium Issues (Nice to Have)

### 12. Branch Portal
**Regional operations management**

### 13. Retailer Portal Enhancement
**Order submission and tracking**

### 14. Advanced Analytics Dashboard
**Business intelligence**

### 15. Automated Notifications
**Multi-channel customer alerts**

### 16. Zoho Financial Sync
**Accounting integration**

---

## Priority P3 - Low Issues (Future)

### 17. Predictive Maintenance ML
### 18. Native Mobile Apps
### 19. Multi-Currency Support
### 20. AI Service Analysis

---

## Recommended Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
**Goal:** Establish SSR and basic client access
- Issue 1: SSR model
- Issue 11: SystemComponent model
- Issue 2: Basic client portal
- Issue 10: RBAC framework

**Deliverable:** Customers can view their systems online

### Phase 2: Field Operations (Weeks 5-8)
**Goal:** Improve installation quality
- Issue 3: Installation checklists
- Issue 7: Technician portal
- Issue 6: Order automation
- Issue 5: Solar packages

**Deliverable:** Checklists enforced, automated workflows

### Phase 3: Monitoring & Service (Weeks 9-12)
**Goal:** Proactive service capability
- Issue 4: Monitoring integration
- Issue 9: Warranty approvals
- Issue 15: Notifications
- Issue 2: Client portal enhancements

**Deliverable:** Automated fault detection and alerts

### Phase 4: Partner Portals (Weeks 13-16)
**Goal:** Partner engagement
- Issue 8: Manufacturer portal
- Issue 13: Retailer portal
- Issue 12: Branch portal
- Issue 14: Analytics

**Deliverable:** All portals operational

### Phase 5: Optimization (Weeks 17-20)
**Goal:** Integration and efficiency
- Issue 16: Zoho sync
- Performance tuning
- Documentation
- Training

**Deliverable:** Production-ready system

---

## Success Metrics

### Operational KPIs
- **Installation documentation completion:** 100% (from checklist enforcement)
- **Average installation time:** Measure and reduce 20%
- **Warranty claim resolution time:** Measure and reduce 30%
- **Customer support tickets:** Reduce 40% via self-service

### Business KPIs
- **Customer satisfaction score:** Target 4.5/5
- **Repeat business rate:** Track and increase
- **Installer productivity:** Installations per week
- **System uptime (monitoring):** 99.9%

---

## Critical Dependencies

1. **SSR must be created first** - Everything depends on it
2. **Client portal needs SSR** - Can't show systems without SSR
3. **Checklists need SSR** - Link to specific installations
4. **Monitoring needs SSR** - Link monitoring data to systems
5. **All portals need RBAC** - Security framework required

---

## Questions for Stakeholders

Before starting, please clarify:

1. **Monitoring platforms:** Which should we integrate first? (Victron VRM, SolarEdge, Goodwe, etc.)
2. **Package definitions:** What are your standard solar packages? (3kW, 5kW, 6kW configurations)
3. **Checklist content:** What are your current installation checklist steps?
4. **Approval authority:** Who approves warranty claims today?
5. **Financial integration:** Which Zoho modules do you use? (Books, CRM, Inventory)
6. **Priority order:** Do you agree with P0-P3 prioritization?
7. **Rollout strategy:** Pilot with one branch first, or system-wide?
8. **Timeline:** Does 4-5 months align with your goals?

---

## Next Steps

1. **Review this document** with stakeholders
2. **Create GitHub issues** using templates from detailed document
3. **Assign to development team** with Phase 1 priorities
4. **Set up project board** to track progress
5. **Schedule kickoff meeting** to begin Phase 1

---

**For detailed issue descriptions, requirements, and acceptance criteria, see the full document: SUGGESTED_GITHUB_ISSUES.md**
