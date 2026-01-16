# whatsappcrm_backend/users/test_retailer_portal.py
"""
Tests for retailer portal - Installation & Warranty Tracking
Tests access control, filtering, and read-only access.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from users.models import Retailer, RetailerBranch
from warranty.models import Warranty, WarrantyClaim, Manufacturer, Technician
from customer_data.models import CustomerProfile, Order, OrderItem
from conversations.models import Contact
from products_and_services.models import Product, SerializedItem
from installation_systems.models import (
    InstallationSystemRecord,
    CommissioningChecklistTemplate,
    InstallationChecklistEntry,
)

User = get_user_model()


class RetailerInstallationTrackingTests(APITestCase):
    """Test installation tracking for retailers"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create retailer 1
        self.retailer1_user = User.objects.create_user(
            username='retailer1',
            email='retailer1@test.com',
            password='testpass123'
        )
        self.retailer1 = Retailer.objects.create(
            user=self.retailer1_user,
            company_name='Test Retailer 1',
            is_active=True
        )
        
        # Create retailer 2
        self.retailer2_user = User.objects.create_user(
            username='retailer2',
            email='retailer2@test.com',
            password='testpass123'
        )
        self.retailer2 = Retailer.objects.create(
            user=self.retailer2_user,
            company_name='Test Retailer 2',
            is_active=True
        )
        
        # Create retailer branch for retailer 1
        self.branch_user = User.objects.create_user(
            username='branch1',
            email='branch1@test.com',
            password='testpass123'
        )
        self.branch = RetailerBranch.objects.create(
            user=self.branch_user,
            retailer=self.retailer1,
            branch_name='Branch 1',
            is_active=True
        )
        
        # Create contact and customer
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer',
            email='test@customer.com'
        )
        
        # Create product
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='product',
            price=Decimal('150.00')
        )
        
        # Create order for retailer 1
        self.order1 = Order.objects.create(
            customer=self.customer,
            order_number='ORD-001',
            stage='closed_won',
            notes=f"Ordered by retailer: {self.retailer1.company_name}",
            acquisition_source=f"Retailer: {self.retailer1.company_name}"
        )
        
        # Create order for retailer 2
        self.order2 = Order.objects.create(
            customer=self.customer,
            order_number='ORD-002',
            stage='closed_won',
            notes=f"Ordered by retailer: {self.retailer2.company_name}",
            acquisition_source=f"Retailer: {self.retailer2.company_name}"
        )
        
        # Create installation for retailer 1's order
        self.installation1 = InstallationSystemRecord.objects.create(
            customer=self.customer,
            order=self.order1,
            installation_type='solar',
            system_size=Decimal('5.0'),
            capacity_unit='kW',
            system_classification='residential',
            installation_status='pending',
            installation_address='123 Test St'
        )
        
        # Create installation for retailer 2's order
        self.installation2 = InstallationSystemRecord.objects.create(
            customer=self.customer,
            order=self.order2,
            installation_type='starlink',
            system_size=Decimal('100'),
            capacity_unit='Mbps',
            system_classification='residential',
            installation_status='completed',
            installation_address='456 Test Ave'
        )
        
        self.client = APIClient()
    
    def test_retailer_can_view_own_installations(self):
        """Test that retailer can view their own installations"""
        self.client.force_authenticate(user=self.retailer1_user)
        
        url = reverse('users_api:retailer-installation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['order_number'], 'ORD-001')
    
    def test_retailer_cannot_view_other_retailer_installations(self):
        """Test that retailer cannot view installations from other retailers"""
        self.client.force_authenticate(user=self.retailer1_user)
        
        url = reverse('users_api:retailer-installation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see their own installation, not retailer2's
        order_numbers = [inst['order_number'] for inst in response.data['results']]
        self.assertIn('ORD-001', order_numbers)
        self.assertNotIn('ORD-002', order_numbers)
    
    def test_retailer_branch_can_view_parent_retailer_installations(self):
        """Test that retailer branch can view parent retailer's installations"""
        self.client.force_authenticate(user=self.branch_user)
        
        url = reverse('users_api:retailer-installation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['order_number'], 'ORD-001')
    
    def test_installation_detail_view(self):
        """Test installation detail view"""
        self.client.force_authenticate(user=self.retailer1_user)
        
        url = reverse('users_api:retailer-installation-detail', kwargs={'pk': self.installation1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('customer_info', response.data)
        self.assertIn('system_details', response.data)
        self.assertIn('installation_progress', response.data)
        self.assertEqual(response.data['customer_info']['name'], 'Test Customer')
    
    def test_filter_by_status(self):
        """Test filtering installations by status"""
        self.client.force_authenticate(user=self.retailer1_user)
        
        url = reverse('users_api:retailer-installation-list')
        response = self.client.get(url, {'installation_status': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['installation_status'], 'pending')
    
    def test_search_installations(self):
        """Test searching installations"""
        self.client.force_authenticate(user=self.retailer1_user)
        
        url = reverse('users_api:retailer-installation-list')
        response = self.client.get(url, {'search': 'Test Customer'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_summary_stats(self):
        """Test summary statistics endpoint"""
        self.client.force_authenticate(user=self.retailer1_user)
        
        url = reverse('users_api:retailer-installation-summary-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_installations', response.data)
        self.assertIn('by_status', response.data)
        self.assertEqual(response.data['total_installations'], 1)
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access installations"""
        url = reverse('users_api:retailer-installation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_non_retailer_access_denied(self):
        """Test that non-retailer users cannot access installations"""
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=regular_user)
        
        url = reverse('users_api:retailer-installation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RetailerWarrantyTrackingTests(APITestCase):
    """Test warranty tracking for retailers"""
    
    def setUp(self):
        """Set up test data"""
        # Create retailer
        self.retailer_user = User.objects.create_user(
            username='retailer',
            email='retailer@test.com',
            password='testpass123'
        )
        self.retailer = Retailer.objects.create(
            user=self.retailer_user,
            company_name='Test Retailer',
            is_active=True
        )
        
        # Create another retailer
        self.retailer2_user = User.objects.create_user(
            username='retailer2',
            email='retailer2@test.com',
            password='testpass123'
        )
        self.retailer2 = Retailer.objects.create(
            user=self.retailer2_user,
            company_name='Test Retailer 2',
            is_active=True
        )
        
        # Create contact and customer
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer',
            email='test@customer.com'
        )
        
        # Create manufacturer
        self.manufacturer = Manufacturer.objects.create(
            name='Test Manufacturer',
            contact_email='manufacturer@test.com'
        )
        
        # Create product and serialized item
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='product',
            price=Decimal('150.00')
        )
        self.serialized_item1 = SerializedItem.objects.create(
            product=self.product,
            serial_number='SN123456789',
            barcode='BC123456789',
            status='sold'
        )
        self.serialized_item2 = SerializedItem.objects.create(
            product=self.product,
            serial_number='SN987654321',
            barcode='BC987654321',
            status='sold'
        )
        
        # Create orders
        self.order1 = Order.objects.create(
            customer=self.customer,
            order_number='ORD-001',
            stage='closed_won',
            notes=f"Ordered by retailer: {self.retailer.company_name}"
        )
        self.order2 = Order.objects.create(
            customer=self.customer,
            order_number='ORD-002',
            stage='closed_won',
            notes=f"Ordered by retailer: {self.retailer2.company_name}"
        )
        
        # Create warranties
        today = datetime.now().date()
        self.warranty1 = Warranty.objects.create(
            manufacturer=self.manufacturer,
            serialized_item=self.serialized_item1,
            customer=self.customer,
            associated_order=self.order1,
            start_date=today,
            end_date=today + timedelta(days=365),
            status='active'
        )
        self.warranty2 = Warranty.objects.create(
            manufacturer=self.manufacturer,
            serialized_item=self.serialized_item2,
            customer=self.customer,
            associated_order=self.order2,
            start_date=today,
            end_date=today + timedelta(days=365),
            status='active'
        )
        
        # Create warranty claim for warranty1
        self.claim = WarrantyClaim.objects.create(
            warranty=self.warranty1,
            claim_id='CLM-001',
            description_of_fault='Panel not working',
            status='pending'
        )
        
        self.client = APIClient()
    
    def test_retailer_can_view_own_warranties(self):
        """Test that retailer can view their own warranties"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-warranty-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['product_serial_number'], 'SN123456789')
    
    def test_retailer_cannot_view_other_retailer_warranties(self):
        """Test that retailer cannot view warranties from other retailers"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-warranty-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serial_numbers = [w['product_serial_number'] for w in response.data['results']]
        self.assertIn('SN123456789', serial_numbers)
        self.assertNotIn('SN987654321', serial_numbers)
    
    def test_warranty_detail_view(self):
        """Test warranty detail view"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-warranty-detail', kwargs={'pk': self.warranty1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('product_info', response.data)
        self.assertIn('customer_info', response.data)
        self.assertIn('warranty_details', response.data)
        self.assertIn('claims', response.data)
        self.assertEqual(len(response.data['claims']), 1)
    
    def test_filter_by_status(self):
        """Test filtering warranties by status"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-warranty-list')
        response = self.client.get(url, {'status': 'active'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'active')
    
    def test_filter_has_active_claims(self):
        """Test filtering warranties with active claims"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-warranty-list')
        response = self.client.get(url, {'has_active_claims': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_warranty_summary_stats(self):
        """Test warranty summary statistics"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-warranty-summary-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_warranties', response.data)
        self.assertIn('active', response.data)
        self.assertEqual(response.data['total_warranties'], 1)
        self.assertEqual(response.data['active'], 1)
    
    def test_warranty_claims_endpoint(self):
        """Test getting claims for a specific warranty"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-warranty-claims', kwargs={'pk': self.warranty1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('claims', response.data)
        self.assertEqual(len(response.data['claims']), 1)
        self.assertEqual(response.data['claims'][0]['claim_id'], 'CLM-001')


class RetailerProductMovementTests(APITestCase):
    """Test product movement tracking for retailers"""
    
    def setUp(self):
        """Set up test data"""
        # Create retailer
        self.retailer_user = User.objects.create_user(
            username='retailer',
            email='retailer@test.com',
            password='testpass123'
        )
        self.retailer = Retailer.objects.create(
            user=self.retailer_user,
            company_name='Test Retailer',
            is_active=True
        )
        
        # Create contact and customer
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer'
        )
        
        # Create product
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='product',
            price=Decimal('150.00')
        )
        
        # Create order
        self.order = Order.objects.create(
            customer=self.customer,
            order_number='ORD-001',
            stage='closed_won',
            notes=f"Ordered by retailer: {self.retailer.company_name}"
        )
        
        # Create order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('150.00')
        )
        
        # Create serialized item
        self.serialized_item = SerializedItem.objects.create(
            product=self.product,
            order_item=self.order_item,
            serial_number='SN123456789',
            barcode='BC123456789',
            status='sold',
            location='customer'
        )
        
        self.client = APIClient()
    
    def test_retailer_can_view_product_movements(self):
        """Test that retailer can view product movements"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-product-movement-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['serial_number'], 'SN123456789')
    
    def test_filter_by_status(self):
        """Test filtering product movements by status"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-product-movement-list')
        response = self.client.get(url, {'status': 'sold'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_by_location(self):
        """Test filtering product movements by location"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-product-movement-list')
        response = self.client.get(url, {'location': 'customer'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_search_by_serial_number(self):
        """Test searching by serial number"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-product-movement-list')
        response = self.client.get(url, {'search': 'SN123456789'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_product_movement_summary_stats(self):
        """Test product movement summary statistics"""
        self.client.force_authenticate(user=self.retailer_user)
        
        url = reverse('users_api:retailer-product-movement-summary-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_items', response.data)
        self.assertIn('by_status', response.data)
        self.assertIn('by_location', response.data)
        self.assertEqual(response.data['total_items'], 1)
