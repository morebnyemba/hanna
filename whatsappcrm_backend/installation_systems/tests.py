from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from conversations.models import Contact
from customer_data.models import CustomerProfile, Order
from warranty.models import Technician
from products_and_services.models import Product, SerializedItem
from .models import InstallationSystemRecord, CommissioningChecklistTemplate, InstallationChecklistEntry

User = get_user_model()


class InstallationSystemRecordModelTest(TestCase):
    """Tests for the InstallationSystemRecord model"""
    
    def setUp(self):
        """Set up test data"""
        # Create user for technician
        self.user = User.objects.create_user(
            username='techuser',
            email='tech@example.com',
            password='testpass123'
        )
        
        # Create WhatsApp contact
        self.contact = Contact.objects.create(
            whatsapp_id='+263771234567',
            name='John Doe'
        )
        
        # Create customer profile
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com'
        )
        
        # Create order
        self.order = Order.objects.create(
            order_number='ORD-001',
            name='Solar Installation Order',
            customer=self.customer,
            amount=Decimal('5000.00')
        )
        
        # Create technician
        self.technician = Technician.objects.create(
            user=self.user,
            specialization='Solar Installation'
        )
        
        # Create product
        self.product = Product.objects.create(
            name='Solar Panel 500W',
            sku='SOLAR-500W',
            product_type='hardware',
            price=Decimal('250.00')
        )
        
        # Create serialized item
        self.serialized_item = SerializedItem.objects.create(
            product=self.product,
            serial_number='SN123456789',
            status='in_stock'
        )
    
    def test_create_solar_installation_record(self):
        """Test creating a solar installation system record"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            order=self.order,
            installation_type='solar',
            system_size=Decimal('5.0'),
            capacity_unit='kW',
            system_classification='residential',
            installation_status='pending',
            installation_date=date(2024, 1, 15),
            installation_address='123 Main St, Harare',
            latitude=Decimal('-17.825166'),
            longitude=Decimal('31.033510')
        )
        
        self.assertEqual(isr.installation_type, 'solar')
        self.assertEqual(isr.system_size, Decimal('5.0'))
        self.assertEqual(isr.capacity_unit, 'kW')
        self.assertEqual(isr.system_classification, 'residential')
        self.assertEqual(isr.customer, self.customer)
        self.assertEqual(isr.order, self.order)
        self.assertIsNotNone(isr.id)
        self.assertIsNotNone(isr.created_at)
        self.assertIsNotNone(isr.updated_at)
    
    def test_create_starlink_installation_record(self):
        """Test creating a starlink installation system record"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='starlink',
            system_size=Decimal('100.0'),
            capacity_unit='Mbps',
            system_classification='commercial',
            installation_status='active',
            installation_date=date(2024, 2, 20),
            commissioning_date=date(2024, 2, 21),
            remote_monitoring_id='STARLINK-001',
            installation_address='456 Office Park, Bulawayo'
        )
        
        self.assertEqual(isr.installation_type, 'starlink')
        self.assertEqual(isr.system_size, Decimal('100.0'))
        self.assertEqual(isr.capacity_unit, 'Mbps')
        self.assertEqual(isr.remote_monitoring_id, 'STARLINK-001')
    
    def test_create_custom_furniture_installation_record(self):
        """Test creating a custom furniture installation system record"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='custom_furniture',
            system_size=Decimal('3.0'),
            capacity_unit='units',
            system_classification='residential',
            installation_status='active',
            installation_date=date(2024, 3, 10),
            installation_address='789 Residential Ave'
        )
        
        self.assertEqual(isr.installation_type, 'custom_furniture')
        self.assertEqual(isr.capacity_unit, 'units')
        self.assertEqual(isr.installation_status, 'active')
    
    def test_create_hybrid_installation_record(self):
        """Test creating a hybrid (starlink + solar) installation record"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='hybrid',
            system_size=Decimal('10.0'),
            capacity_unit='kW',
            system_classification='hybrid',
            installation_status='commissioned',
            installation_date=date(2024, 4, 5),
            commissioning_date=date(2024, 4, 6)
        )
        
        self.assertEqual(isr.installation_type, 'hybrid')
        self.assertEqual(isr.system_classification, 'hybrid')
        self.assertEqual(isr.installation_status, 'commissioned')
    
    def test_str_method_solar(self):
        """Test __str__ method for solar installation"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            system_size=Decimal('5.0'),
            capacity_unit='kW',
        )
        
        str_repr = str(isr)
        self.assertIn('ISR-', str_repr)
        self.assertIn('John Doe', str_repr)
        self.assertIn('solar', str_repr)
        self.assertIn('5', str_repr)
        self.assertIn('kW', str_repr)
    
    def test_str_method_starlink(self):
        """Test __str__ method for starlink installation"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='starlink',
            system_size=Decimal('100.0'),
            capacity_unit='Mbps',
        )
        
        str_repr = str(isr)
        self.assertIn('starlink', str_repr)
        self.assertIn('100', str_repr)
        self.assertIn('Mbps', str_repr)
    
    def test_str_method_custom_furniture(self):
        """Test __str__ method for custom furniture installation"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='custom_furniture',
            system_size=Decimal('3.0'),
            capacity_unit='units',
        )
        
        str_repr = str(isr)
        self.assertIn('custom_furniture', str_repr)
        self.assertIn('3', str_repr)
        self.assertIn('units', str_repr)
    
    def test_str_method_no_system_size(self):
        """Test __str__ method when system_size is None"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            system_size=None,
        )
        
        str_repr = str(isr)
        self.assertIn('N/A', str_repr)
    
    def test_technicians_relationship(self):
        """Test ManyToMany relationship with technicians"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
        )
        
        isr.technicians.add(self.technician)
        self.assertEqual(isr.technicians.count(), 1)
        self.assertEqual(isr.technicians.first(), self.technician)
        
        # Test reverse relationship
        self.assertIn(isr, self.technician.installation_system_records.all())
    
    def test_installed_components_relationship(self):
        """Test ManyToMany relationship with SerializedItems"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
        )
        
        isr.installed_components.add(self.serialized_item)
        self.assertEqual(isr.installed_components.count(), 1)
        self.assertEqual(isr.installed_components.first(), self.serialized_item)
        
        # Test reverse relationship
        self.assertIn(isr, self.serialized_item.installation_system_records.all())
    
    def test_customer_relationship(self):
        """Test ForeignKey relationship with CustomerProfile"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
        )
        
        # Test forward relationship
        self.assertEqual(isr.customer, self.customer)
        
        # Test reverse relationship
        self.assertIn(isr, self.customer.installation_system_records.all())
    
    def test_order_relationship(self):
        """Test ForeignKey relationship with Order"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            order=self.order,
            installation_type='solar',
        )
        
        # Test forward relationship
        self.assertEqual(isr.order, self.order)
        
        # Test reverse relationship
        self.assertIn(isr, self.order.installation_system_records.all())
    
    def test_order_nullable(self):
        """Test that order field is nullable"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            order=None,
            installation_type='solar',
        )
        
        self.assertIsNone(isr.order)
    
    def test_default_values(self):
        """Test that default values are set correctly"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
        )
        
        self.assertEqual(isr.capacity_unit, 'units')
        self.assertEqual(isr.system_classification, 'residential')
        self.assertEqual(isr.installation_status, 'pending')
    
    def test_gps_coordinates(self):
        """Test GPS coordinates fields"""
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            latitude=Decimal('-17.825166'),
            longitude=Decimal('31.033510')
        )
        
        self.assertEqual(isr.latitude, Decimal('-17.825166'))
        self.assertEqual(isr.longitude, Decimal('31.033510'))
    
    def test_installation_dates(self):
        """Test installation and commissioning date fields"""
        install_date = date(2024, 1, 15)
        commission_date = date(2024, 1, 20)
        
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            installation_date=install_date,
            commissioning_date=commission_date
        )
        
        self.assertEqual(isr.installation_date, install_date)
        self.assertEqual(isr.commissioning_date, commission_date)
    
    def test_model_ordering(self):
        """Test that model ordering is by -created_at"""
        isr1 = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
        )
        
        isr2 = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='starlink',
        )
        
        records = list(InstallationSystemRecord.objects.all())
        self.assertEqual(records[0], isr2)  # Most recent first
        self.assertEqual(records[1], isr1)
    
    def test_installation_request_relationship(self):
        """Test OneToOne relationship with InstallationRequest"""
        from customer_data.models import InstallationRequest
        
        # Create InstallationRequest
        inst_request = InstallationRequest.objects.create(
            customer=self.customer,
            installation_type='solar',
            full_name='John Doe',
            address='123 Test St',
            preferred_datetime='2024-01-15',
            contact_phone='+263771234567'
        )
        
        # Create ISR linked to InstallationRequest
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_request=inst_request,
            installation_type='solar',
        )
        
        # Test forward relationship
        self.assertEqual(isr.installation_request, inst_request)
        
        # Test reverse relationship
        self.assertEqual(inst_request.installation_system_record, isr)
    
    def test_warranties_relationship(self):
        """Test ManyToMany relationship with Warranty"""
        from warranty.models import Warranty, Manufacturer
        
        # Create manufacturer
        manufacturer = Manufacturer.objects.create(name='Test Manufacturer')
        
        # Create warranty
        warranty = Warranty.objects.create(
            manufacturer=manufacturer,
            serialized_item=self.serialized_item,
            customer=self.customer,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1)
        )
        
        # Create ISR
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
        )
        
        # Add warranty
        isr.warranties.add(warranty)
        self.assertEqual(isr.warranties.count(), 1)
        self.assertEqual(isr.warranties.first(), warranty)
        
        # Test reverse relationship
        self.assertIn(isr, warranty.installation_system_records.all())
    
    def test_job_cards_relationship(self):
        """Test ManyToMany relationship with JobCard"""
        from customer_data.models import JobCard
        
        # Create job card
        job_card = JobCard.objects.create(
            job_card_number='JC-001',
            customer=self.customer,
            serialized_item=self.serialized_item,
            reported_fault='Test fault',
            is_under_warranty=True
        )
        
        # Create ISR
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
        )
        
        # Add job card
        isr.job_cards.add(job_card)
        self.assertEqual(isr.job_cards.count(), 1)
        self.assertEqual(isr.job_cards.first(), job_card)
        
        # Test reverse relationship
        self.assertIn(isr, job_card.installation_system_records.all())


class CommissioningChecklistTemplateModelTest(TestCase):
    """Tests for the CommissioningChecklistTemplate model"""
    
    def test_create_checklist_template(self):
        """Test creating a checklist template"""
        
        items = [
            {
                'id': 'item_1',
                'title': 'Check item 1',
                'description': 'Description 1',
                'required': True,
                'requires_photo': True,
                'photo_count': 2,
                'notes_required': False
            },
            {
                'id': 'item_2',
                'title': 'Check item 2',
                'description': 'Description 2',
                'required': True,
                'requires_photo': False,
                'photo_count': 0,
                'notes_required': True
            }
        ]
        
        template = CommissioningChecklistTemplate.objects.create(
            name='Test Pre-Installation Checklist',
            checklist_type='pre_install',
            installation_type='solar',
            description='Test checklist for solar pre-installation',
            items=items,
            is_active=True
        )
        
        self.assertEqual(template.name, 'Test Pre-Installation Checklist')
        self.assertEqual(template.checklist_type, 'pre_install')
        self.assertEqual(template.installation_type, 'solar')
        self.assertEqual(len(template.items), 2)
        self.assertTrue(template.is_active)
        self.assertIsNotNone(template.id)
        
    def test_str_method(self):
        """Test __str__ method"""
        
        template = CommissioningChecklistTemplate.objects.create(
            name='Solar Commissioning',
            checklist_type='commissioning',
            items=[]
        )
        
        str_repr = str(template)
        self.assertIn('Solar Commissioning', str_repr)
        self.assertIn('Commissioning', str_repr)
    
    def test_template_without_installation_type(self):
        """Test template without specific installation type (general template)"""
        
        template = CommissioningChecklistTemplate.objects.create(
            name='General Safety Checklist',
            checklist_type='pre_install',
            installation_type=None,
            items=[]
        )
        
        self.assertIsNone(template.installation_type)


class InstallationChecklistEntryModelTest(TestCase):
    """Tests for the InstallationChecklistEntry model"""
    
    def setUp(self):
        """Set up test data"""
        
        # Create user for technician
        self.user = User.objects.create_user(
            username='techuser',
            email='tech@example.com',
            password='testpass123'
        )
        
        # Create WhatsApp contact
        self.contact = Contact.objects.create(
            whatsapp_id='+263771234567',
            name='John Doe'
        )
        
        # Create customer profile
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com'
        )
        
        # Create technician
        self.technician = Technician.objects.create(
            user=self.user,
            specialization='Solar Installation'
        )
        
        # Create installation record
        self.isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            system_size=Decimal('5.0'),
            capacity_unit='kW',
            installation_status='pending'
        )
        
        # Create checklist template
        self.template = CommissioningChecklistTemplate.objects.create(
            name='Test Checklist',
            checklist_type='installation',
            installation_type='solar',
            items=[
                {
                    'id': 'item_1',
                    'title': 'Required Item 1',
                    'required': True,
                    'requires_photo': True,
                    'photo_count': 2
                },
                {
                    'id': 'item_2',
                    'title': 'Required Item 2',
                    'required': True,
                    'requires_photo': False,
                    'photo_count': 0
                },
                {
                    'id': 'item_3',
                    'title': 'Optional Item',
                    'required': False,
                    'requires_photo': False,
                    'photo_count': 0
                }
            ]
        )
    
    def test_create_checklist_entry(self):
        """Test creating a checklist entry"""
        
        entry = InstallationChecklistEntry.objects.create(
            installation_record=self.isr,
            template=self.template,
            technician=self.technician
        )
        
        self.assertEqual(entry.installation_record, self.isr)
        self.assertEqual(entry.template, self.template)
        self.assertEqual(entry.technician, self.technician)
        self.assertEqual(entry.completion_status, 'not_started')
        self.assertEqual(entry.completion_percentage, 0)
        self.assertIsNotNone(entry.id)
    
    def test_calculate_completion_percentage_empty(self):
        """Test completion percentage calculation with no completed items"""
        
        entry = InstallationChecklistEntry.objects.create(
            installation_record=self.isr,
            template=self.template
        )
        
        percentage = entry.calculate_completion_percentage()
        self.assertEqual(percentage, Decimal('0'))
    
    def test_calculate_completion_percentage_partial(self):
        """Test completion percentage calculation with partial completion"""
        
        entry = InstallationChecklistEntry.objects.create(
            installation_record=self.isr,
            template=self.template,
            completed_items={
                'item_1': {'completed': True},
                'item_2': {'completed': False}
            }
        )
        
        percentage = entry.calculate_completion_percentage()
        # 1 out of 2 required items = 50%
        self.assertEqual(percentage, Decimal('50.00'))
    
    def test_calculate_completion_percentage_full(self):
        """Test completion percentage calculation with full completion"""
        
        entry = InstallationChecklistEntry.objects.create(
            installation_record=self.isr,
            template=self.template,
            completed_items={
                'item_1': {'completed': True},
                'item_2': {'completed': True},
                'item_3': {'completed': False}  # Optional, doesn't affect percentage
            }
        )
        
        percentage = entry.calculate_completion_percentage()
        # 2 out of 2 required items = 100%
        self.assertEqual(percentage, Decimal('100.00'))
    
    def test_update_completion_status_not_started(self):
        """Test update_completion_status for not started"""
        
        entry = InstallationChecklistEntry.objects.create(
            installation_record=self.isr,
            template=self.template
        )
        
        entry.update_completion_status()
        self.assertEqual(entry.completion_status, 'not_started')
        self.assertIsNone(entry.started_at)
    
    def test_update_completion_status_in_progress(self):
        """Test update_completion_status for in progress"""
        
        entry = InstallationChecklistEntry.objects.create(
            installation_record=self.isr,
            template=self.template,
            completed_items={
                'item_1': {'completed': True}
            }
        )
        
        entry.update_completion_status()
        self.assertEqual(entry.completion_status, 'in_progress')
        self.assertIsNotNone(entry.started_at)
    
    def test_update_completion_status_completed(self):
        """Test update_completion_status for completed"""
        
        entry = InstallationChecklistEntry.objects.create(
            installation_record=self.isr,
            template=self.template,
            completed_items={
                'item_1': {'completed': True},
                'item_2': {'completed': True}
            }
        )
        
        entry.update_completion_status()
        self.assertEqual(entry.completion_status, 'completed')
        self.assertIsNotNone(entry.completed_at)
    
    def test_is_fully_completed(self):
        """Test is_fully_completed method"""
        
        entry = InstallationChecklistEntry.objects.create(
            installation_record=self.isr,
            template=self.template,
            completed_items={
                'item_1': {'completed': True},
                'item_2': {'completed': True}
            }
        )
        entry.update_completion_status()
        
        self.assertTrue(entry.is_fully_completed())
        
        # Test incomplete
        entry.completed_items['item_2']['completed'] = False
        entry.update_completion_status()
        self.assertFalse(entry.is_fully_completed())


class InstallationValidationTest(TestCase):
    """Tests for installation validation logic"""
    
    def setUp(self):
        """Set up test data"""
        
        # Create user
        self.user = User.objects.create_user(
            username='techuser',
            email='tech@example.com',
            password='testpass123'
        )
        
        # Create WhatsApp contact
        self.contact = Contact.objects.create(
            whatsapp_id='+263771234567',
            name='John Doe'
        )
        
        # Create customer profile
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com'
        )
        
        # Create technician
        self.technician = Technician.objects.create(
            user=self.user,
            specialization='Solar Installation'
        )
        
        # Create checklist template
        self.template = CommissioningChecklistTemplate.objects.create(
            name='Test Checklist',
            checklist_type='commissioning',
            items=[
                {
                    'id': 'item_1',
                    'title': 'Required Item',
                    'required': True
                }
            ]
        )
    
    def test_cannot_commission_without_complete_checklist(self):
        """Test that installation cannot be commissioned without complete checklist"""
        # Create installation
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            installation_status='pending'
        )
        
        # Create incomplete checklist
        entry = InstallationChecklistEntry.objects.create(
            installation_record=isr,
            template=self.template,
            completed_items={}
        )
        entry.update_completion_status()
        entry.save()
        
        # Try to change status to commissioned
        isr.installation_status = 'commissioned'
        
        with self.assertRaises(ValidationError) as context:
            isr.save()
        
        self.assertIn('Cannot mark installation', str(context.exception))
        self.assertIn('100% complete', str(context.exception))
    
    def test_can_commission_with_complete_checklist(self):
        """Test that installation can be commissioned with complete checklist"""
        
        # Create installation
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            installation_status='pending'
        )
        
        # Create complete checklist
        entry = InstallationChecklistEntry.objects.create(
            installation_record=isr,
            template=self.template,
            completed_items={
                'item_1': {'completed': True}
            }
        )
        entry.update_completion_status()
        entry.save()
        
        # Change status to commissioned - should work
        isr.installation_status = 'commissioned'
        isr.save()  # Should not raise exception
        
        self.assertEqual(isr.installation_status, 'commissioned')
    
    def test_can_commission_without_checklists(self):
        """Test that installation can be commissioned if no checklists exist"""
        # Create installation without any checklists
        isr = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            installation_status='pending'
        )
        
        # Change status to commissioned - should work
        isr.installation_status = 'commissioned'
        isr.save()  # Should not raise exception
        
        self.assertEqual(isr.installation_status, 'commissioned')
