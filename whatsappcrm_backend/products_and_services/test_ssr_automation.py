"""
Tests for automatic SSR creation on solar package purchase.
Tests the signal handler and automation service.
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from products_and_services.models import (
    Product, SolarPackage, SolarPackageProduct, 
    ProductCategory, CompatibilityRule
)
from customer_data.models import Order, OrderItem, CustomerProfile, InstallationRequest
from installation_systems.models import InstallationSystemRecord
from warranty.models import Warranty, Manufacturer, WarrantyRule
from conversations.models import Contact
from products_and_services.services import (
    CompatibilityValidationService,
    SolarOrderAutomationService
)

User = get_user_model()


class CompatibilityRuleModelTest(TestCase):
    """Test cases for CompatibilityRule model"""
    
    def setUp(self):
        """Set up test data"""
        self.category = ProductCategory.objects.create(name='Solar Equipment')
        
        self.inverter = Product.objects.create(
            name='5kW Inverter',
            sku='INV-5KW',
            product_type='hardware',
            category=self.category,
            price=Decimal('1500.00'),
            is_active=True
        )
        
        self.battery = Product.objects.create(
            name='5kWh Battery',
            sku='BAT-5KWH',
            product_type='hardware',
            category=self.category,
            price=Decimal('2500.00'),
            is_active=True
        )
    
    def test_create_compatibility_rule(self):
        """Test creating a compatibility rule"""
        rule = CompatibilityRule.objects.create(
            name='5kW Inverter compatible with 5kWh Battery',
            product_a=self.inverter,
            product_b=self.battery,
            rule_type=CompatibilityRule.RuleType.COMPATIBLE,
            description='These products work well together',
            is_active=True
        )
        
        self.assertEqual(rule.name, '5kW Inverter compatible with 5kWh Battery')
        self.assertEqual(rule.product_a, self.inverter)
        self.assertEqual(rule.product_b, self.battery)
        self.assertEqual(rule.rule_type, CompatibilityRule.RuleType.COMPATIBLE)
        self.assertTrue(rule.is_active)
    
    def test_incompatibility_rule(self):
        """Test creating an incompatibility rule"""
        wrong_battery = Product.objects.create(
            name='3kWh Battery',
            sku='BAT-3KWH',
            product_type='hardware',
            price=Decimal('1800.00')
        )
        
        rule = CompatibilityRule.objects.create(
            name='5kW Inverter incompatible with 3kWh Battery',
            product_a=self.inverter,
            product_b=wrong_battery,
            rule_type=CompatibilityRule.RuleType.INCOMPATIBLE,
            description='Battery capacity too small for inverter',
            is_active=True
        )
        
        self.assertEqual(rule.rule_type, CompatibilityRule.RuleType.INCOMPATIBLE)
    
    def test_unique_constraint(self):
        """Test that duplicate compatibility rules are prevented"""
        CompatibilityRule.objects.create(
            name='Test Rule',
            product_a=self.inverter,
            product_b=self.battery,
            rule_type=CompatibilityRule.RuleType.COMPATIBLE
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CompatibilityRule.objects.create(
                name='Duplicate Rule',
                product_a=self.inverter,
                product_b=self.battery,
                rule_type=CompatibilityRule.RuleType.COMPATIBLE
            )


class CompatibilityValidationServiceTest(TestCase):
    """Test cases for CompatibilityValidationService"""
    
    def setUp(self):
        """Set up test data"""
        self.category = ProductCategory.objects.create(name='Solar Equipment')
        
        self.inverter = Product.objects.create(
            name='5kW Inverter',
            sku='INV-5KW',
            product_type='hardware',
            price=Decimal('1500.00')
        )
        
        self.compatible_battery = Product.objects.create(
            name='5kWh Battery',
            sku='BAT-5KWH',
            product_type='hardware',
            price=Decimal('2500.00')
        )
        
        self.incompatible_battery = Product.objects.create(
            name='1kWh Battery',
            sku='BAT-1KWH',
            product_type='hardware',
            price=Decimal('800.00')
        )
        
        # Create compatibility rules
        CompatibilityRule.objects.create(
            name='Compatible',
            product_a=self.inverter,
            product_b=self.compatible_battery,
            rule_type=CompatibilityRule.RuleType.COMPATIBLE,
            is_active=True
        )
        
        CompatibilityRule.objects.create(
            name='Incompatible',
            product_a=self.inverter,
            product_b=self.incompatible_battery,
            rule_type=CompatibilityRule.RuleType.INCOMPATIBLE,
            description='Battery too small for inverter',
            is_active=True
        )
    
    def test_check_compatible_products(self):
        """Test checking compatible products"""
        result = CompatibilityValidationService.check_product_compatibility(
            self.inverter, self.compatible_battery
        )
        
        self.assertTrue(result['compatible'])
        self.assertIn('Compatible', result['reason'])
        self.assertIsNotNone(result['rule'])
    
    def test_check_incompatible_products(self):
        """Test checking incompatible products"""
        result = CompatibilityValidationService.check_product_compatibility(
            self.inverter, self.incompatible_battery
        )
        
        self.assertFalse(result['compatible'])
        self.assertIn('Incompatible', result['reason'])
        self.assertIsNotNone(result['rule'])
    
    def test_check_products_no_rule(self):
        """Test checking products with no explicit rule"""
        unrelated_product = Product.objects.create(
            name='Cable',
            sku='CABLE-001',
            product_type='hardware',
            price=Decimal('50.00')
        )
        
        result = CompatibilityValidationService.check_product_compatibility(
            self.inverter, unrelated_product
        )
        
        self.assertTrue(result['compatible'])
        self.assertTrue(result.get('warning', False))
        self.assertIsNone(result['rule'])
    
    def test_validate_solar_package(self):
        """Test validating a solar package"""
        package = SolarPackage.objects.create(
            name='5kW System',
            system_size=Decimal('5.0'),
            price=Decimal('8000.00')
        )
        
        SolarPackageProduct.objects.create(
            solar_package=package,
            product=self.inverter,
            quantity=1
        )
        
        SolarPackageProduct.objects.create(
            solar_package=package,
            product=self.compatible_battery,
            quantity=2
        )
        
        result = CompatibilityValidationService.validate_solar_package(package)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_incompatible_package(self):
        """Test validating a package with incompatible products"""
        package = SolarPackage.objects.create(
            name='Invalid System',
            system_size=Decimal('5.0'),
            price=Decimal('5000.00')
        )
        
        SolarPackageProduct.objects.create(
            solar_package=package,
            product=self.inverter,
            quantity=1
        )
        
        SolarPackageProduct.objects.create(
            solar_package=package,
            product=self.incompatible_battery,
            quantity=1
        )
        
        result = CompatibilityValidationService.validate_solar_package(package)
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)


class SSRAutomationServiceTest(TransactionTestCase):
    """Test cases for automatic SSR creation service"""
    
    def setUp(self):
        """Set up test data"""
        # Create manufacturer
        self.manufacturer = Manufacturer.objects.create(
            name='Test Solar Co'
        )
        
        # Create products
        self.category = ProductCategory.objects.create(name='Solar Equipment')
        
        self.inverter = Product.objects.create(
            name='5kW Inverter',
            sku='INV-5KW',
            product_type='hardware',
            category=self.category,
            price=Decimal('1500.00'),
            manufacturer=self.manufacturer,
            is_active=True
        )
        
        self.battery = Product.objects.create(
            name='5kWh Battery',
            sku='BAT-5KWH',
            product_type='hardware',
            category=self.category,
            price=Decimal('2500.00'),
            manufacturer=self.manufacturer,
            is_active=True
        )
        
        self.panel = Product.objects.create(
            name='550W Panel',
            sku='PANEL-550W',
            product_type='hardware',
            category=self.category,
            price=Decimal('250.00'),
            manufacturer=self.manufacturer,
            is_active=True
        )
        
        # Create solar package
        self.package = SolarPackage.objects.create(
            name='5kW Complete System',
            system_size=Decimal('5.0'),
            price=Decimal('8000.00'),
            is_active=True
        )
        
        SolarPackageProduct.objects.create(
            solar_package=self.package,
            product=self.inverter,
            quantity=1
        )
        
        SolarPackageProduct.objects.create(
            solar_package=self.package,
            product=self.battery,
            quantity=2
        )
        
        SolarPackageProduct.objects.create(
            solar_package=self.package,
            product=self.panel,
            quantity=10
        )
        
        # Create customer
        contact = Contact.objects.create(whatsapp_id='+263771234567')
        self.customer = CustomerProfile.objects.create(
            contact=contact,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            address_line_1='123 Main St',
            city='Harare',
            country='Zimbabwe'
        )
        
        # Create warranty rule
        WarrantyRule.objects.create(
            name='Standard Solar Equipment',
            product_category=self.category,
            warranty_duration_days=730,  # 2 years
            is_active=True,
            priority=1
        )
    
    def test_create_ssr_from_order(self):
        """Test creating SSR from a solar order"""
        # Create order
        order = Order.objects.create(
            customer=self.customer,
            stage=Order.Stage.CLOSED_WON,
            payment_status=Order.PaymentStatus.PAID,
            amount=self.package.price,
            order_number='TEST-001'
        )
        
        # Add order items
        OrderItem.objects.create(
            order=order,
            product=self.inverter,
            quantity=1,
            unit_price=self.inverter.price,
            total_amount=self.inverter.price
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.battery,
            quantity=2,
            unit_price=self.battery.price,
            total_amount=self.battery.price * 2
        )
        
        # Call automation service
        result = SolarOrderAutomationService.create_ssr_from_order(order)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['ssr'])
        self.assertIsNotNone(result['installation_request'])
        self.assertEqual(len(result['errors']), 0)
        
        # Verify SSR was created
        ssr = result['ssr']
        self.assertEqual(ssr.customer, self.customer)
        self.assertEqual(ssr.order, order)
        self.assertEqual(ssr.installation_type, InstallationSystemRecord.InstallationType.SOLAR)
        self.assertEqual(ssr.system_size, self.package.system_size)
        self.assertEqual(ssr.installation_status, InstallationSystemRecord.InstallationStatus.PENDING)
        
        # Verify installation request
        installation_request = result['installation_request']
        self.assertEqual(installation_request.customer, self.customer)
        self.assertEqual(installation_request.associated_order, order)
        self.assertEqual(installation_request.installation_type, 'solar')
        self.assertEqual(installation_request.status, 'pending')
    
    def test_idempotency_prevents_duplicate_ssr(self):
        """Test that calling automation twice doesn't create duplicate SSR"""
        order = Order.objects.create(
            customer=self.customer,
            stage=Order.Stage.CLOSED_WON,
            payment_status=Order.PaymentStatus.PAID,
            amount=self.package.price,
            order_number='TEST-002'
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.inverter,
            quantity=1,
            unit_price=self.inverter.price,
            total_amount=self.inverter.price
        )
        
        # First call
        result1 = SolarOrderAutomationService.create_ssr_from_order(order)
        self.assertTrue(result1['success'])
        ssr1_id = result1['ssr'].id
        
        # Second call
        result2 = SolarOrderAutomationService.create_ssr_from_order(order)
        self.assertFalse(result2['success'])
        self.assertIn('already exists', result2['errors'][0])
        self.assertEqual(result2['ssr'].id, ssr1_id)
        
        # Verify only one SSR exists
        ssr_count = InstallationSystemRecord.objects.filter(order=order).count()
        self.assertEqual(ssr_count, 1)
    
    def test_non_solar_order_skipped(self):
        """Test that non-solar orders are skipped"""
        # Create a non-solar product
        software = Product.objects.create(
            name='Software License',
            sku='SW-001',
            product_type='software',
            price=Decimal('500.00')
        )
        
        order = Order.objects.create(
            customer=self.customer,
            stage=Order.Stage.CLOSED_WON,
            payment_status=Order.PaymentStatus.PAID,
            amount=software.price,
            order_number='TEST-003'
        )
        
        OrderItem.objects.create(
            order=order,
            product=software,
            quantity=1,
            unit_price=software.price,
            total_amount=software.price
        )
        
        result = SolarOrderAutomationService.create_ssr_from_order(order)
        
        self.assertFalse(result['success'])
        self.assertIn('No solar products', result['errors'][0])
        self.assertIsNone(result['ssr'])
    
    def test_compatibility_validation_failure(self):
        """Test that incompatible packages are flagged"""
        # Create incompatible products
        small_battery = Product.objects.create(
            name='1kWh Battery',
            sku='BAT-1KWH',
            product_type='hardware',
            price=Decimal('800.00')
        )
        
        # Add incompatibility rule
        CompatibilityRule.objects.create(
            name='Incompatible',
            product_a=self.inverter,
            product_b=small_battery,
            rule_type=CompatibilityRule.RuleType.INCOMPATIBLE,
            description='Battery too small',
            is_active=True
        )
        
        # Create bad package
        bad_package = SolarPackage.objects.create(
            name='Bad System',
            system_size=Decimal('5.0'),
            price=Decimal('5000.00')
        )
        
        SolarPackageProduct.objects.create(
            solar_package=bad_package,
            product=self.inverter,
            quantity=1
        )
        
        SolarPackageProduct.objects.create(
            solar_package=bad_package,
            product=small_battery,
            quantity=1
        )
        
        order = Order.objects.create(
            customer=self.customer,
            stage=Order.Stage.CLOSED_WON,
            payment_status=Order.PaymentStatus.PAID,
            amount=bad_package.price,
            order_number='TEST-004'
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.inverter,
            quantity=1,
            unit_price=self.inverter.price,
            total_amount=self.inverter.price
        )
        
        OrderItem.objects.create(
            order=order,
            product=small_battery,
            quantity=1,
            unit_price=small_battery.price,
            total_amount=small_battery.price
        )
        
        result = SolarOrderAutomationService.create_ssr_from_order(order)
        
        self.assertFalse(result['success'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIsNone(result['ssr'])


class SSRSignalHandlerTest(TransactionTestCase):
    """Test cases for the SSR creation signal handler"""
    
    def setUp(self):
        """Set up test data"""
        self.manufacturer = Manufacturer.objects.create(name='Test Solar Co')
        self.category = ProductCategory.objects.create(name='Solar Equipment')
        
        self.inverter = Product.objects.create(
            name='5kW Inverter',
            sku='INV-5KW',
            product_type='hardware',
            category=self.category,
            price=Decimal('1500.00'),
            manufacturer=self.manufacturer
        )
        
        self.package = SolarPackage.objects.create(
            name='5kW System',
            system_size=Decimal('5.0'),
            price=Decimal('8000.00')
        )
        
        SolarPackageProduct.objects.create(
            solar_package=self.package,
            product=self.inverter,
            quantity=1
        )
        
        contact = Contact.objects.create(whatsapp_id='+263777777777')
        self.customer = CustomerProfile.objects.create(
            contact=contact,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            address_line_1='Test Address',
            city='Test City',
            country='Test Country'
        )
    
    def test_signal_creates_ssr_on_paid_order(self):
        """Test that signal automatically creates SSR when order is paid"""
        # Create order with paid status
        order = Order.objects.create(
            customer=self.customer,
            stage=Order.Stage.CLOSED_WON,
            payment_status=Order.PaymentStatus.PAID,
            amount=self.package.price,
            order_number='SIGNAL-TEST-001'
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.inverter,
            quantity=1,
            unit_price=self.inverter.price,
            total_amount=self.inverter.price
        )
        
        # Manually trigger save to fire signal
        order.save()
        
        # Check if SSR was created
        ssr = InstallationSystemRecord.objects.filter(order=order).first()
        self.assertIsNotNone(ssr)
        self.assertEqual(ssr.customer, self.customer)
        self.assertEqual(ssr.installation_type, InstallationSystemRecord.InstallationType.SOLAR)
    
    def test_signal_skips_unpaid_orders(self):
        """Test that signal doesn't create SSR for unpaid orders"""
        order = Order.objects.create(
            customer=self.customer,
            stage=Order.Stage.CLOSED_WON,
            payment_status=Order.PaymentStatus.PENDING,  # Not paid
            amount=self.package.price,
            order_number='SIGNAL-TEST-002'
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.inverter,
            quantity=1,
            unit_price=self.inverter.price,
            total_amount=self.inverter.price
        )
        
        order.save()
        
        # Check that no SSR was created
        ssr_count = InstallationSystemRecord.objects.filter(order=order).count()
        self.assertEqual(ssr_count, 0)
    
    def test_signal_skips_non_closed_won_orders(self):
        """Test that signal doesn't create SSR for non-closed-won orders"""
        order = Order.objects.create(
            customer=self.customer,
            stage=Order.Stage.PROPOSAL,  # Not closed won
            payment_status=Order.PaymentStatus.PAID,
            amount=self.package.price,
            order_number='SIGNAL-TEST-003'
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.inverter,
            quantity=1,
            unit_price=self.inverter.price,
            total_amount=self.inverter.price
        )
        
        order.save()
        
        # Check that no SSR was created
        ssr_count = InstallationSystemRecord.objects.filter(order=order).count()
        self.assertEqual(ssr_count, 0)
