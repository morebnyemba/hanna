# Installation Systems App

This Django app implements the **Installation System Record (ISR)** model, which serves as the master object for tracking every installation throughout its lifecycle.

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
   - Customer (ForeignKey to CustomerProfile)
   - Order (ForeignKey to Order, nullable)
   - Technicians (ManyToMany to Technician)
   - Installed Components (ManyToMany to SerializedItem)

### String Representation

The `__str__` method returns a formatted string:
- Solar: `"ISR-12345678 - John Doe - solar - 5kW"`
- Starlink: `"ISR-87654321 - Jane Smith - starlink - 100Mbps"`
- Custom Furniture: `"ISR-11223344 - Bob Jones - custom_furniture - 3units"`

## Admin Interface

The admin interface provides:

- List view with filterable columns (type, status, classification, dates)
- Search by customer name, WhatsApp ID, address, monitoring ID
- Organized fieldsets for data entry
- Horizontal filter for many-to-many relationships
- Date hierarchy by installation_date

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
