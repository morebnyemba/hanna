# HANNA System: Current State vs Desired State

## Current State (Fragmented Data Model)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Customer        │────▶│ Installation     │     │ Warranty        │
│ Profile         │     │ Request          │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                          │
                               │                          │
                               ▼                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │ Technician       │     │ SerializedItem  │
                        │ Assignment       │     │                 │
                        └──────────────────┘     └─────────────────┘
                                                          │
                                                          │
                        ┌──────────────────┐             │
                        │ JobCard          │◀────────────┘
                        │ (Service)        │
                        └──────────────────┘

❌ No central hub linking lifecycle
❌ No photo documentation
❌ No checklists
❌ No monitoring integration
```

## Desired State (SSR-Centric Model per PDF)

```
                    ┌───────────────────────────────────────┐
                    │  SOLAR SYSTEM RECORD (SSR)            │
                    │  The Anchor - Unique Digital File     │
                    │  ─────────────────────────────────    │
                    │  • Installation ID                    │
                    │  • System Size (3kW/5kW/6kW/8kW)      │
                    │  • Customer Profile                   │
                    │  • Associated Order                   │
                    │  • Lifecycle Status                   │
                    └───────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────────┐       ┌──────────────┐
│ Equipment    │          │ Installation      │       │ Warranty     │
│ Serial #s    │          │ ─────────────     │       │ Records      │
│              │          │ • Technicians     │       │              │
│ • Panels     │          │ • Checklists ✅   │       │ • Active     │
│ • Inverter   │          │ • Photos ✅       │       │ • Claims     │
│ • Batteries  │          │ • Completion ✅   │       │              │
└──────────────┘          └──────────────────┘       └──────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────────┐       ┌──────────────┐
│ Remote       │          │ Service          │       │ Reports &    │
│ Monitoring   │          │ History          │       │ Certificates │
│              │          │                  │       │              │
│ • Victron ID │          │ • Job Cards      │       │ • Warranty   │
│ • Alerts ✅  │          │ • Technician     │       │ • Install    │
│ • Auto-Fault │          │   Comments       │       │ • PDF Gen ✅ │
└──────────────┘          └──────────────────┘       └──────────────┘

✅ Central SSR hub
✅ Complete documentation
✅ Automated workflows
✅ Role-based access to SSR
```

## Data Flow: Current vs Desired

### Current Flow (Disconnected)
```
Digital Shop Sale
    ↓
Order Created
    ↓
❌ Manual step: Admin creates Installation Request
    ↓
❌ Manual step: Technician assigned
    ↓
❌ No checklist - just mark complete
    ↓
❌ Manual step: Create warranty separately
    ↓
❌ No monitoring link
    ↓
Service requests handled separately
```

### Desired Flow (Automated & Connected)
```
Digital Shop Sale / Retailer Order
    ↓
✅ SSR Auto-Created
    ↓
✅ Installation Request Auto-Generated
    ↓
✅ Technician Assigned (Manual or Auto)
    ↓
✅ Digital Checklists (Pre, Install, Commission)
    ↓
✅ Photos & Serial Numbers Required
    ↓
✅ Cannot Complete Without Evidence
    ↓
✅ Warranty Auto-Activated
    ↓
✅ Remote Monitoring Linked
    ↓
✅ Auto-Fault Detection & Ticket Creation
    ↓
✅ Service History Logged to SSR
    ↓
Ongoing Upsell & Retention
```

## Portal Access to SSR

```
┌────────────────────────────────────────────────────────┐
│                  SOLAR SYSTEM RECORD                   │
│              (All Portals Interact Here)               │
└────────────────────────────────────────────────────────┘
         │          │          │          │          │
         ▼          ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │ Admin  │ │ Client │ │Technic.│ │ Manuf. │ │Retailer│
    │        │ │        │ │        │ │        │ │        │
    │ FULL   │ │READ OWN│ │UPDATE  │ │ READ   │ │ READ   │
    │ACCESS  │ │  ONLY  │ │INSTALL │ │WARRANTY│ │ ORDERS │
    └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2) - CRITICAL
```
┌──────────────────────────────────────────────┐
│ Issue #1: Create Solar System Record Model  │
│ ──────────────────────────────────────────── │
│ • New SolarSystemInstallation model          │
│ • Links all existing models                  │
│ • API endpoints                              │
│ • Admin interface                            │
│ • Role-based permissions                     │
└──────────────────────────────────────────────┘
         │
         └─▶ Enables all other issues
```

### Phase 2: Technician Enablement (Weeks 3-5)
```
Issue #2: Checklists ────┐
Issue #3: Photos ────────┤─▶ Complete Installation Workflow
Issue #4: Serial Numbers ┘
```

### Phase 3: Client Transparency (Week 6)
```
Issue #5: Certificates & Reports ─▶ Client Portal Enhancement
```

### Phase 4: Sales Expansion (Weeks 7-8)
```
Issue #6: Retailer Sales ────┐
Issue #7: Install Tracking ──┘─▶ Retailer Portal Complete
```

### Phase 5: Admin & Financial (Weeks 9-10)
```
Issue #8: Payouts ───────┐
Issue #9: Warranty Rules ┘─▶ Admin Governance Enhanced
```

### Phase 6: Automation (Weeks 11-12)
```
Issue #10: Monitoring ───┐
Issue #12: Auto SSR ─────┘─▶ Automated Lifecycle
```

### Phase 7: Analytics (Week 13)
```
Issue #11: Branch Metrics ─▶ Performance Insights
```

## Gap Priority Matrix

```
                    IMPACT
                    
    HIGH    │ Issue #1 SSR      │ Issues #2,3,4   │
            │ (Foundation)      │ (Technician)    │
            ├──────────────────┼─────────────────┤
            │ Issue #6 Retailer│ Issue #5 Certs  │
    MEDIUM  │ Sales             │ Issue #10 Mon.  │
            ├──────────────────┼─────────────────┤
            │ Issue #8 Payouts │ Issue #11 Branch│
    LOW     │ Issue #9 SLA     │ Issue #12 Auto  │
            │                   │                 │
            └──────────────────┴─────────────────┘
              URGENT           IMPORTANT
                   URGENCY
```

## Success Metrics (Post-Implementation)

### Operational Efficiency
- ✅ 100% of installations documented with photos
- ✅ 100% of installations completed with checklists
- ✅ 0% undocumented installations
- ✅ <24hr response time to monitoring alerts
- ✅ 50% reduction in warranty disputes (proper documentation)

### Business Growth
- ✅ Retailer network can independently sell and track
- ✅ Automated SSR creation reduces admin overhead
- ✅ Client portal transparency increases retention
- ✅ Predictive maintenance reduces emergency calls

### Data Quality
- ✅ Single source of truth (SSR) for all installation data
- ✅ Complete equipment serial number tracking
- ✅ Auditable installation process
- ✅ Evidence-backed warranty claims

## Alignment with PDF Vision

The PDF positions HANNA as a **"Solar Lifecycle Operating System"** with these goals:

1. ✅ **Faster sales conversion** → Retailer sales interface (Issue #6)
2. ✅ **Controlled, auditable installations** → Checklists + Photos (Issues #2, #3)
3. ✅ **Reduced warranty risk** → Documentation + Serial tracking (Issues #3, #4)
4. ✅ **Long-term retention & upselling** → Monitoring + Client portal (Issues #5, #10)

All 12 issues directly support these four core objectives.

## Key Takeaway

**HANNA has excellent infrastructure but lacks the unifying SSR concept.**

The 12 proposed issues transform HANNA from:
- A collection of independent systems
- Into a cohesive Solar Lifecycle Operating System

Issue #1 (SSR) is the **critical foundation** - implement it first.
