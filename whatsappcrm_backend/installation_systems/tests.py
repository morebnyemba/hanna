from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from conversations.models import Contact
from customer_data.models import CustomerProfile, Order
from warranty.models import Technician
from products_and_services.models import Product, SerializedItem
from .models import InstallationSystemRecord

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
            installation_status='completed',
            installation_date=date(2024, 3, 10),
            installation_address='789 Residential Ave'
        )
        
        self.assertEqual(isr.installation_type, 'custom_furniture')
        self.assertEqual(isr.capacity_unit, 'units')
        self.assertEqual(isr.installation_status, 'completed')
    
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
