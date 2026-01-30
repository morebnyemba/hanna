"""
Management command to create a complete test installation with checklist.
Usage: python manage.py create_test_installation
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User
from customer_data.models import CustomerProfile, Contact, InstallationRequest
from installation_systems.models import InstallationSystemRecord
from warranty.models import Technician
from decimal import Decimal
from datetime import date


class Command(BaseCommand):
    help = 'Creates a complete test installation setup for testing checklists'

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Create/get technician user
        tech_user, created = User.objects.get_or_create(
            username="technician_test",
            defaults={
                'email': "technician@hanna.co.zw",
                'role': 'technician',
                'is_active': True,
                'first_name': 'Test',
                'last_name': 'Technician',
            }
        )
        if created:
            tech_user.set_password("Tech123!@#")
            tech_user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Created technician user: {tech_user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️  Technician user already exists: {tech_user.username}'))
        
        # 2. Create/get Technician profile
        technician, created = Technician.objects.get_or_create(
            user=tech_user,
            defaults={
                'employee_id': 'TECH001',
                'specialization': 'Solar',
                'certification_level': 'advanced',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created technician profile'))
        
        # 3. Create test contact
        contact, _ = Contact.objects.get_or_create(
            whatsapp_id='+263771234567',
            defaults={
                'name': 'Test Customer',
            }
        )
        
        # 4. Create test customer
        customer, created = CustomerProfile.objects.get_or_create(
            contact=contact,
            defaults={
                'first_name': 'Test',
                'last_name': 'Customer',
                'address_line_1': '123 Test Street',
                'city': 'Harare',
                'country': 'Zimbabwe',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created test customer: {customer.get_full_name()}'))
        
        # 5. Create InstallationRequest
        inst_request, created = InstallationRequest.objects.get_or_create(
            customer=customer,
            contact_phone=contact.whatsapp_id,
            defaults={
                'installation_type': 'solar',
                'full_name': customer.get_full_name(),
                'address': customer.address_line_1,
                'preferred_datetime': 'ASAP',
                'status': 'in_progress',
                'notes': 'Test installation for checklist functionality',
            }
        )
        
        # Assign technician to InstallationRequest
        inst_request.technicians.add(technician)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created installation request: {inst_request.id}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️  Using existing installation request: {inst_request.id}'))
        
        # 6. Create or get InstallationSystemRecord
        isr = None
        if hasattr(inst_request, 'installation_system_record'):
            isr = inst_request.installation_system_record
            self.stdout.write(self.style.WARNING(f'ℹ️  ISR already exists: {isr.id}'))
        else:
            isr = InstallationSystemRecord.objects.create(
                installation_request=inst_request,
                customer=customer,
                installation_type='solar',
                system_size=Decimal('5.0'),
                capacity_unit='kW',
                system_classification='residential',
                installation_status='in_progress',
                installation_date=date.today(),
                installation_address=customer.address_line_1,
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created ISR: {isr.id}'))
        
        # Assign technician to ISR (triggers checklist creation)
        isr.technicians.add(technician)
        self.stdout.write(self.style.SUCCESS(f'✅ Assigned technician to ISR'))
        
        # 7. Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('TEST INSTALLATION CREATED SUCCESSFULLY!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\n🔐 LOGIN CREDENTIALS:')
        self.stdout.write(f'   Username: technician_test')
        self.stdout.write(f'   Password: Tech123!@#')
        self.stdout.write(f'\n📋 TEST DATA:')
        self.stdout.write(f'   Customer: {customer.get_full_name()}')
        self.stdout.write(f'   Installation Request ID: {inst_request.id}')
        self.stdout.write(f'   Installation System Record ID: {isr.id}')
        self.stdout.write(f'   Technician: {technician.user.get_full_name()}')
        self.stdout.write(f'\n🔗 TEST URLS:')
        self.stdout.write(f'   Checklists: /technician/checklists')
        self.stdout.write(f'   Specific: /technician/checklists?installation={isr.id}')
        self.stdout.write(self.style.SUCCESS('\n✅ You can now log in and test the checklist functionality!'))
