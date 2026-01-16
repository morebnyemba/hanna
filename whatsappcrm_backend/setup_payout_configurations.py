#!/usr/bin/env python
"""
Initial Payout Configuration Setup Script
Creates default payout configurations for the installer payout system.

Usage:
    python setup_payout_configurations.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
django.setup()

from decimal import Decimal
from installation_systems.models import PayoutConfiguration


def create_default_configurations():
    """Create default payout configurations for each installation type."""
    
    print("Creating default payout configurations...")
    print("=" * 60)
    
    configurations = [
        # Solar installations - tiered by system size
        {
            'name': 'Solar Small System (0-5kW)',
            'installation_type': 'solar',
            'capacity_unit': 'kW',
            'min_system_size': Decimal('0'),
            'max_system_size': Decimal('5.0'),
            'rate_type': 'per_unit',
            'rate_amount': Decimal('60.00'),  # $60 per kW
            'is_active': True,
            'priority': 1,
        },
        {
            'name': 'Solar Medium System (5-15kW)',
            'installation_type': 'solar',
            'capacity_unit': 'kW',
            'min_system_size': Decimal('5.0'),
            'max_system_size': Decimal('15.0'),
            'rate_type': 'per_unit',
            'rate_amount': Decimal('50.00'),  # $50 per kW
            'is_active': True,
            'priority': 2,
        },
        {
            'name': 'Solar Large System (15kW+)',
            'installation_type': 'solar',
            'capacity_unit': 'kW',
            'min_system_size': Decimal('15.0'),
            'max_system_size': None,
            'rate_type': 'per_unit',
            'rate_amount': Decimal('45.00'),  # $45 per kW for large systems
            'is_active': True,
            'priority': 3,
        },
        
        # Starlink installations - flat rate
        {
            'name': 'Starlink Installation',
            'installation_type': 'starlink',
            'capacity_unit': 'units',
            'min_system_size': None,
            'max_system_size': None,
            'rate_type': 'flat',
            'rate_amount': Decimal('100.00'),  # $100 per installation
            'is_active': True,
            'priority': 1,
        },
        
        # Hybrid installations - flat rate
        {
            'name': 'Hybrid Solar + Starlink',
            'installation_type': 'hybrid',
            'capacity_unit': 'units',
            'min_system_size': None,
            'max_system_size': None,
            'rate_type': 'flat',
            'rate_amount': Decimal('150.00'),  # $150 per hybrid installation
            'is_active': True,
            'priority': 1,
        },
        
        # Custom furniture - flat rate
        {
            'name': 'Custom Furniture Installation',
            'installation_type': 'custom_furniture',
            'capacity_unit': 'units',
            'min_system_size': None,
            'max_system_size': None,
            'rate_type': 'flat',
            'rate_amount': Decimal('75.00'),  # $75 per furniture installation
            'is_active': True,
            'priority': 1,
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for config_data in configurations:
        # Check if configuration with same name already exists
        existing = PayoutConfiguration.objects.filter(name=config_data['name']).first()
        
        if existing:
            print(f"⏭  Skipped: {config_data['name']} (already exists)")
            skipped_count += 1
            continue
        
        # Create configuration
        config = PayoutConfiguration.objects.create(**config_data)
        print(f"✓  Created: {config.name} - ${config.rate_amount} ({config.get_rate_type_display()})")
        created_count += 1
    
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total:   {created_count + skipped_count}")
    
    if created_count > 0:
        print("\n✓ Default payout configurations created successfully!")
        print("\nYou can now:")
        print("1. View configurations in Django admin")
        print("2. Adjust rates via API: /api/admin/payout-configurations/")
        print("3. Create payouts for completed installations")
    else:
        print("\n⚠ No new configurations created (all already exist)")


def display_existing_configurations():
    """Display all existing payout configurations."""
    
    print("\nExisting Payout Configurations:")
    print("=" * 60)
    
    configs = PayoutConfiguration.objects.all().order_by('-priority', 'installation_type', 'min_system_size')
    
    if not configs.exists():
        print("No configurations found.")
        return
    
    for config in configs:
        status = "✓ Active" if config.is_active else "✗ Inactive"
        size_range = ""
        if config.min_system_size or config.max_system_size:
            min_val = f"{config.min_system_size}" if config.min_system_size else "0"
            max_val = f"{config.max_system_size}" if config.max_system_size else "∞"
            size_range = f" ({min_val}-{max_val}{config.capacity_unit})"
        
        print(f"{status} | {config.name}{size_range}")
        print(f"         Type: {config.get_installation_type_display() if config.installation_type else 'All'}")
        print(f"         Rate: ${config.rate_amount} ({config.get_rate_type_display()})")
        print(f"         Priority: {config.priority}")
        print()


def main():
    """Main execution function."""
    
    print("\n" + "=" * 60)
    print("Installer Payout Configuration Setup")
    print("=" * 60 + "\n")
    
    try:
        # Display existing configurations
        display_existing_configurations()
        
        # Ask user if they want to create defaults
        response = input("\nCreate default configurations? (y/n): ").strip().lower()
        
        if response == 'y':
            create_default_configurations()
        else:
            print("\nSetup cancelled.")
        
        print("\n" + "=" * 60)
        print("Setup complete!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
