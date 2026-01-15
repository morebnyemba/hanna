"""
Tests for serial number capture and validation for technician portal.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from conversations.models import Contact
from customer_data.models import CustomerProfile, Order
from warranty.models import Technician, Manufacturer
from products_and_services.models import Product, SerializedItem
from installation_systems.models import InstallationSystemRecord

User = get_user_model()


class SerialNumberValidationTestCase(TestCase):
    """Tests for serial number validation endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.tech_user = User.objects.create_user(
            username='techuser',
            email='tech@example.com',
            password='techpass123'
        )
        
        # Create technician profile
        self.technician = Technician.objects.create(
            user=self.tech_user,
            specialization='Solar Installation',
            technician_type='installer'
        )
        
        # Create contact and customer
        self.contact = Contact.objects.create(
            whatsapp_id='+263771234567',
            name='John Doe'
        )
        
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com'
        )
        
        # Create products
        self.panel_product = Product.objects.create(
            name='Solar Panel 500W',
            sku='PANEL-500W',
            barcode='BAR-PANEL-500',
            product_type='hardware',
            price=Decimal('250.00')
        )
        
        self.inverter_product = Product.objects.create(
            name='Inverter 5kVA',
            sku='INV-5KVA',
            barcode='BAR-INV-5K',
            product_type='hardware',
            price=Decimal('1500.00')
        )
        
        self.battery_product = Product.objects.create(
            name='Battery 200Ah',
            sku='BAT-200AH',
            product_type='hardware',
            price=Decimal('800.00')
        )
        
        # Create serialized items
        self.panel_item = SerializedItem.objects.create(
            product=self.panel_product,
            serial_number='PANEL-SN-001',
            barcode='PANEL-BAR-001',
            status=SerializedItem.Status.IN_STOCK
        )
        
        self.inverter_item = SerializedItem.objects.create(
            product=self.inverter_product,
            serial_number='INV-SN-001',
            barcode='INV-BAR-001',
            status=SerializedItem.Status.IN_STOCK
        )
        
        # Create installation
        self.installation = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            system_size=Decimal('5.0'),
            capacity_unit='kW',
            system_classification='residential',
            installation_status='in_progress',
            installation_address='123 Main St, Harare'
        )
        self.installation.technicians.add(self.technician)
        
        # Setup API client
        self.client = APIClient()
    
    def test_validate_serial_number_exists_and_available(self):
        """Test validating a serial number that exists and is available"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/validate-serial-number/',
            {
                'serial_number': 'PANEL-SN-001'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])
        self.assertTrue(response.data['valid'])
        self.assertFalse(response.data['already_assigned'])
        self.assertIsNone(response.data['assigned_to'])
        self.assertEqual(len(response.data['errors']), 0)
        self.assertIsNotNone(response.data['item'])
        self.assertEqual(response.data['item']['serial_number'], 'PANEL-SN-001')
    
    def test_validate_serial_number_does_not_exist(self):
        """Test validating a serial number that doesn't exist"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/validate-serial-number/',
            {
                'serial_number': 'NONEXISTENT-SN'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['exists'])
        self.assertFalse(response.data['valid'])
        self.assertIn('does not exist', response.data['errors'][0])
    
    def test_validate_serial_number_already_assigned(self):
        """Test validating a serial number that's already assigned to another installation"""
        # Assign item to installation
        self.installation.installed_components.add(self.panel_item)
        
        # Create another installation
        contact2 = Contact.objects.create(
            whatsapp_id='+263771234568',
            name='Jane Smith'
        )
        customer2 = CustomerProfile.objects.create(
            contact=contact2,
            first_name='Jane',
            last_name='Smith'
        )
        installation2 = InstallationSystemRecord.objects.create(
            customer=customer2,
            installation_type='solar',
            system_classification='residential',
            installation_status='in_progress'
        )
        
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/validate-serial-number/',
            {
                'serial_number': 'PANEL-SN-001',
                'installation_id': str(installation2.id)
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])
        self.assertFalse(response.data['valid'])  # Not valid because already assigned
        self.assertTrue(response.data['already_assigned'])
        self.assertIsNotNone(response.data['assigned_to'])
        self.assertIn('already assigned', response.data['errors'][0])
    
    def test_validate_serial_number_same_installation(self):
        """Test validating a serial number that's already in the same installation"""
        # Assign item to installation
        self.installation.installed_components.add(self.panel_item)
        
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/validate-serial-number/',
            {
                'serial_number': 'PANEL-SN-001',
                'installation_id': str(self.installation.id)
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])
        self.assertTrue(response.data['valid'])  # Valid because same installation
        self.assertTrue(response.data['already_assigned'])
        self.assertIsNone(response.data['assigned_to'])  # None because it's in the same installation
    
    def test_lookup_by_barcode_finds_serialized_item(self):
        """Test looking up a serialized item by barcode"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/lookup-by-barcode/',
            {
                'barcode': 'PANEL-BAR-001'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['found'])
        self.assertEqual(response.data['type'], 'serialized_item')
        self.assertIsNotNone(response.data['item'])
        self.assertEqual(response.data['item']['serial_number'], 'PANEL-SN-001')
    
    def test_lookup_by_barcode_finds_product(self):
        """Test looking up a product by barcode when no serialized item exists"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/lookup-by-barcode/',
            {
                'barcode': 'BAR-INV-5K'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['found'])
        self.assertEqual(response.data['type'], 'product')
        self.assertIsNotNone(response.data['product'])
        self.assertEqual(response.data['product']['sku'], 'INV-5KVA')
    
    def test_lookup_by_barcode_not_found(self):
        """Test looking up with a barcode that doesn't exist"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/lookup-by-barcode/',
            {
                'barcode': 'NONEXISTENT-BARCODE'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['found'])
    
    def test_batch_capture_success(self):
        """Test batch capturing multiple serial numbers"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/batch-capture/',
            {
                'installation_id': str(self.installation.id),
                'serial_numbers': [
                    {
                        'serial_number': 'PANEL-SN-001'
                    },
                    {
                        'serial_number': 'INV-SN-001'
                    }
                ]
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 2)
        self.assertEqual(response.data['error_count'], 0)
        self.assertEqual(response.data['total'], 2)
        
        # Verify items were added to installation
        self.assertTrue(
            self.installation.installed_components.filter(serial_number='PANEL-SN-001').exists()
        )
        self.assertTrue(
            self.installation.installed_components.filter(serial_number='INV-SN-001').exists()
        )
    
    def test_batch_capture_create_new_item(self):
        """Test batch capture can create new items if product_id provided"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/batch-capture/',
            {
                'installation_id': str(self.installation.id),
                'serial_numbers': [
                    {
                        'serial_number': 'NEW-BATTERY-001',
                        'product_id': self.battery_product.id,
                        'barcode': 'BAT-BAR-001',
                        'notes': 'New battery for solar system'
                    }
                ]
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 1)
        self.assertEqual(response.data['error_count'], 0)
        
        # Verify item was created
        new_item = SerializedItem.objects.get(serial_number='NEW-BATTERY-001')
        self.assertEqual(new_item.product, self.battery_product)
        self.assertEqual(new_item.barcode, 'BAT-BAR-001')
        
        # Verify item was added to installation
        self.assertTrue(
            self.installation.installed_components.filter(serial_number='NEW-BATTERY-001').exists()
        )
    
    def test_batch_capture_mixed_results(self):
        """Test batch capture with mix of success and errors"""
        # Assign panel to another installation
        contact2 = Contact.objects.create(
            whatsapp_id='+263771234569',
            name='Bob Johnson'
        )
        customer2 = CustomerProfile.objects.create(
            contact=contact2,
            first_name='Bob',
            last_name='Johnson'
        )
        installation2 = InstallationSystemRecord.objects.create(
            customer=customer2,
            installation_type='solar',
            system_classification='residential',
            installation_status='in_progress'
        )
        installation2.installed_components.add(self.panel_item)
        
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/batch-capture/',
            {
                'installation_id': str(self.installation.id),
                'serial_numbers': [
                    {
                        'serial_number': 'PANEL-SN-001'  # Already assigned to installation2
                    },
                    {
                        'serial_number': 'INV-SN-001'  # Available
                    },
                    {
                        'serial_number': 'NONEXISTENT-SN'  # Doesn't exist, no product_id
                    }
                ]
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 1)  # Only inverter
        self.assertEqual(response.data['error_count'], 2)  # Panel and nonexistent
        self.assertEqual(response.data['total'], 3)
    
    def test_batch_capture_requires_authentication(self):
        """Test that batch capture requires authentication"""
        response = self.client.post(
            '/crm-api/products/serialized-items/batch-capture/',
            {
                'installation_id': str(self.installation.id),
                'serial_numbers': []
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_batch_capture_requires_technician_assignment(self):
        """Test that technician must be assigned to installation"""
        # Create another technician not assigned to installation
        other_user = User.objects.create_user(
            username='othertech',
            email='other@example.com',
            password='pass123'
        )
        other_tech = Technician.objects.create(
            user=other_user,
            specialization='Solar'
        )
        
        self.client.force_authenticate(user=other_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/batch-capture/',
            {
                'installation_id': str(self.installation.id),
                'serial_numbers': [
                    {'serial_number': 'PANEL-SN-001'}
                ]
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not assigned', response.data['error'].lower())
    
    def test_admin_can_batch_capture_any_installation(self):
        """Test that admin can batch capture for any installation"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/batch-capture/',
            {
                'installation_id': str(self.installation.id),
                'serial_numbers': [
                    {'serial_number': 'PANEL-SN-001'}
                ]
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 1)
    
    def test_validate_requires_serial_number(self):
        """Test that validate endpoint requires serial_number"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/validate-serial-number/',
            {},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('required', response.data['error'].lower())
    
    def test_lookup_requires_barcode(self):
        """Test that lookup endpoint requires barcode"""
        self.client.force_authenticate(user=self.tech_user)
        
        response = self.client.post(
            '/crm-api/products/serialized-items/lookup-by-barcode/',
            {},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('required', response.data['error'].lower())
    
    def test_get_queryset_filters(self):
        """Test that queryset filters work correctly"""
        self.client.force_authenticate(user=self.tech_user)
        
        # Test product_type filter
        response = self.client.get(
            '/crm-api/products/serialized-items/?product_type=hardware'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        # Test status filter
        response = self.client.get(
            '/crm-api/products/serialized-items/?status=in_stock'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test available_only filter
        response = self.client.get(
            '/crm-api/products/serialized-items/?available_only=true'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
