# Installation Systems App

This Django app implements the **Installation System Record (ISR)** model, which serves as the master object for tracking every installation throughout its lifecycle. This is the implementation of the Solar System Record (SSR) concept from the project requirements, generalized to support all installation types.

## Overview

The ISR generalizes the Solar System Record (SSR) concept from the project documentation to support multiple installation types:

- **Solar (SSI)**: Solar Panel Installations
- **Starlink (SLI)**: Starlink Internet Installations  
- **Custom Furniture (CFI)**: Custom Furniture Installations
- **Hybrid (SSI)**: Combined Starlink + Solar Installations

## Model: InstallationSystemRecord

### Key Features

1. **System Identification**
   - UUID primary key
   - OneToOne link to InstallationRequest
   - Links to CustomerProfile and Order
   - Auto-generated ISR ID (e.g., ISR-12345678)

2. **Installation Details**
   - Installation type (solar, starlink, hybrid, custom_furniture)
   - System size/capacity with flexible units (kW, Mbps, units)
   - System classification (residential, commercial, hybrid)

3. **Status Tracking**
   - Installation status (pending, in_progress, commissioned, active, decommissioned)
   - Installation date
   - Commissioning date

4. **Location & Monitoring**
   - GPS coordinates (latitude, longitude)
   - Installation address
   - Remote monitoring ID

5. **Relationships**
   - **InstallationRequest** (OneToOne): The originating installation request
   - **Customer** (ForeignKey): The customer who owns the installation
   - **Order** (ForeignKey): The sales order associated with the installation
   - **Technicians** (ManyToMany): Assigned technicians
   - **Installed Components** (ManyToMany): SerializedItems in the installation
   - **Warranties** (ManyToMany): Active warranties for the installation
   - **Job Cards** (ManyToMany): Service history and maintenance records

### String Representation

The `__str__` method returns a formatted string:
- Solar: `"ISR-12345678 - John Doe - solar - 5kW"`
- Starlink: `"ISR-87654321 - Jane Smith - starlink - 100Mbps"`
- Custom Furniture: `"ISR-11223344 - Bob Jones - custom_furniture - 3units"`

## API Endpoints

### Admin API

Base URL: `/api/admin/installation-system-records/`

**Authentication Required**: Admin users only (is_staff=True)

#### List & Create
- `GET /api/admin/installation-system-records/` - List all ISRs
- `POST /api/admin/installation-system-records/` - Create new ISR

#### Retrieve, Update, Delete
- `GET /api/admin/installation-system-records/{id}/` - Get ISR details
- `PUT /api/admin/installation-system-records/{id}/` - Update ISR
- `PATCH /api/admin/installation-system-records/{id}/` - Partial update
- `DELETE /api/admin/installation-system-records/{id}/` - Delete ISR

#### Filtering & Search

**Filter by:**
- `?installation_type=solar` - Filter by installation type
- `?installation_status=active` - Filter by status
- `?system_classification=residential` - Filter by classification
- `?customer=<id>` - Filter by customer
- `?order=<id>` - Filter by order

**Search:**
- `?search=john` - Search customer name, address, monitoring ID

**Ordering:**
- `?ordering=-created_at` - Order by field (use `-` for descending)
- Available fields: created_at, installation_date, commissioning_date, system_size, installation_status

#### Custom Actions

**Update Status:**
```
POST /api/admin/installation-system-records/{id}/update_status/
Body: {"status": "active"}
```

**Assign Technician:**
```
POST /api/admin/installation-system-records/{id}/assign_technician/
Body: {"technician_id": 123}
```

**Get Statistics:**
```
GET /api/admin/installation-system-records/statistics/
```
Returns counts by type, status, and classification.

### Client/Technician API

Base URL: `/installation-systems/installation-system-records/`

**Permissions:**
- **Clients**: Read-only access to their own installations
- **Technicians**: View and update assigned installations
- **Admin**: Full access

#### Custom Actions for Users

**My Installations (Client):**
```
GET /installation-systems/installation-system-records/my_installations/
```
Returns only active/commissioned installations for the logged-in customer.

**Assigned Installations (Technician):**
```
GET /installation-systems/installation-system-records/assigned_installations/
```
Returns installations assigned to the logged-in technician.

## Automatic ISR Creation

When an `InstallationRequest` is created, the system automatically creates a corresponding `InstallationSystemRecord` via signal handlers.

### Mapping Logic

| InstallationRequest Field | InstallationSystemRecord Field | Notes |
|---------------------------|-------------------------------|--------|
| customer | customer | Direct mapping |
| associated_order | order | Direct mapping |
| installation_type | installation_type | Converts legacy types |
| address | installation_address | Direct mapping |
| location_latitude | latitude | Prefers new field over legacy |
| location_longitude | longitude | Prefers new field over legacy |
| technicians | technicians | Copied after creation |
| status | installation_status | Mapped via dictionary |

### Status Mapping

| InstallationRequest Status | ISR Status |
|---------------------------|------------|
| pending | pending |
| scheduled | pending |
| in_progress | in_progress |
| completed | commissioned |
| cancelled | decommissioned |

### Legacy Type Handling

Legacy installation types ('residential', 'commercial') are converted:
- Default installation_type: 'solar'
- system_classification: Uses the legacy type value

## Admin Interface

The admin interface provides:

- List view with filterable columns (type, status, classification, dates)
- Search by customer name, WhatsApp ID, address, monitoring ID
- Organized fieldsets for data entry
- Horizontal filter for many-to-many relationships (technicians, components, warranties, job cards)
- Date hierarchy by installation_date
- Autocomplete for customer, order, and installation_request

## Usage

### Creating an Installation Record

```python
from installation_systems.models import InstallationSystemRecord
from customer_data.models import CustomerProfile, Order
from decimal import Decimal

# Create a solar installation record
isr = InstallationSystemRecord.objects.create(
    customer=customer_profile,
    order=order,
    installation_type='solar',
    system_size=Decimal('5.0'),
    capacity_unit='kW',
    system_classification='residential',
    installation_status='pending',
    installation_address='123 Main St, Harare',
    latitude=Decimal('-17.825166'),
    longitude=Decimal('31.033510')
)

# Assign technicians
isr.technicians.add(technician)

# Add installed components
isr.installed_components.add(serialized_item)

# Add warranties
isr.warranties.add(warranty)

# Add job cards
isr.job_cards.add(job_card)
```

### Querying Records

```python
# Get all active solar installations
solar_active = InstallationSystemRecord.objects.filter(
    installation_type='solar',
    installation_status='active'
)

# Get installations for a specific customer
customer_installations = customer_profile.installation_system_records.all()

# Get installations assigned to a technician
tech_installations = technician.installation_system_records.all()

# Get installation with all relationships
isr = InstallationSystemRecord.objects.select_related(
    'customer', 'order', 'installation_request'
).prefetch_related(
    'technicians', 'installed_components', 'warranties', 'job_cards'
).get(id=isr_id)
```

## Migrations

To create migrations after model changes:

```bash
docker compose exec backend python manage.py makemigrations installation_systems
docker compose exec backend python manage.py migrate
```

Or use the provided script:

```bash
./run-migrations.sh
```

## Testing

Run tests for this app:

```bash
docker compose exec backend python manage.py test installation_systems
```

The test suite includes:
- Model creation tests for all installation types
- Relationship tests (customer, order, technicians, components)
- String representation tests
- Field validation tests
- Default value tests

## Future Enhancements

Potential additions to consider:

1. **Lifecycle Management**
   - Maintenance schedules
   - Service history tracking
   - Component replacement tracking

2. **Performance Monitoring**
   - Energy production data (for solar)
   - Bandwidth utilization (for starlink)
   - System health metrics

3. **Documentation**
   - Installation photos
   - System diagrams
   - Commissioning certificates

4. **Notifications**
   - Maintenance reminders
   - Warranty expiration alerts
   - System performance alerts

---

# Commissioning Checklist System

## Overview

The Digital Commissioning Checklist System provides a structured way to track installation progress through three phases: Pre-Installation, Installation, and Commissioning. This ensures quality control and prevents installations from being marked as complete without proper verification.

## Models

### CommissioningChecklistTemplate

Defines the structure and requirements for a checklist.

**Key Fields:**
- `name`: Template name (e.g., "Solar Pre-Installation Checklist")
- `checklist_type`: Type of checklist (`pre_install`, `installation`, `commissioning`)
- `installation_type`: Optional - restrict to specific installation type (`solar`, `starlink`, `hybrid`, `custom_furniture`)
- `items`: JSON array of checklist items
- `is_active`: Whether the template is currently active

**Item Structure:**
```json
{
  "id": "unique_item_id",
  "title": "Item Title",
  "description": "Detailed description",
  "required": true,
  "requires_photo": true,
  "photo_count": 2,
  "notes_required": false
}
```

### InstallationChecklistEntry

Tracks completion of a checklist for a specific installation.

**Key Fields:**
- `installation_record`: Link to InstallationSystemRecord
- `template`: Link to CommissioningChecklistTemplate
- `technician`: Technician who completed the checklist
- `completed_items`: JSON object tracking completion of each item
- `completion_status`: Overall status (`not_started`, `in_progress`, `completed`)
- `completion_percentage`: Calculated percentage (0-100)

**Completed Item Structure:**
```json
{
  "item_id": {
    "completed": true,
    "completed_at": "2024-01-15T10:30:00Z",
    "notes": "Additional notes",
    "photos": ["media_uuid_1", "media_uuid_2"],
    "completed_by": "user_id"
  }
}
```

## Validation Rules

### Hard Control
An installation **cannot** be marked as `COMMISSIONED` or `ACTIVE` unless:
1. All checklist entries linked to the installation are 100% complete
2. All required items in each checklist have been completed
3. If no checklists exist, the installation can be commissioned (allows flexibility)

### Validation Error
If attempting to commission an incomplete installation:
```
ValidationError: Cannot mark installation as Commissioned until all checklists 
are 100% complete. Incomplete checklists: Solar Installation Checklist (75%)
```

## API Endpoints

### Checklist Templates

**List Templates**
```
GET /api/admin/checklist-templates/
```

**Create Template**
```
POST /api/admin/checklist-templates/
{
  "name": "Custom Checklist",
  "checklist_type": "installation",
  "installation_type": "solar",
  "description": "Description",
  "items": [...],
  "is_active": true
}
```

**Duplicate Template**
```
POST /api/admin/checklist-templates/{id}/duplicate/
```

### Checklist Entries

**List Entries**
```
GET /api/admin/checklist-entries/
```

**Create Entry**
```
POST /api/admin/checklist-entries/
{
  "installation_record": "uuid",
  "template": "uuid",
  "technician": "technician_id"
}
```

**Update Item**
```
POST /api/admin/checklist-entries/{id}/update_item/
{
  "item_id": "item_1",
  "completed": true,
  "notes": "Item completed successfully",
  "photos": ["media_uuid_1"]
}
```

**Get Checklist Status**
```
GET /api/admin/checklist-entries/{id}/checklist_status/
```

**Get Checklists by Installation**
```
GET /api/admin/checklist-entries/by_installation/?installation_id=uuid
```

## Management Commands

### Seed Default Templates

Creates default checklist templates for Solar and Starlink installations:

```bash
python manage.py seed_checklist_templates
# Or with Docker:
docker compose exec backend python manage.py seed_checklist_templates
```

This creates:
- Solar Pre-Installation Checklist (5 items)
- Solar Installation Checklist (6 items)
- Solar Commissioning Checklist (6 items)
- Starlink Pre-Installation Checklist (4 items)
- Starlink Installation Checklist (4 items)
- Starlink Commissioning Checklist (4 items)
- General Pre-Installation Checklist (3 items)

## Usage Flow

### 1. Admin Creates Templates
Admin uses Django admin or API to create/edit checklist templates.

### 2. Technician Assignment
When an installation is assigned to a technician:
1. Create `InstallationChecklistEntry` records for each applicable template
2. Link entries to the `InstallationSystemRecord`
3. Assign the technician

### 3. Field Work
Technician completes checklist items:
1. For each item, mark as completed
2. Add required photos
3. Add notes if required
4. System automatically calculates completion percentage

### 4. Validation
When attempting to commission the installation:
1. System checks all checklist entries
2. Validates 100% completion of required items
3. Either allows commissioning or returns validation error

## Model Methods

### InstallationChecklistEntry

**`calculate_completion_percentage()`**
Returns completion percentage based on required items.

**`update_completion_status()`**
Updates status and timestamps based on completion percentage.

**`is_fully_completed()`**
Returns True if all required items are completed.

### InstallationSystemRecord

**`are_all_checklists_complete()`**
Returns tuple: (all_complete: bool, incomplete_checklists: list)

**`clean()`**
Validates installation status changes.

## Testing

Run tests:
```bash
python manage.py test installation_systems
# Or with Docker:
docker compose exec backend python manage.py test installation_systems
```

Test coverage includes:
- Model creation and relationships
- Completion percentage calculation
- Status updates
- Validation logic preventing premature commissioning
- API endpoints (basic)

## Security

- Only admin users can manage templates
- Technicians can only update their assigned checklists
- All changes are logged with timestamps and user IDs
- Photos stored securely with UUID references

## Implementation Status vs HANNA Core Scope

### ✅ Fully Implemented (Backend)
- **InstallationSystemRecord Model** - Master object for all installation types
- **CommissioningChecklistTemplate & Entry** - Digital checklists with validation
- **InstallationPhoto** - Photo evidence with type-specific requirements
- **PayoutConfiguration & InstallerPayout** - Complete payout workflow
- **Branch Models** - InstallerAssignment & InstallerAvailability
- **Comprehensive APIs** - Full REST API with permissions
- **Automatic Workflows** - Signal-based ISR creation, status sync
- **Hard Validation** - Cannot commission without complete checklists & photos

### 🚧 Partially Implemented
- **System Bundles** - SolarPackage exists but not generalized for all types
  - Missing: Generic SystemBundle model for starlink/furniture/hybrid
  - Missing: REST API endpoints for bundle management
- **Zoho Payout Sync** - Stub exists in tasks.py but not fully implemented

### ❌ Not Implemented (Frontend)
- **Admin Dashboard** - ISR management UI (APIs ready, pages missing)
- **Technician Portal** - Mobile checklist UI (APIs ready, pages missing)
- **Client Portal** - My Installation view (APIs ready, pages missing)

### 📊 Overall Status
- **Backend:** 95% Complete ✅
- **Frontend:** 0% Complete ❌
- **Overall:** 70% Complete 🚧

**For detailed implementation status, see:** 
- [docs/architecture/ISR_IMPLEMENTATION_STATUS.md](../../docs/architecture/ISR_IMPLEMENTATION_STATUS.md)
- [docs/planning/IMPLEMENTATION_STATUS.md](../../docs/planning/IMPLEMENTATION_STATUS.md)

---

## Future Enhancements for Checklist System

1. **Offline Support**: PWA with local storage for field work
2. **Photo Analysis**: AI-powered quality checks on uploaded photos
3. **GPS Verification**: Ensure technician is on-site
4. **Time Tracking**: Track time spent on each item
5. **Customer Sign-off**: Digital signature capture
6. **Reporting**: Generate PDF completion reports
7. **Notifications**: Alert admins of checklist completion
8. **Templates per Customer**: Custom checklists for VIP customers

## Next Steps

### High Priority
1. **Frontend Implementation** - Build Admin/Technician/Client dashboards using existing APIs
2. **Generalize System Bundles** - Create SystemBundle model supporting all installation types
3. **Complete Zoho Integration** - Implement payout sync with Zoho Books

### Medium Priority
4. **Remote Monitoring Integration** - Connect to inverter/Starlink APIs
5. **Automated Fault Detection** - Proactive issue identification from monitoring data

### Low Priority
6. **Mobile App** - Native app alternative for technicians
7. **AI Photo Validation** - Automated photo quality checks
8. **GPS Verification** - Ensure on-site presence
