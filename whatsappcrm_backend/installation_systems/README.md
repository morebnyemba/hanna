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
