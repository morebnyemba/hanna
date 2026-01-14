"""
Management command to seed default checklist templates.
Usage: python manage.py seed_checklist_templates
"""

from django.core.management.base import BaseCommand
from installation_systems.models import CommissioningChecklistTemplate


class Command(BaseCommand):
    help = 'Seed default commissioning checklist templates'

    def handle(self, *args, **options):
        self.stdout.write('Seeding checklist templates...')

        templates = [
            {
                'name': 'Solar Pre-Installation Checklist',
                'checklist_type': 'pre_install',
                'installation_type': 'solar',
                'description': 'Pre-installation checklist for solar panel installations',
                'items': [
                    {
                        'id': 'site_access',
                        'title': 'Site Access Verification',
                        'description': 'Verify vehicle can access installation site with all equipment',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': False
                    },
                    {
                        'id': 'roof_condition',
                        'title': 'Roof Condition Assessment',
                        'description': 'Assess roof structural integrity and suitability for solar panels',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 4,
                        'notes_required': True
                    },
                    {
                        'id': 'electrical_panel',
                        'title': 'Electrical Panel Inspection',
                        'description': 'Inspect main electrical panel and verify capacity',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': True
                    },
                    {
                        'id': 'mounting_location',
                        'title': 'Panel Mounting Location Confirmation',
                        'description': 'Confirm optimal panel placement with customer',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 3,
                        'notes_required': True
                    },
                    {
                        'id': 'shading_analysis',
                        'title': 'Shading Analysis',
                        'description': 'Document any potential shading issues throughout the day',
                        'required': True,
                        'requires_photo': False,
                        'photo_count': 0,
                        'notes_required': True
                    },
                ],
                'is_active': True
            },
            {
                'name': 'Solar Installation Checklist',
                'checklist_type': 'installation',
                'installation_type': 'solar',
                'description': 'Installation checklist for solar panel systems',
                'items': [
                    {
                        'id': 'mounting_hardware',
                        'title': 'Mounting Hardware Installation',
                        'description': 'Install all mounting rails and hardware securely',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 4,
                        'notes_required': True
                    },
                    {
                        'id': 'panel_installation',
                        'title': 'Solar Panel Installation',
                        'description': 'Install and secure all solar panels',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 5,
                        'notes_required': True
                    },
                    {
                        'id': 'wiring_installation',
                        'title': 'Electrical Wiring',
                        'description': 'Complete all DC and AC wiring connections',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 3,
                        'notes_required': True
                    },
                    {
                        'id': 'inverter_installation',
                        'title': 'Inverter Installation',
                        'description': 'Install and configure inverter system',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 3,
                        'notes_required': True
                    },
                    {
                        'id': 'grounding',
                        'title': 'Grounding System',
                        'description': 'Install proper grounding for system safety',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': True
                    },
                    {
                        'id': 'weather_proofing',
                        'title': 'Weather Proofing',
                        'description': 'Seal all roof penetrations and ensure weather-tight installation',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 3,
                        'notes_required': False
                    },
                ],
                'is_active': True
            },
            {
                'name': 'Solar Commissioning Checklist',
                'checklist_type': 'commissioning',
                'installation_type': 'solar',
                'description': 'Final commissioning checklist for solar installations',
                'items': [
                    {
                        'id': 'system_power_on',
                        'title': 'System Power-On Test',
                        'description': 'Power on system and verify basic operation',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': True
                    },
                    {
                        'id': 'voltage_testing',
                        'title': 'Voltage and Current Testing',
                        'description': 'Measure and document voltage and current at key points',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 3,
                        'notes_required': True
                    },
                    {
                        'id': 'monitoring_setup',
                        'title': 'Monitoring System Configuration',
                        'description': 'Configure and verify remote monitoring system',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': True
                    },
                    {
                        'id': 'safety_features',
                        'title': 'Safety Features Test',
                        'description': 'Test all safety features including shutdown procedures',
                        'required': True,
                        'requires_photo': False,
                        'photo_count': 0,
                        'notes_required': True
                    },
                    {
                        'id': 'customer_training',
                        'title': 'Customer Training',
                        'description': 'Train customer on system operation and maintenance',
                        'required': True,
                        'requires_photo': False,
                        'photo_count': 0,
                        'notes_required': True
                    },
                    {
                        'id': 'documentation',
                        'title': 'Documentation Handover',
                        'description': 'Provide all system documentation and warranties to customer',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 1,
                        'notes_required': True
                    },
                ],
                'is_active': True
            },
            {
                'name': 'Starlink Pre-Installation Checklist',
                'checklist_type': 'pre_install',
                'installation_type': 'starlink',
                'description': 'Pre-installation checklist for Starlink installations',
                'items': [
                    {
                        'id': 'site_survey',
                        'title': 'Site Survey',
                        'description': 'Survey installation site for optimal placement',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 3,
                        'notes_required': True
                    },
                    {
                        'id': 'obstruction_check',
                        'title': 'Sky Obstruction Check',
                        'description': 'Check for obstructions in the required field of view',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': True
                    },
                    {
                        'id': 'power_availability',
                        'title': 'Power Source Verification',
                        'description': 'Verify adequate power source is available',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 1,
                        'notes_required': False
                    },
                    {
                        'id': 'mounting_location',
                        'title': 'Mounting Location Assessment',
                        'description': 'Assess and confirm dish mounting location',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': True
                    },
                ],
                'is_active': True
            },
            {
                'name': 'Starlink Installation Checklist',
                'checklist_type': 'installation',
                'installation_type': 'starlink',
                'description': 'Installation checklist for Starlink systems',
                'items': [
                    {
                        'id': 'mount_installation',
                        'title': 'Mounting Bracket Installation',
                        'description': 'Install mounting bracket securely',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 3,
                        'notes_required': True
                    },
                    {
                        'id': 'dish_installation',
                        'title': 'Dish Installation',
                        'description': 'Install and position Starlink dish',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 3,
                        'notes_required': True
                    },
                    {
                        'id': 'cable_routing',
                        'title': 'Cable Routing',
                        'description': 'Route cables from dish to router location',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': False
                    },
                    {
                        'id': 'router_setup',
                        'title': 'Router Installation',
                        'description': 'Install and position Starlink router',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 2,
                        'notes_required': False
                    },
                ],
                'is_active': True
            },
            {
                'name': 'Starlink Commissioning Checklist',
                'checklist_type': 'commissioning',
                'installation_type': 'starlink',
                'description': 'Commissioning checklist for Starlink installations',
                'items': [
                    {
                        'id': 'system_activation',
                        'title': 'System Activation',
                        'description': 'Activate and configure Starlink service',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 1,
                        'notes_required': True
                    },
                    {
                        'id': 'speed_test',
                        'title': 'Speed Test',
                        'description': 'Conduct speed test and document results',
                        'required': True,
                        'requires_photo': True,
                        'photo_count': 1,
                        'notes_required': True
                    },
                    {
                        'id': 'wifi_setup',
                        'title': 'WiFi Configuration',
                        'description': 'Configure WiFi network and test connectivity',
                        'required': True,
                        'requires_photo': False,
                        'photo_count': 0,
                        'notes_required': True
                    },
                    {
                        'id': 'customer_training',
                        'title': 'Customer Training',
                        'description': 'Train customer on system operation and app usage',
                        'required': True,
                        'requires_photo': False,
                        'photo_count': 0,
                        'notes_required': True
                    },
                ],
                'is_active': True
            },
            {
                'name': 'General Pre-Installation Checklist',
                'checklist_type': 'pre_install',
                'installation_type': None,
                'description': 'General pre-installation checklist for all installation types',
                'items': [
                    {
                        'id': 'customer_contact',
                        'title': 'Customer Contact Confirmation',
                        'description': 'Confirm customer contact details and appointment',
                        'required': True,
                        'requires_photo': False,
                        'photo_count': 0,
                        'notes_required': True
                    },
                    {
                        'id': 'tools_equipment',
                        'title': 'Tools and Equipment Check',
                        'description': 'Verify all required tools and equipment are available',
                        'required': True,
                        'requires_photo': False,
                        'photo_count': 0,
                        'notes_required': True
                    },
                    {
                        'id': 'safety_gear',
                        'title': 'Safety Gear Check',
                        'description': 'Verify all safety equipment is available and in good condition',
                        'required': True,
                        'requires_photo': False,
                        'photo_count': 0,
                        'notes_required': False
                    },
                ],
                'is_active': True
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            # Check if template already exists
            existing = CommissioningChecklistTemplate.objects.filter(
                name=template_data['name'],
                checklist_type=template_data['checklist_type']
            ).first()

            if existing:
                # Update existing template
                for key, value in template_data.items():
                    setattr(existing, key, value)
                existing.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {existing.name}')
                )
            else:
                # Create new template
                template = CommissioningChecklistTemplate.objects.create(**template_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {template.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new templates, '
                f'updated {updated_count} existing templates.'
            )
        )
