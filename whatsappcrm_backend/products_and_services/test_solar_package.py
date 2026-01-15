"""
Tests for SolarPackage model and retailer order creation workflow.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from products_and_services.models import Product, SolarPackage, SolarPackageProduct, ProductCategory
from customer_data.models import Order, OrderItem, CustomerProfile, InstallationRequest
from conversations.models import Contact
from users.models import Retailer

User = get_user_model()


class SolarPackageModelTest(TestCase):
    """Test cases for SolarPackage model"""
    
    def setUp(self):
        """Set up test data"""
        # Create product category
        self.category = ProductCategory.objects.create(
            name='Solar Equipment',
            description='Solar panels, inverters, batteries'
        )
        
        # Create products
        self.inverter = Product.objects.create(
            name='5kW Solar Inverter',
            sku='INV-5KW-001',
            product_type='hardware',
            category=self.category,
            price=Decimal('1500.00'),
            currency='USD',
            is_active=True
        )
        
        self.panel = Product.objects.create(
            name='550W Solar Panel',
            sku='PANEL-550W-001',
            product_type='hardware',
            category=self.category,
            price=Decimal('250.00'),
            currency='USD',
            is_active=True
        )
        
        self.battery = Product.objects.create(
            name='5kWh Lithium Battery',
            sku='BAT-5KWH-001',
            product_type='hardware',
            category=self.category,
            price=Decimal('2500.00'),
            currency='USD',
            is_active=True
        )
    
    def test_create_solar_package(self):
        """Test creating a solar package"""
        package = SolarPackage.objects.create(
            name='3kW Starter System',
            system_size=Decimal('3.0'),
            description='Perfect for small homes',
            price=Decimal('5000.00'),
            currency='USD',
            is_active=True
        )
        
        self.assertEqual(package.name, '3kW Starter System')
        self.assertEqual(package.system_size, Decimal('3.0'))
        self.assertEqual(package.price, Decimal('5000.00'))
        self.assertTrue(package.is_active)
    
    def test_add_products_to_package(self):
        """Test adding products to a solar package"""
        package = SolarPackage.objects.create(
            name='5kW Complete System',
            system_size=Decimal('5.0'),
            price=Decimal('8000.00'),
            currency='USD'
        )
        
        # Add products to package
        SolarPackageProduct.objects.create(
            solar_package=package,
            product=self.inverter,
            quantity=1
        )
        SolarPackageProduct.objects.create(
            solar_package=package,
            product=self.panel,
            quantity=10
        )
        SolarPackageProduct.objects.create(
            solar_package=package,
            product=self.battery,
            quantity=2
        )
        
        # Check that products were added
        self.assertEqual(package.package_products.count(), 3)
        self.assertEqual(package.included_products.count(), 3)
        
        # Check quantities
        inverter_package = package.package_products.get(product=self.inverter)
        self.assertEqual(inverter_package.quantity, 1)
        
        panel_package = package.package_products.get(product=self.panel)
        self.assertEqual(panel_package.quantity, 10)
    
    def test_solar_package_str(self):
        """Test string representation of solar package"""
        package = SolarPackage.objects.create(
            name='3kW Starter System',
            system_size=Decimal('3.0'),
            price=Decimal('5000.00'),
        )
        
        expected = '3kW Starter System (3.0kW)'
        self.assertEqual(str(package), expected)
    
    def test_solar_package_product_unique_constraint(self):
        """Test that a product can't be added to a package twice"""
        package = SolarPackage.objects.create(
            name='Test Package',
            system_size=Decimal('5.0'),
            price=Decimal('8000.00'),
        )
        
        SolarPackageProduct.objects.create(
            solar_package=package,
            product=self.inverter,
            quantity=1
        )
        
        # Try to add the same product again - should fail
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SolarPackageProduct.objects.create(
                solar_package=package,
                product=self.inverter,
                quantity=2
            )


class RetailerOrderCreationTest(TestCase):
    """Test cases for retailer order creation workflow"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and retailer
        self.user = User.objects.create_user(
            username='testretailer',
            email='retailer@test.com',
            password='testpass123'
        )
        
        self.retailer = Retailer.objects.create(
            user=self.user,
            company_name='Test Solar Retailer',
            is_active=True
        )
        
        # Create products
        self.category = ProductCategory.objects.create(name='Solar Equipment')
        
        self.inverter = Product.objects.create(
            name='5kW Inverter',
            sku='INV-5KW',
            product_type='hardware',
            price=Decimal('1500.00'),
            is_active=True
        )
        
        self.panel = Product.objects.create(
            name='550W Panel',
            sku='PANEL-550W',
            product_type='hardware',
            price=Decimal('250.00'),
            is_active=True
        )
        
        # Create solar package
        self.package = SolarPackage.objects.create(
            name='5kW System',
            system_size=Decimal('5.0'),
            price=Decimal('8000.00'),
            currency='USD',
            is_active=True
        )
        
        SolarPackageProduct.objects.create(
            solar_package=self.package,
            product=self.inverter,
            quantity=1
        )
        
        SolarPackageProduct.objects.create(
            solar_package=self.package,
            product=self.panel,
            quantity=10
        )
    
    def test_order_creation_creates_customer_profile(self):
        """Test that order creation creates a customer profile"""
        from customer_data.serializers import RetailerOrderCreationSerializer
        
        data = {
            'solar_package_id': self.package.id,
            'customer_first_name': 'John',
            'customer_last_name': 'Doe',
            'customer_phone': '+263771234567',
            'customer_email': 'john@example.com',
            'address_line_1': '123 Main St',
            'city': 'Harare',
            'country': 'Zimbabwe',
            'payment_method': 'paynow_ecocash',
            'preferred_installation_date': '2024-02-01',
        }
        
        # Mock request with user
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.user)
        serializer = RetailerOrderCreationSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        
        # Check that customer profile was created
        self.assertIsNotNone(result['customer_profile'])
        customer = result['customer_profile']
        self.assertEqual(customer.first_name, 'John')
        self.assertEqual(customer.last_name, 'Doe')
        self.assertEqual(customer.contact.whatsapp_id, '+263771234567')
    
    def test_order_creation_creates_order_with_items(self):
        """Test that order creation creates order with correct items"""
        from customer_data.serializers import RetailerOrderCreationSerializer
        
        data = {
            'solar_package_id': self.package.id,
            'customer_first_name': 'Jane',
            'customer_last_name': 'Smith',
            'customer_phone': '+263777654321',
            'address_line_1': '456 Oak Ave',
            'city': 'Bulawayo',
            'country': 'Zimbabwe',
            'payment_method': 'manual_cash',
        }
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.user)
        serializer = RetailerOrderCreationSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        
        # Check order was created
        order = result['order']
        self.assertIsNotNone(order)
        self.assertEqual(order.amount, self.package.price)
        self.assertEqual(order.stage, Order.Stage.CLOSED_WON)
        self.assertEqual(order.payment_method, 'manual_cash')
        
        # Check order items were created
        order_items = order.items.all()
        self.assertEqual(order_items.count(), 2)  # inverter + panels
        
        # Check that quantities match package
        inverter_item = order_items.get(product=self.inverter)
        self.assertEqual(inverter_item.quantity, 1)
        
        panel_item = order_items.get(product=self.panel)
        self.assertEqual(panel_item.quantity, 10)
    
    def test_order_creation_creates_installation_request(self):
        """Test that order creation creates an installation request"""
        from customer_data.serializers import RetailerOrderCreationSerializer
        
        data = {
            'solar_package_id': self.package.id,
            'customer_first_name': 'Bob',
            'customer_last_name': 'Johnson',
            'customer_phone': '+263772345678',
            'address_line_1': '789 Pine Rd',
            'city': 'Mutare',
            'country': 'Zimbabwe',
            'payment_method': 'paynow_onemoney',
            'latitude': Decimal('-18.9707'),
            'longitude': Decimal('32.6703'),
        }
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.user)
        serializer = RetailerOrderCreationSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()
        
        # Check installation request was created
        installation_request = result['installation_request']
        self.assertIsNotNone(installation_request)
        self.assertEqual(installation_request.installation_type, 'solar')
        self.assertEqual(installation_request.status, 'pending')
        self.assertEqual(installation_request.full_name, 'Bob Johnson')
        self.assertEqual(installation_request.location_latitude, Decimal('-18.9707'))
        self.assertEqual(installation_request.location_longitude, Decimal('32.6703'))
    
    def test_invalid_phone_number_fails_validation(self):
        """Test that invalid phone number fails validation"""
        from customer_data.serializers import RetailerOrderCreationSerializer
        
        data = {
            'solar_package_id': self.package.id,
            'customer_first_name': 'Test',
            'customer_last_name': 'User',
            'customer_phone': 'invalid',  # Invalid phone
            'address_line_1': '123 Test St',
            'city': 'Test City',
            'country': 'Zimbabwe',
            'payment_method': 'manual_cash',
        }
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.user)
        serializer = RetailerOrderCreationSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('customer_phone', serializer.errors)
    
    def test_inactive_package_fails_validation(self):
        """Test that inactive package fails validation"""
        from customer_data.serializers import RetailerOrderCreationSerializer
        
        # Create inactive package
        inactive_package = SolarPackage.objects.create(
            name='Inactive Package',
            system_size=Decimal('3.0'),
            price=Decimal('5000.00'),
            is_active=False
        )
        
        data = {
            'solar_package_id': inactive_package.id,
            'customer_first_name': 'Test',
            'customer_last_name': 'User',
            'customer_phone': '+263771111111',
            'address_line_1': '123 Test St',
            'city': 'Test City',
            'country': 'Zimbabwe',
            'payment_method': 'manual_cash',
        }
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.user)
        serializer = RetailerOrderCreationSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('solar_package_id', serializer.errors)
