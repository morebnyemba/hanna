from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
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


class ProductMetaCatalogSyncTestCase(TestCase):
    """
    Test cases for Product synchronization with Meta Catalog via signals.
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = ProductCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_product_creation_triggers_catalog_sync(self, mock_service_class):
        """Test that creating a product triggers Meta Catalog sync"""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_123'}
        
        # Create a product
        product = Product.objects.create(
            name='Test Product',
            sku='TEST-SKU-001',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True
        )
        
        # Verify catalog service was called
        mock_service.create_product_in_catalog.assert_called_once_with(product)
        
        # Verify the product was updated with catalog ID
        product.refresh_from_db()
        self.assertEqual(product.whatsapp_catalog_id, 'meta_catalog_123')
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_product_update_triggers_catalog_sync(self, mock_service_class):
        """Test that updating a product triggers Meta Catalog update"""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_123'}
        mock_service.update_product_in_catalog.return_value = {'success': True}
        
        # Create a product (this triggers create signal)
        product = Product.objects.create(
            name='Test Product',
            sku='TEST-SKU-002',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True,
            whatsapp_catalog_id='meta_catalog_123'
        )
        
        # Reset mock to clear creation call
        mock_service.reset_mock()
        
        # Update the product (this triggers update signal)
        product.price = 150.00
        product.save()
        
        # Verify update was called
        mock_service.update_product_in_catalog.assert_called_once_with(product)
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_product_without_sku_skips_sync(self, mock_service_class):
        """Test that products without SKU are not synced"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Create a product without SKU
        product = Product.objects.create(
            name='Test Product No SKU',
            description='Test product description',
            product_type='service',
            category=self.category,
            price=100.00,
            currency='USD',
            is_active=True
        )
        
        # Verify catalog service was NOT called
        mock_service.create_product_in_catalog.assert_not_called()
        mock_service.update_product_in_catalog.assert_not_called()
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_inactive_product_skips_sync(self, mock_service_class):
        """Test that inactive products are not synced"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Create an inactive product
        product = Product.objects.create(
            name='Test Product Inactive',
            sku='TEST-SKU-003',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            is_active=False
        )
        
        # Verify catalog service was NOT called
        mock_service.create_product_in_catalog.assert_not_called()
        mock_service.update_product_in_catalog.assert_not_called()
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_product_update_without_catalog_id_creates_new(self, mock_service_class):
        """Test that updating a product without catalog ID creates it in catalog"""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_456'}
        
        # Create a product without triggering signals
        product = Product(
            name='Test Product',
            sku='TEST-SKU-004',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True
        )
        product.save()
        
        # Reset mock
        mock_service.reset_mock()
        
        # Update the product (should create since no catalog_id)
        product.price = 150.00
        product.save()
        
        # Verify create was called (not update)
        mock_service.create_product_in_catalog.assert_called_once()
        
        # Verify the product was updated with catalog ID
        product.refresh_from_db()
        self.assertEqual(product.whatsapp_catalog_id, 'meta_catalog_456')
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_product_deletion_triggers_catalog_deletion(self, mock_service_class):
        """Test that deleting a product triggers Meta Catalog deletion"""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_789'}
        mock_service.delete_product_from_catalog.return_value = {'success': True}
        
        # Create a product with catalog ID
        product = Product.objects.create(
            name='Test Product',
            sku='TEST-SKU-005',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True,
            whatsapp_catalog_id='meta_catalog_789'
        )
        
        # Reset mock to clear creation call
        mock_service.reset_mock()
        
        # Delete the product
        product.delete()
        
        # Verify delete was called
        mock_service.delete_product_from_catalog.assert_called_once()
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_product_deletion_without_catalog_id_skips_sync(self, mock_service_class):
        """Test that deleting a product without catalog ID doesn't call API"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_999'}
        
        # Create a product
        product = Product.objects.create(
            name='Test Product',
            sku='TEST-SKU-006',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True
        )
        
        # Manually clear the catalog ID
        Product.objects.filter(pk=product.pk).update(whatsapp_catalog_id=None)
        product.refresh_from_db()
        
        # Reset mock
        mock_service.reset_mock()
        
        # Delete the product
        product.delete()
        
        # Verify delete was NOT called
        mock_service.delete_product_from_catalog.assert_not_called()
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_signal_handles_api_error_gracefully(self, mock_service_class):
        """Test that signal handles API errors without raising exceptions"""
        # Setup mock to raise an exception
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.side_effect = Exception("API Error")
        
        # Create a product - should not raise exception
        try:
            product = Product.objects.create(
                name='Test Product',
                sku='TEST-SKU-007',
                description='Test product description',
                product_type='hardware',
                category=self.category,
                price=100.00,
                currency='USD',
                stock_quantity=10,
                is_active=True
            )
            # If we get here, the signal handled the error gracefully
            self.assertIsNotNone(product.id)
        except Exception as e:
            self.fail(f"Signal should handle API errors gracefully, but raised: {e}")
