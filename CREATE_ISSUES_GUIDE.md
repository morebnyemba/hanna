# GitHub Issues Creation Guide

This document provides instructions and automation scripts for creating GitHub issues from the documented specifications in this repository.

## Overview

Based on the comprehensive gap analysis and implementation planning documents in this repository, we have prepared **7 critical GitHub issues** for Week 1 Sprint. These issues transform HANNA into an Installation Lifecycle Operating System supporting multiple installation types: Solar (SSI), Starlink (SLI), Custom Furniture (CFI), and Hybrid (SSI).

## Source Documents

The issues are based on the following planning documents:
- `GITHUB_ISSUES_TO_CREATE.md` - Quick reference for 7 Week 1 Sprint issues
- `GITHUB_ISSUES_READY_TO_CREATE.md` - 12 comprehensive issues for solar lifecycle management
- `IMPLEMENTABLE_ISSUES_WEEK1.md` - Detailed specifications for 7 focused Week 1 issues
- `IMPLEMENTABLE_ISSUES_LIST.md` - 12 week-sized implementable issues

## Created Artifacts

### 1. `issues_to_create.json`
A structured JSON file containing all 7 issues with:
- Title
- Labels
- Body (markdown formatted with acceptance criteria)
- Milestone
- Assignees
- Copilot assignment flag

### 2. `create_github_issues.py`
A Python script that uses GitHub CLI (`gh`) to create all issues programmatically.

### 3. `CREATE_ISSUES_GUIDE.md` (this file)
Comprehensive guide for creating and managing the issues.

## Prerequisites

To create the issues, you need:
1. **GitHub CLI (`gh`)** installed and authenticated
2. **Write access** to the `morebnyemba/hanna` repository
3. **Python 3.x** (for running the automation script)

## Method 1: Automated Creation with Python Script

### Step 1: Ensure GitHub CLI is authenticated

```bash
# Check if gh is authenticated
gh auth status

# If not authenticated, login
gh auth login
```

### Step 2: Run the Python script

```bash
# Make the script executable
chmod +x create_github_issues.py

# Run the script
./create_github_issues.py
```

The script will:
- Create all 7 issues in the repository
- Apply the appropriate labels
- Set the milestone to "Week 1 Sprint"
- Output the URL for each created issue

### Step 3: Assign GitHub Copilot to each issue

After issues are created, assign GitHub Copilot:

```bash
# For each issue URL output by the script, assign Copilot
# Replace <issue-number> with the actual issue number

gh issue edit <issue-number> --repo morebnyemba/hanna --add-assignee "@copilot"
```

Or use this one-liner to assign Copilot to all recent issues:

```bash
# Get the last 7 issues and assign Copilot to each
for issue in $(gh issue list --repo morebnyemba/hanna --limit 7 --json number --jq '.[].number'); do
  gh issue edit $issue --repo morebnyemba/hanna --add-assignee "@copilot"
done
```

## Method 2: Manual Creation via GitHub Web Interface

If you prefer manual creation or don't have CLI access:

### For Each Issue:

1. Go to https://github.com/morebnyemba/hanna/issues/new
2. Copy the title from `issues_to_create.json`
3. Copy the body markdown from `issues_to_create.json`
4. Add labels: Click "Labels" and add the ones specified in the JSON
5. Set milestone: Click "Milestone" and select or create "Week 1 Sprint"
6. Click "Submit new issue"
7. On the created issue page, click the gear icon next to "Assignees"
8. Type "@copilot" and select GitHub Copilot from the dropdown

## Method 3: Using GitHub API with curl

For automation in CI/CD pipelines:

```bash
#!/bin/bash

REPO="morebnyemba/hanna"
GITHUB_TOKEN="your_token_here"

# Read the JSON file and create issues
cat issues_to_create.json | jq -c '.[]' | while read issue; do
  TITLE=$(echo $issue | jq -r '.title')
  BODY=$(echo $issue | jq -r '.body')
  LABELS=$(echo $issue | jq -r '.labels | join(",")')
  
  # Create the issue
  RESPONSE=$(curl -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/repos/$REPO/issues \
    -d "{
      \"title\": \"$TITLE\",
      \"body\": \"$BODY\",
      \"labels\": [$(echo $issue | jq -r '.labels | map("\"" + . + "\"") | join(",")')]
    }")
  
  ISSUE_NUMBER=$(echo $RESPONSE | jq -r '.number')
  echo "Created issue #$ISSUE_NUMBER: $TITLE"
  
  # Assign Copilot
  curl -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/repos/$REPO/issues/$ISSUE_NUMBER/assignees \
    -d '{"assignees": ["copilot"]}'
done
```

## Issue Labels to Create

Before creating issues, ensure these labels exist in your repository:

```bash
# Create labels if they don't exist
gh label create "backend" --color "0E8A16" --repo morebnyemba/hanna --force
gh label create "frontend" --color "1D76DB" --repo morebnyemba/hanna --force
gh label create "critical" --color "D93F0B" --repo morebnyemba/hanna --force
gh label create "high-priority" --color "FF9900" --repo morebnyemba/hanna --force
gh label create "medium-priority" --color "FFCC00" --repo morebnyemba/hanna --force
gh label create "data-model" --color "5319E7" --repo morebnyemba/hanna --force
gh label create "api" --color "0075CA" --repo morebnyemba/hanna --force
gh label create "multi-type" --color "006B75" --repo morebnyemba/hanna --force
gh label create "automation" --color "C2E0C6" --repo morebnyemba/hanna --force
gh label create "business-logic" --color "BFD4F2" --repo morebnyemba/hanna --force
gh label create "admin-portal" --color "D4C5F9" --repo morebnyemba/hanna --force
gh label create "client-portal" --color "FEF2C0" --repo morebnyemba/hanna --force
gh label create "technician-portal" --color "C5DEF5" --repo morebnyemba/hanna --force
gh label create "nextjs" --color "000000" --repo morebnyemba/hanna --force
gh label create "mobile" --color "FFA500" --repo morebnyemba/hanna --force
```

## The 7 Issues to Create

### Week 1 Sprint Issues:

1. **Create Installation System Record (ISR) Model Foundation** (Critical)
   - Backend, Data Model, Multi-type
   - 3-4 days
   
2. **Add System Bundles / Installation Packages Model** (High Priority)
   - Backend, Data Model, API, Multi-type
   - 2-3 days
   
3. **Automated ISR Creation on Installation Product Sale** (Critical)
   - Backend, Automation, Business Logic, Multi-type
   - 3-4 days
   
4. **Commissioning Checklist Model and API** (High Priority)
   - Backend, Data Model, API, Multi-type
   - 3 days
   
5. **Admin Portal - Installation Systems Management Dashboard** (High Priority)
   - Frontend, Admin Portal, Next.js, Multi-type
   - 3 days
   
6. **Technician Portal - Commissioning Checklist Mobile UI** (High Priority)
   - Frontend, Technician Portal, Next.js, Mobile, Multi-type
   - 3-4 days
   
7. **Client Portal - My Installation System Dashboard** (Medium Priority)
   - Frontend, Client Portal, Next.js, Multi-type
   - 3 days

## Expected Outcomes

After creating and completing these 7 issues:

✅ **Installation System Record (ISR)** - Core concept operational for all types  
✅ **Automated Installation Tracking** - No manual record creation (solar, starlink, furniture, hybrid)  
✅ **Digital Commissioning** - Type-specific quality assurance enforced  
✅ **Admin Visibility** - All installation systems tracked centrally with type filtering  
✅ **Technician Tools** - Field execution made easy with appropriate checklists  
✅ **Client Transparency** - Installation ownership visible with type-specific displays  
✅ **Foundation for Monitoring** - Ready for Week 2 integration (solar/starlink)  
✅ **Unified Lifecycle Management** - Across all installation business lines (SSI, SLI, CFI)

## Dependencies

The issues have the following dependencies:
- Issue 3 depends on Issue 1 (ISR model must exist)
- Issue 4 depends on Issue 1 (Checklist links to ISR)
- Issue 5 depends on Issue 1 (Admin views ISRs)
- Issue 6 depends on Issue 4 (Technician completes checklist)
- Issue 7 depends on Issue 1 (Client views their ISR)

## Implementation Order

For maximum impact within the week:

### Days 1-2: Backend Foundation
- Issue 1: ISR Model (Critical) - Supports all installation types
- Issue 2: System Bundles (can be parallel) - Supports all installation types

### Days 3-4: Automation & Business Logic
- Issue 3: Automated ISR Creation - Handles solar, starlink, furniture, hybrid
- Issue 4: Commissioning Checklist - Type-specific templates

### Days 5-7: Frontend Portals
- Issue 5: Admin ISR Dashboard - View all installation types
- Issue 6: Technician Checklist UI - Type-specific checklists
- Issue 7: Client Installation System View - Type-specific displays

## Troubleshooting

### "gh: command not found"
Install GitHub CLI: https://cli.github.com/

### "Error: Authentication required"
Run `gh auth login` and follow the prompts

### "Error: Label does not exist"
Run the label creation commands from the "Issue Labels to Create" section above

### "Error: Milestone not found"
Create the milestone first:
```bash
gh api repos/morebnyemba/hanna/milestones -X POST -f title="Week 1 Sprint" -f state="open"
```

## Support Documents

For detailed implementation specifications, refer to:
- `IMPLEMENTABLE_ISSUES_WEEK1.md` - Full technical specifications
- `HANNA_CORE_SCOPE_GAP_ANALYSIS.md` - Gap analysis and strategic vision
- `GITHUB_ISSUES_TO_CREATE.md` - Quick reference guide

## Next Steps After Issue Creation

1. **Assign issues** to appropriate team members or GitHub Copilot
2. **Set up project board** to track progress
3. **Schedule kickoff meeting** to review issues and timeline
4. **Begin implementation** following the recommended order
5. **Regular check-ins** to ensure Week 1 Sprint stays on track

## Contact

For questions or clarifications about these issues, please refer to the detailed documentation in the repository or contact the project maintainers.

---

**Last Updated:** January 11, 2026  
**Status:** ✅ Ready for Issue Creation  
**Scope:** Multi-type installation support (Solar SSI, Starlink SLI, Custom Furniture CFI, Hybrid SSI)
