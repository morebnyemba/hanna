#!/bin/bash

# Script to create GitHub issues for HANNA Installation System transformation
# Based on GITHUB_ISSUES_TO_CREATE.md and IMPLEMENTABLE_ISSUES_WEEK1.md

set -e

REPO="morebnyemba/hanna"
MILESTONE="Week 1 Sprint"

echo "=================================================="
echo "Creating GitHub Issues for HANNA"
echo "Repository: $REPO"
echo "=================================================="
echo ""

# Check if gh CLI is authenticated
if ! gh auth status &>/dev/null; then
    echo "❌ Error: GitHub CLI is not authenticated"
    echo "Please run: gh auth login"
    exit 1
fi

echo "✓ GitHub CLI authenticated"
echo ""

# Create labels if they don't exist
echo "Creating labels..."
gh label create "backend" --color "0E8A16" --repo $REPO --force 2>/dev/null || true
gh label create "frontend" --color "1D76DB" --repo $REPO --force 2>/dev/null || true
gh label create "critical" --color "D93F0B" --repo $REPO --force 2>/dev/null || true
gh label create "high-priority" --color "FF9900" --repo $REPO --force 2>/dev/null || true
gh label create "medium-priority" --color "FFCC00" --repo $REPO --force 2>/dev/null || true
gh label create "data-model" --color "5319E7" --repo $REPO --force 2>/dev/null || true
gh label create "api" --color "0075CA" --repo $REPO --force 2>/dev/null || true
gh label create "multi-type" --color "006B75" --repo $REPO --force 2>/dev/null || true
gh label create "automation" --color "C2E0C6" --repo $REPO --force 2>/dev/null || true
gh label create "business-logic" --color "BFD4F2" --repo $REPO --force 2>/dev/null || true
gh label create "admin-portal" --color "D4C5F9" --repo $REPO --force 2>/dev/null || true
gh label create "client-portal" --color "FEF2C0" --repo $REPO --force 2>/dev/null || true
gh label create "technician-portal" --color "C5DEF5" --repo $REPO --force 2>/dev/null || true
gh label create "nextjs" --color "000000" --repo $REPO --force 2>/dev/null || true
gh label create "mobile" --color "FFA500" --repo $REPO --force 2>/dev/null || true
echo "✓ Labels created/verified"
echo ""

# Array to store created issue numbers
declare -a ISSUE_NUMBERS

# Issue 1: Create Installation System Record (ISR) Model Foundation
echo "Creating Issue 1: Create Installation System Record (ISR) Model Foundation"
ISSUE_URL=$(gh issue create --repo $REPO \
  --title "Create Installation System Record (ISR) Model Foundation" \
  --label "backend,critical,data-model,multi-type" \
  --body "## Description
Create the foundational \`InstallationSystemRecord\` model that serves as the master object for tracking every installation throughout its lifecycle. Supports **all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI). This is THE core concept from the PDF that's currently missing.

## Why Critical
Without ISR, we cannot achieve the strategic vision of an Installation Lifecycle Operating System. Every sale, installation, warranty, and service event should orbit around an ISR, regardless of installation type.

## What to Build
- New Django app: \`installation_systems\`
- \`InstallationSystemRecord\` model with:
  - Installation type field (solar, starlink, custom_furniture, hybrid)
  - Fields for customer, order, system size/capacity, status, technicians, components, monitoring ID
  - Flexible capacity units (kW for solar, Mbps for starlink, units for furniture)
- Database migrations
- Admin interface
- Tests for all installation types

## Acceptance Criteria
- [ ] Create \`InstallationSystemRecord\` model in new Django app \`installation_systems\`
- [ ] Include installation type field (choices: solar, starlink, custom_furniture, hybrid)
- [ ] Add system capacity with flexible units (kW, Mbps, units)
- [ ] Create relationships to existing models (Order, Customer, InstallationRequest, SerializedItem, etc.)
- [ ] Create database migrations
- [ ] Add Django admin interface
- [ ] Create REST API endpoints (CRUD)
- [ ] Add role-based permissions
- [ ] Write unit tests for all installation types

## Reference
See \`IMPLEMENTABLE_ISSUES_WEEK1.md\` Issue 1 for full details.

## Estimated Time
3-4 days")
echo "✓ Created: $ISSUE_URL"
ISSUE_NUMBERS+=($(echo $ISSUE_URL | grep -oE '[0-9]+$'))
echo ""

# Issue 2: Add System Bundles / Installation Packages Model
echo "Creating Issue 2: Add System Bundles / Installation Packages Model"
ISSUE_URL=$(gh issue create --repo $REPO \
  --title "Add System Bundles / Installation Packages Model" \
  --label "backend,high-priority,data-model,api,multi-type" \
  --body "## Description
Create models and APIs for pre-configured installation packages for **all installation types**: Solar packages (e.g., \"3kW Residential Kit\"), Starlink packages (e.g., \"Starlink Business Kit\"), Custom Furniture packages (e.g., \"Office Furniture Set\"), and Hybrid packages. This enables controlled offerings where retailers sell only approved bundles.

## Why Important
The PDF emphasizes retailers should \"sell only pre-approved system bundles to avoid undersizing risks.\" This provides standardization and quality control across all installation types.

## What to Build
- \`SystemBundle\` model with installation_type field (name, capacity, price, components, type)
- \`BundleComponent\` model (links products to bundles)
- Type-specific compatibility validation rules (solar: inverter+battery+panel, starlink: router+dish, etc.)
- REST API endpoints for bundles with installation type filtering
- Tests for all types

## Acceptance Criteria
- [ ] Create \`SystemBundle\` model with installation_type field
- [ ] Create \`BundleComponent\` model
- [ ] Add compatibility validation rules for each installation type
- [ ] Create REST API endpoints (list, filter, get, validate)
- [ ] Add serializers with nested bundle components
- [ ] Write API tests for all installation types

## Reference
See \`IMPLEMENTABLE_ISSUES_WEEK1.md\` Issue 2 for full details.

## Estimated Time
2-3 days")
echo "✓ Created: $ISSUE_URL"
ISSUE_NUMBERS+=($(echo $ISSUE_URL | grep -oE '[0-9]+$'))
echo ""

# Issue 3: Automated ISR Creation on Installation Product Sale
echo "Creating Issue 3: Automated ISR Creation on Installation Product Sale"
ISSUE_URL=$(gh issue create --repo $REPO \
  --title "Automated ISR Creation on Installation Product Sale" \
  --label "backend,critical,automation,business-logic,multi-type" \
  --body "## Description
Implement automatic Installation System Record creation when an installation bundle is sold. This applies to **all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI). This automates the first step in the \"Sale → ISR → Installation → Warranty\" pipeline from the PDF.

## Why Critical
The PDF states: \"Every sale = an ISR is created instantly.\" This eliminates manual steps and ensures no installation goes untracked, regardless of type.

## What to Build
- Django signal handler on Order model
- Installation type detection logic (from product keywords, bundles, categories)
- Celery task for async ISR creation (all types)
- Link ISR to Order, Customer, InstallationRequest
- Extend email invoice processor to create ISR
- Notification to admin when ISR created (specify type)
- Management command to backfill existing orders (all types)
- Tests for solar, starlink, furniture, hybrid

## Acceptance Criteria
- [ ] Create Django signal handler for Order model
- [ ] Implement installation type detection logic
- [ ] Create Celery task for async ISR creation
- [ ] Extend email invoice processor in \`email_integration/tasks.py\`
- [ ] Add ISR field to InstallationRequest
- [ ] Send admin notifications on ISR creation
- [ ] Create management command to backfill existing orders
- [ ] Write integration tests for all installation types

## Reference
See \`IMPLEMENTABLE_ISSUES_WEEK1.md\` Issue 3 for full details.

## Estimated Time
3-4 days")
echo "✓ Created: $ISSUE_URL"
ISSUE_NUMBERS+=($(echo $ISSUE_URL | grep -oE '[0-9]+$'))
echo ""

# Issue 4: Commissioning Checklist Model and API
echo "Creating Issue 4: Commissioning Checklist Model and API"
ISSUE_URL=$(gh issue create --repo $REPO \
  --title "Commissioning Checklist Model and API" \
  --label "backend,high-priority,data-model,api,multi-type" \
  --body "## Description
Create a digital commissioning checklist system for technicians. **Supports all installation types** with type-specific checklists (Solar, Starlink, Custom Furniture, Hybrid). This enforces the PDF requirement: \"A job cannot be marked 'Complete' unless all required fields are submitted.\"

## Why Important
Digital checklists protect warranties, limit liability, and ensure quality. The PDF emphasizes \"hard control\" - no shortcuts allowed.

## What to Build
- \`CommissioningChecklist\` model linked to ISR
- \`ChecklistItem\` model with categories, completion tracking, photo upload
- **Type-specific predefined checklist templates** (solar: inverter/battery checks, starlink: network tests, furniture: assembly verification)
- REST API for checklist CRUD
- Validation preventing ISR commissioning without 100% completion
- Tests for all installation types

## Acceptance Criteria
- [ ] Create \`CommissioningChecklist\` model
- [ ] Create \`ChecklistItem\` model
- [ ] Create predefined templates for each installation type (solar, starlink, furniture, hybrid)
- [ ] Create REST API endpoints for checklist operations
- [ ] Add validation to prevent commissioning without completion
- [ ] Write tests for all installation types

## Checklist Templates
**Solar**: Site assessment, panel mounting, electrical connections, inverter config, battery test, performance test, training, photos, serial numbers

**Starlink**: Site assessment, dish mounting, router installation, cable routing, connectivity test, speed test, training, photos, serial numbers

**Custom Furniture**: Site assessment, assembly verification, placement confirmation, hardware check, finish inspection, acceptance signature, photos, serial numbers

**Hybrid**: Combination of solar and starlink checklists

## Reference
See \`IMPLEMENTABLE_ISSUES_WEEK1.md\` Issue 4 for full details.

## Estimated Time
3 days")
echo "✓ Created: $ISSUE_URL"
ISSUE_NUMBERS+=($(echo $ISSUE_URL | grep -oE '[0-9]+$'))
echo ""

# Issue 5: Admin Portal - Installation Systems Management Dashboard
echo "Creating Issue 5: Admin Portal - Installation Systems Management Dashboard"
ISSUE_URL=$(gh issue create --repo $REPO \
  --title "Admin Portal - Installation Systems Management Dashboard" \
  --label "frontend,high-priority,admin-portal,nextjs,multi-type" \
  --body "## Description
Create an admin dashboard to view and manage all Installation System Records. **Supports all installation types**: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), Hybrid (SSI). Addresses the \"System Control Tower\" function from the PDF.

## Why Important
Admins need visibility into all installations across all types with filtering by installation type. This provides the governance layer for the entire installation lifecycle business.

## What to Build
- Next.js page: \`/admin/(protected)/installation-systems/\`
- Table view with ISR ID, customer, **installation type**, size, status, technician
- Filters (installation type, status, date range, technician)
- Search functionality
- Detail view page
- Responsive design
- Color-coded type badges
- Navigation menu integration

## Acceptance Criteria
- [ ] Create page \`/admin/(protected)/installation-systems/page.tsx\`
- [ ] Display table with all ISR columns
- [ ] Implement filters (installation type, status, date, technician)
- [ ] Add search functionality (ISR ID, customer name)
- [ ] Add pagination (30 items per page)
- [ ] Create ISR detail view page
- [ ] Add to navigation menu
- [ ] Implement responsive design
- [ ] Add color-coded installation type badges
- [ ] Add loading states and error handling

## Reference
See \`IMPLEMENTABLE_ISSUES_WEEK1.md\` Issue 5 for full details.

## Estimated Time
3 days")
echo "✓ Created: $ISSUE_URL"
ISSUE_NUMBERS+=($(echo $ISSUE_URL | grep -oE '[0-9]+$'))
echo ""

# Issue 6: Technician Portal - Commissioning Checklist Mobile UI
echo "Creating Issue 6: Technician Portal - Commissioning Checklist Mobile UI"
ISSUE_URL=$(gh issue create --repo $REPO \
  --title "Technician Portal - Commissioning Checklist Mobile UI" \
  --label "frontend,high-priority,technician-portal,nextjs,mobile,multi-type" \
  --body "## Description
Create a mobile-friendly commissioning checklist interface for technicians. **Supports all installation types** with type-specific checklists. This addresses the \"Execution Layer\" requirements: \"Step-by-step digital checklists: pre-install, installation, commissioning.\"

## Why Important
The PDF emphasizes field data capture with photo upload, serial numbers, and test results. This tool empowers technicians and ensures quality across all installation types.

## What to Build
- Next.js page: \`/technician/(protected)/installations/\`
- Installation list with type badges
- Checklist view with grouping (varies by type: pre-install, installation, testing, docs)
- Checkbox, notes, photo upload per item
- Progress indicator
- Cannot complete installation without all required items
- Mobile-optimized (large touch targets, camera integration)
- Different checklists load based on installation type

## Acceptance Criteria
- [ ] Create page \`/technician/(protected)/installations/page.tsx\`
- [ ] List assigned installations with type badges
- [ ] Create checklist page \`/technician/(protected)/installations/{isr_id}/checklist/page.tsx\`
- [ ] Display installation type with appropriate icon
- [ ] Show checklist grouped by category (type-specific)
- [ ] Add checkbox, notes, and photo upload for each item
- [ ] Implement visual progress indicator
- [ ] Prevent completion without all required items checked
- [ ] Optimize for mobile (large touch targets)
- [ ] Integrate device camera for photo capture
- [ ] Load appropriate checklist based on installation type

## Reference
See \`IMPLEMENTABLE_ISSUES_WEEK1.md\` Issue 6 for full details.

## Estimated Time
3-4 days")
echo "✓ Created: $ISSUE_URL"
ISSUE_NUMBERS+=($(echo $ISSUE_URL | grep -oE '[0-9]+$'))
echo ""

# Issue 7: Client Portal - My Installation System Dashboard
echo "Creating Issue 7: Client Portal - My Installation System Dashboard"
ISSUE_URL=$(gh issue create --repo $REPO \
  --title "Client Portal - My Installation System Dashboard" \
  --label "frontend,medium-priority,client-portal,nextjs,multi-type" \
  --body "## Description
Enhance client portal to show complete installation system information linked to their ISR. **Supports all installation types** with type-specific displays. Addresses \"Customer Ownership & Self-Service\" requirements from the PDF.

## Why Important
The PDF states clients should \"View installed system details, warranty validity, monitoring status\" and \"Download warranty certificates, installation reports.\" This builds trust and reduces support calls.

## What to Build
- Next.js page: \`/client/(protected)/my-installation/\`
- Display system info with **installation type badge and icon**
- Type-specific features (solar: monitoring, starlink: speed test, furniture: maintenance tips)
- Installation photos gallery
- Download buttons (installation report, warranty certificate)
- \"Report Issue\" button to create JobCard
- Service history
- Link to monitoring dashboard (for solar/starlink)

## Acceptance Criteria
- [ ] Create page \`/client/(protected)/my-installation/page.tsx\`
- [ ] Display installation info with type badge
- [ ] Show system capacity with appropriate unit
- [ ] List installed components with serial numbers
- [ ] Display warranty status per component
- [ ] Add installation photos gallery
- [ ] Implement type-specific features (solar: monitoring, starlink: speed test, furniture: maintenance)
- [ ] Add \"Download Installation Report\" button
- [ ] Add \"Download Warranty Certificate\" button
- [ ] Add \"Report Issue\" button (creates JobCard)
- [ ] Show service history
- [ ] Link to monitoring dashboard (for solar/starlink)
- [ ] Implement responsive design

## Reference
See \`IMPLEMENTABLE_ISSUES_WEEK1.md\` Issue 7 for full details.

## Estimated Time
3 days")
echo "✓ Created: $ISSUE_URL"
ISSUE_NUMBERS+=($(echo $ISSUE_URL | grep -oE '[0-9]+$'))
echo ""

echo "=================================================="
echo "Summary: Created 7 issues"
echo "=================================================="
echo ""
echo "Issue numbers: ${ISSUE_NUMBERS[@]}"
echo ""
echo "Next step: Assign GitHub Copilot to each issue"
echo ""
echo "Run the following commands to assign Copilot:"
echo ""
for issue_num in "${ISSUE_NUMBERS[@]}"; do
  echo "gh issue edit $issue_num --repo $REPO --add-assignee '@copilot'"
done
echo ""
echo "Or run this one-liner to assign all at once:"
echo "for issue in ${ISSUE_NUMBERS[@]}; do gh issue edit \$issue --repo $REPO --add-assignee '@copilot'; done"
echo ""
echo "=================================================="
echo "✓ Done!"
echo "=================================================="
