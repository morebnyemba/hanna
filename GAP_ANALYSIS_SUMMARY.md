# HANNA Gap Analysis Summary

**Date:** January 9, 2026  
**Reference:** Hanna Core Scope and Functionality PDF  

## Executive Summary

HANNA has a **strong foundation** with all 6 portals implemented (Admin, Client, Manufacturer, Technician, Retailer, Retailer Branch) and solid backend infrastructure. However, it lacks the unifying **Solar System Record (SSR)** concept that the PDF emphasizes as critical for a true "Solar Lifecycle Operating System."

## Critical Finding

**Missing Solar System Record (SSR)** - The PDF states: "All portals should orbit a single master object: Solar System Record (SSR)." Currently, installation data is fragmented across multiple models without a unified digital file per installation.

## Portal Status Summary

| Portal | Implementation Status | Key Gaps |
|--------|----------------------|----------|
| **Admin** | ✅ Mostly Complete | Installer payouts, warranty rule config, SLA thresholds |
| **Client** | ✅ Complete | Certificate downloads, installation report downloads |
| **Manufacturer** | ✅ Well Implemented | Minor (firmware updates, fault code library) |
| **Technician** | ⚠️ Significant Gaps | Digital checklists, photo upload, serial capture, completion validation |
| **Retailer** | ⚠️ Major Gaps | Solar package sales, order submission, installation tracking |
| **Retailer Branch** | ⚠️ Moderate Gaps | Installer allocation, performance metrics |

## Top 5 Priority Gaps

1. **No Solar System Record (SSR)** - Missing central anchor for all installation data
2. **No Digital Commissioning Checklists** - Technicians lack structured installation workflow
3. **No Photo Upload System** - Cannot document installations with evidence
4. **Retailer Portal Underdeveloped** - Cannot sell solar packages or track orders
5. **No Remote Monitoring Integration** - Cannot detect faults automatically

## Recommended GitHub Issues (12 Total)

All scoped to **1 week or less** as requested:

### Critical Priority (Must Do First)
1. **Create Solar System Record (SSR) Model** - 7 days - Foundation for everything else

### High Priority (Core Operations)
2. **Digital Commissioning Checklist System** - 7 days - Technician workflow
3. **Installation Photo Upload** - 5 days - Documentation evidence
4. **Serial Number Capture & Validation** - 5 days - Equipment tracking
5. **Certificate & Report Generation** - 7 days - Client transparency
6. **Retailer Solar Package Sales Interface** - 7 days - Sales expansion

### Medium Priority (Enhancement)
7. **Retailer Installation Tracking** - 5 days - Visibility
8. **Installer Payout Approval System** - 7 days - Financial workflow
9. **Warranty Rules & SLA Configuration** - 5 days - Automation
10. **Remote Monitoring Integration (Victron)** - 7 days - Fault detection
12. **Auto SSR Creation on Purchase** - 5 days - E-commerce integration

### Low Priority (Optimization)
11. **Branch Performance Metrics** - 7 days - Analytics

**Total: 12 issues = ~74 days effort** (can be parallelized to ~7-10 weeks with multiple developers)

## Implementation Order

```
Week 1-2:   Issue #1 (SSR Foundation)
Week 3-5:   Issues #2, #3, #4 (Technician Portal) - Can parallelize
Week 6:     Issue #5 (Certificates)
Week 7-8:   Issues #6, #7 (Retailer Portal)
Week 9-10:  Issues #8, #9 (Admin Enhancements)
Week 11-12: Issues #10, #12 (Monitoring & Automation)
Week 13:    Issue #11 (Branch Metrics)
```

## Key Architectural Change Needed

The PDF envisions this data flow:
```
Digital Shop/Retailer Sale
    ↓
Solar System Record Created (SSR) ← MISSING
    ↓
Technician Assigned
    ↓
Installation & Commissioning (with checklists) ← MISSING
    ↓
Warranty Activated ← EXISTS
    ↓
Remote Monitoring Linked ← MISSING
    ↓
Ongoing Service & Upsell ← PARTIAL
```

## What's Working Well

✅ All 6 portals exist with login and basic dashboards  
✅ Warranty system is well-implemented  
✅ Manufacturer portal has excellent job card tracking  
✅ Product and customer models are comprehensive  
✅ Strong integration foundation (Zoho, Meta, Paynow)  
✅ Barcode scanning exists in manufacturer and branch portals  

## What Needs Work

❌ No unified SSR linking entire installation lifecycle  
❌ Technician portal lacks structured installation workflow  
❌ No photo documentation system  
❌ Retailer portal can't sell or track orders effectively  
❌ No monitoring platform integration  
❌ Missing PDF generation for certificates/reports  
❌ No installer payout workflow  
❌ No automated fault detection  

## Detailed Documentation

For complete analysis and full issue descriptions, see:
- **PROJECT_GAP_ANALYSIS_DETAILED.md** - Complete portal-by-portal analysis
- **IMPLEMENTABLE_ISSUES_LIST.md** - Full issue descriptions with acceptance criteria

## Alignment with PDF Vision

The PDF positions HANNA as a **Solar Lifecycle Operating System** managing:
- Sales → Installation → Warranty → Monitoring → Service → Repeat Business

Current HANNA has pieces of this vision but lacks:
1. The unifying SSR concept
2. Structured installation workflow (checklists)
3. Documentation evidence (photos)
4. Automated monitoring integration
5. Complete retailer sales capability

These 12 issues directly address these gaps and align HANNA with the PDF's vision.
