from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Product, ProductCategory, SerializedItem

User = get_user_model()


class BarcodeScanAPITestCase(TestCase):
    """
    Test cases for barcode scanning API endpoints
    """
    
    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test category
        self.category = ProductCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            sku='TEST-SKU-001',
            barcode='123456789',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            sku='TEST-SKU-002',
            description='Test product without barcode',
            product_type='software',
            price=50.00,
            currency='USD',
            stock_quantity=5
        )
        
        # Create test serialized item
        self.serialized_item = SerializedItem.objects.create(
            product=self.product1,
            serial_number='SN-12345',
            barcode='987654321',
            status='in_stock'
        )
    
    def test_scan_product_by_barcode_success(self):
        """Test scanning a product by barcode successfully"""
        response = self.client.post(
            '/crm-api/products/barcode/scan/',
            {
                'barcode': '123456789',
                'scan_type': 'product'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['found'])
        self.assertEqual(response.data['item_type'], 'product')
        self.assertEqual(response.data['data']['name'], 'Test Product 1')
        self.assertEqual(response.data['data']['barcode'], '123456789')
    
    def test_scan_product_by_sku_fallback(self):
        """Test scanning a product by SKU when barcode not found"""
        response = self.client.post(
            '/crm-api/products/barcode/scan/',
            {
                'barcode': 'TEST-SKU-002',
                'scan_type': 'product'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['found'])
        self.assertEqual(response.data['item_type'], 'product')
        self.assertEqual(response.data['data']['name'], 'Test Product 2')
        self.assertIn('SKU', response.data['message'])
    
    def test_scan_serialized_item_by_barcode_success(self):
        """Test scanning a serialized item by barcode successfully"""
        response = self.client.post(
            '/crm-api/products/barcode/scan/',
            {
                'barcode': '987654321',
                'scan_type': 'serialized_item'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['found'])
        self.assertEqual(response.data['item_type'], 'serialized_item')
        self.assertEqual(response.data['data']['serial_number'], 'SN-12345')
        self.assertEqual(response.data['data']['barcode'], '987654321')
    
    def test_scan_serialized_item_by_serial_number_fallback(self):
        """Test scanning a serialized item by serial number when barcode not found"""
        response = self.client.post(
            '/crm-api/products/barcode/scan/',
            {
                'barcode': 'SN-12345',
                'scan_type': 'serialized_item'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['found'])
        self.assertEqual(response.data['item_type'], 'serialized_item')
        self.assertIn('serial number', response.data['message'])
    
    def test_scan_barcode_not_found(self):
        """Test scanning a barcode that doesn't exist"""
        response = self.client.post(
            '/crm-api/products/barcode/scan/',
            {
                'barcode': 'NONEXISTENT-BARCODE',
                'scan_type': 'product'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['found'])
        self.assertIsNone(response.data['item_type'])
        self.assertIsNone(response.data['data'])
    
    def test_scan_barcode_missing_required_field(self):
        """Test scanning without required barcode field"""
        response = self.client.post(
            '/crm-api/products/barcode/scan/',
            {
                'scan_type': 'product'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_lookup_barcode_multiple_results(self):
        """Test flexible barcode lookup that returns multiple results"""
        # Create another product with same barcode
        product3 = Product.objects.create(
            name='Test Product 3',
            sku='111222333',
            description='Another test product',
            product_type='hardware',
            price=75.00,
            currency='USD',
            stock_quantity=3
        )
        
        response = self.client.post(
            '/crm-api/products/barcode/lookup/',
            {
                'barcode': '123456789'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['found'])
        self.assertGreaterEqual(response.data['count'], 1)
        self.assertIsInstance(response.data['results'], list)
    
    def test_lookup_barcode_no_results(self):
        """Test flexible barcode lookup with no results"""
        response = self.client.post(
            '/crm-api/products/barcode/lookup/',
            {
                'barcode': 'NONEXISTENT'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['found'])
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_lookup_barcode_missing_field(self):
        """Test lookup without required barcode field"""
        response = self.client.post(
            '/crm-api/products/barcode/lookup/',
            {},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_scan_barcode_unauthenticated(self):
        """Test that unauthenticated users cannot scan barcodes"""
        self.client.force_authenticate(user=None)
        
        response = self.client.post(
            '/crm-api/products/barcode/scan/',
            {
                'barcode': '123456789',
                'scan_type': 'product'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BarcodeModelTestCase(TestCase):
    """
    Test cases for barcode fields in models
    """
    
    def test_product_barcode_uniqueness(self):
        """Test that product barcodes must be unique"""
        category = ProductCategory.objects.create(name='Test Category')
        
        Product.objects.create(
            name='Product 1',
            barcode='UNIQUE-BARCODE-1',
            product_type='hardware',
            category=category
        )
        
        # Attempting to create another product with same barcode should fail
        with self.assertRaises(Exception):
            Product.objects.create(
                name='Product 2',
                barcode='UNIQUE-BARCODE-1',
                product_type='software',
                category=category
            )
    
    def test_serialized_item_barcode_uniqueness(self):
        """Test that serialized item barcodes must be unique"""
        category = ProductCategory.objects.create(name='Test Category')
        product = Product.objects.create(
            name='Test Product',
            product_type='hardware',
            category=category
        )
        
        SerializedItem.objects.create(
            product=product,
            serial_number='SN-001',
            barcode='ITEM-BARCODE-1'
        )
        
        # Attempting to create another item with same barcode should fail
        with self.assertRaises(Exception):
            SerializedItem.objects.create(
                product=product,
                serial_number='SN-002',
                barcode='ITEM-BARCODE-1'
            )
    
    def test_product_can_have_null_barcode(self):
        """Test that products can have null barcodes"""
        category = ProductCategory.objects.create(name='Test Category')
        
        product = Product.objects.create(
            name='Product Without Barcode',
            product_type='service',
            category=category
        )
        
        self.assertIsNone(product.barcode)
    
    def test_serialized_item_can_have_null_barcode(self):
        """Test that serialized items can have null barcodes"""
        category = ProductCategory.objects.create(name='Test Category')
        product = Product.objects.create(
            name='Test Product',
            product_type='hardware',
            category=category
        )
        
        item = SerializedItem.objects.create(
            product=product,
            serial_number='SN-003'
        )
        
        self.assertIsNone(item.barcode)
