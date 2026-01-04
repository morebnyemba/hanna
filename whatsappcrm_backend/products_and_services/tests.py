from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import Product, ProductCategory, ProductImage, SerializedItem

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


class ProductImageSyncSignalTestCase(TestCase):
    """
    Test cases for ProductImage signal triggering product re-sync to Meta Catalog.
    
    This tests the fix for the issue where product images are not detected during 
    initial product creation because inline images are saved AFTER the parent product.
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = ProductCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_image_creation_triggers_resync_for_product_without_catalog_id(self, mock_service_class):
        """Test that adding an image to a product without catalog_id triggers re-sync"""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_img_001'}
        
        # Create a product
        product = Product.objects.create(
            name='Test Product',
            sku='TEST-IMG-001',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True
        )
        
        # Initial sync should have happened - reset the mock
        mock_service.reset_mock()
        
        # Manually clear the catalog ID to simulate failed initial sync
        Product.objects.filter(pk=product.pk).update(whatsapp_catalog_id=None)
        product.refresh_from_db()
        
        # Create a simple test image
        test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x89\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/gif'
        )
        
        # Add image to product - this should trigger re-sync
        ProductImage.objects.create(
            product=product,
            image=test_image,
            alt_text='Test image'
        )
        
        # Verify create was called again (re-sync triggered)
        self.assertTrue(mock_service.create_product_in_catalog.called)
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_image_creation_triggers_update_for_synced_product(self, mock_service_class):
        """Test that adding a new image to a synced product triggers update"""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_img_002'}
        mock_service.update_product_in_catalog.return_value = {'success': True}
        
        # Create a product with catalog ID
        product = Product.objects.create(
            name='Test Product',
            sku='TEST-IMG-002',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True,
            whatsapp_catalog_id='meta_catalog_img_002'
        )
        
        # Reset the mock
        mock_service.reset_mock()
        
        # Create a simple test image
        test_image = SimpleUploadedFile(
            name='test_image2.jpg',
            content=b'\x47\x49\x46\x38\x89\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/gif'
        )
        
        # Add image to product - this should trigger update
        ProductImage.objects.create(
            product=product,
            image=test_image,
            alt_text='Test image 2'
        )
        
        # Verify update was called (sync triggered with existing catalog_id)
        self.assertTrue(mock_service.update_product_in_catalog.called)
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_image_creation_resets_failed_sync_attempts(self, mock_service_class):
        """Test that adding an image resets sync attempts for previously failed products"""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_img_003'}
        
        # Create a product and set it to failed state
        product = Product.objects.create(
            name='Test Product',
            sku='TEST-IMG-003',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True
        )
        
        # Simulate failed sync attempts
        Product.objects.filter(pk=product.pk).update(
            whatsapp_catalog_id=None,
            meta_sync_attempts=3,
            meta_sync_last_error='Previous error'
        )
        product.refresh_from_db()
        
        # Reset the mock
        mock_service.reset_mock()
        
        # Create a simple test image
        test_image = SimpleUploadedFile(
            name='test_image3.jpg',
            content=b'\x47\x49\x46\x38\x89\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/gif'
        )
        
        # Add image to product - this should reset attempts and trigger re-sync
        ProductImage.objects.create(
            product=product,
            image=test_image,
            alt_text='Test image 3'
        )
        
        # Verify create was called
        self.assertTrue(mock_service.create_product_in_catalog.called)
    
    @patch('products_and_services.signals.MetaCatalogService')
    def test_image_for_inactive_product_skips_sync(self, mock_service_class):
        """Test that adding an image to an inactive product does not trigger sync"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Create an inactive product
        product = Product.objects.create(
            name='Inactive Product',
            sku='TEST-IMG-004',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=False
        )
        
        # Reset the mock
        mock_service.reset_mock()
        
        # Manually clear the catalog ID
        Product.objects.filter(pk=product.pk).update(whatsapp_catalog_id=None)
        product.refresh_from_db()
        
        # Create a simple test image
        test_image = SimpleUploadedFile(
            name='test_image4.jpg',
            content=b'\x47\x49\x46\x38\x89\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/gif'
        )
        
        # Add image to product
        ProductImage.objects.create(
            product=product,
            image=test_image,
            alt_text='Test image 4'
        )
        
        # Verify sync was NOT called
        mock_service.create_product_in_catalog.assert_not_called()
        mock_service.update_product_in_catalog.assert_not_called()


class PublicProductAccessTestCase(TestCase):
    """
    Test cases for public access to products and categories
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test category
        self.category = ProductCategory.objects.create(
            name='Public Test Category',
            description='Test category description'
        )
        
        # Create test products
        self.active_product = Product.objects.create(
            name='Active Product',
            sku='ACTIVE-001',
            description='Active test product',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True
        )
        
        self.inactive_product = Product.objects.create(
            name='Inactive Product',
            sku='INACTIVE-001',
            description='Inactive test product',
            product_type='hardware',
            category=self.category,
            price=50.00,
            currency='USD',
            stock_quantity=5,
            is_active=False
        )
    
    def test_public_can_list_products(self):
        """Test that unauthenticated users can list products"""
        # Make sure client is not authenticated
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/crm-api/products/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        # Both active and inactive products should be visible in list
        self.assertGreaterEqual(len(response.data), 2)
    
    def test_public_can_retrieve_product(self):
        """Test that unauthenticated users can retrieve a single product"""
        # Make sure client is not authenticated
        self.client.force_authenticate(user=None)
        
        response = self.client.get(f'/crm-api/products/products/{self.active_product.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Active Product')
        self.assertEqual(response.data['sku'], 'ACTIVE-001')
    
    def test_public_cannot_create_product(self):
        """Test that unauthenticated users cannot create products"""
        # Make sure client is not authenticated
        self.client.force_authenticate(user=None)
        
        response = self.client.post(
            '/crm-api/products/products/',
            {
                'name': 'New Product',
                'sku': 'NEW-001',
                'product_type': 'hardware',
                'price': 75.00,
                'currency': 'USD'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_public_cannot_update_product(self):
        """Test that unauthenticated users cannot update products"""
        # Make sure client is not authenticated
        self.client.force_authenticate(user=None)
        
        response = self.client.patch(
            f'/crm-api/products/products/{self.active_product.id}/',
            {
                'price': 150.00
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_public_cannot_delete_product(self):
        """Test that unauthenticated users cannot delete products"""
        # Make sure client is not authenticated
        self.client.force_authenticate(user=None)
        
        response = self.client.delete(f'/crm-api/products/products/{self.active_product.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_public_can_list_categories(self):
        """Test that unauthenticated users can list product categories"""
        # Make sure client is not authenticated
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/crm-api/products/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_public_can_retrieve_category(self):
        """Test that unauthenticated users can retrieve a single category"""
        # Make sure client is not authenticated
        self.client.force_authenticate(user=None)
        
        response = self.client.get(f'/crm-api/products/categories/{self.category.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Public Test Category')


class MetaCatalogSyncAPITestCase(TestCase):
    """
    Test cases for Meta Catalog sync API endpoints.
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
        self.synced_product = Product.objects.create(
            name='Synced Product',
            sku='SYNCED-001',
            description='Product synced to Meta',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True,
            whatsapp_catalog_id='meta_catalog_12345'
        )
        
        self.unsynced_product = Product.objects.create(
            name='Unsynced Product',
            sku='UNSYNCED-001',
            description='Product not synced to Meta',
            product_type='hardware',
            category=self.category,
            price=50.00,
            currency='USD',
            stock_quantity=5,
            is_active=True
        )
        
        self.no_sku_product = Product.objects.create(
            name='No SKU Product',
            description='Product without SKU',
            product_type='service',
            category=self.category,
            price=25.00,
            currency='USD',
            is_active=True
        )
    
    @patch('products_and_services.views.MetaCatalogService')
    def test_meta_sync_action_success(self, mock_service_class):
        """Test meta-sync action for a product"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.sync_product_update.return_value = {'id': 'new_catalog_id'}
        
        response = self.client.post(
            f'/crm-api/products/products/{self.unsynced_product.id}/meta-sync/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['product_id'], self.unsynced_product.id)
        mock_service.sync_product_update.assert_called_once()
    
    @patch('products_and_services.views.MetaCatalogService')
    def test_meta_sync_action_no_sku(self, mock_service_class):
        """Test meta-sync action for a product without SKU"""
        response = self.client.post(
            f'/crm-api/products/products/{self.no_sku_product.id}/meta-sync/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('SKU', response.data['error'])
    
    @patch('products_and_services.views.MetaCatalogService')
    def test_meta_visibility_published(self, mock_service_class):
        """Test setting product visibility to published"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.set_product_visibility.return_value = {'success': True}
        
        response = self.client.post(
            f'/crm-api/products/products/{self.synced_product.id}/meta-visibility/',
            {'visibility': 'published'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['visibility'], 'published')
        mock_service.set_product_visibility.assert_called_once_with(
            self.synced_product, 'published'
        )
    
    @patch('products_and_services.views.MetaCatalogService')
    def test_meta_visibility_hidden(self, mock_service_class):
        """Test setting product visibility to hidden"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.set_product_visibility.return_value = {'success': True}
        
        response = self.client.post(
            f'/crm-api/products/products/{self.synced_product.id}/meta-visibility/',
            {'visibility': 'hidden'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['visibility'], 'hidden')
    
    def test_meta_visibility_invalid_value(self):
        """Test setting product visibility with invalid value"""
        response = self.client.post(
            f'/crm-api/products/products/{self.synced_product.id}/meta-visibility/',
            {'visibility': 'invalid'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_meta_visibility_unsynced_product(self):
        """Test setting visibility for unsynced product"""
        response = self.client.post(
            f'/crm-api/products/products/{self.unsynced_product.id}/meta-visibility/',
            {'visibility': 'published'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('not been synced', response.data['error'])
    
    @patch('products_and_services.views.MetaCatalogService')
    def test_meta_status_synced_product(self, mock_service_class):
        """Test getting meta status for a synced product"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_product_from_catalog.return_value = {
            'id': 'meta_catalog_12345',
            'name': 'Synced Product',
            'visibility': 'published'
        }
        
        response = self.client.get(
            f'/crm-api/products/products/{self.synced_product.id}/meta-status/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['synced'])
        self.assertEqual(response.data['catalog_id'], 'meta_catalog_12345')
        self.assertIn('meta_catalog_data', response.data)
    
    def test_meta_status_unsynced_product(self):
        """Test getting meta status for an unsynced product"""
        response = self.client.get(
            f'/crm-api/products/products/{self.unsynced_product.id}/meta-status/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['synced'])
        self.assertIn('local_sync_info', response.data)
    
    @patch('products_and_services.views.MetaCatalogService')
    def test_meta_batch_visibility(self, mock_service_class):
        """Test batch visibility update for multiple products"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.batch_update_products.return_value = {'success': True}
        
        response = self.client.post(
            '/crm-api/products/products/meta-batch-visibility/',
            {
                'product_ids': [self.synced_product.id],
                'visibility': 'published'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['visibility'], 'published')
    
    def test_meta_batch_visibility_no_visibility(self):
        """Test batch visibility without visibility field"""
        response = self.client.post(
            '/crm-api/products/products/meta-batch-visibility/',
            {
                'product_ids': [self.synced_product.id]
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('products_and_services.views.MetaCatalogService')
    def test_meta_batch_sync(self, mock_service_class):
        """Test batch sync for multiple products"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.sync_product_update.return_value = {'id': 'new_catalog_id'}
        
        response = self.client.post(
            '/crm-api/products/products/meta-batch-sync/',
            {
                'product_ids': [self.synced_product.id, self.unsynced_product.id]
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('success_count', response.data)
    
    def test_meta_batch_sync_empty_list(self):
        """Test batch sync with empty product list"""
        response = self.client.post(
            '/crm-api/products/products/meta-batch-sync/',
            {
                'product_ids': []
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_meta_sync_unauthenticated(self):
        """Test that unauthenticated users cannot sync products"""
        self.client.force_authenticate(user=None)
        
        response = self.client.post(
            f'/crm-api/products/products/{self.synced_product.id}/meta-sync/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MetaCatalogServiceMethodsTestCase(TestCase):
    """
    Test cases for MetaCatalogService methods.
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = ProductCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST-001',
            description='Test product',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True,
            whatsapp_catalog_id='meta_catalog_12345'
        )
    
    @patch('meta_integration.catalog_service.MetaAppConfig.objects.get_active_config')
    @patch('meta_integration.catalog_service.requests.post')
    def test_set_product_visibility_published(self, mock_post, mock_get_config):
        """Test setting product visibility to published"""
        from meta_integration.catalog_service import MetaCatalogService
        
        # Setup mock config
        mock_config = MagicMock()
        mock_config.api_version = 'v19.0'
        mock_config.access_token = 'test_token'
        mock_config.catalog_id = 'test_catalog_id'
        mock_get_config.return_value = mock_config
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        service = MetaCatalogService()
        result = service.set_product_visibility(self.product, 'published')
        
        self.assertEqual(result, {'success': True})
        mock_post.assert_called_once()
        
        # Verify the payload contains visibility
        call_kwargs = mock_post.call_args[1]
        self.assertIn('json', call_kwargs)
        requests_list = call_kwargs['json']['requests']
        self.assertEqual(len(requests_list), 1)
        self.assertEqual(requests_list[0]['data']['visibility'], 'published')
    
    @patch('meta_integration.catalog_service.MetaAppConfig.objects.get_active_config')
    @patch('meta_integration.catalog_service.requests.get')
    def test_get_product_from_catalog(self, mock_get, mock_get_config):
        """Test getting product from Meta catalog"""
        from meta_integration.catalog_service import MetaCatalogService
        
        # Setup mock config
        mock_config = MagicMock()
        mock_config.api_version = 'v19.0'
        mock_config.access_token = 'test_token'
        mock_config.catalog_id = 'test_catalog_id'
        mock_get_config.return_value = mock_config
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'meta_catalog_12345',
            'name': 'Test Product',
            'visibility': 'published'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        service = MetaCatalogService()
        result = service.get_product_from_catalog(self.product)
        
        self.assertEqual(result['id'], 'meta_catalog_12345')
        mock_get.assert_called_once()
    
    @patch('meta_integration.catalog_service.MetaAppConfig.objects.get_active_config')
    def test_set_product_visibility_invalid(self, mock_get_config):
        """Test setting product visibility with invalid value"""
        from meta_integration.catalog_service import MetaCatalogService
        
        mock_config = MagicMock()
        mock_config.api_version = 'v19.0'
        mock_config.access_token = 'test_token'
        mock_config.catalog_id = 'test_catalog_id'
        mock_get_config.return_value = mock_config
        
        service = MetaCatalogService()
        
        with self.assertRaises(ValueError) as context:
            service.set_product_visibility(self.product, 'invalid_visibility')
        
        self.assertIn('Invalid visibility', str(context.exception))
    
    @patch('meta_integration.catalog_service.MetaAppConfig.objects.get_active_config')
    def test_set_product_visibility_no_catalog_id(self, mock_get_config):
        """Test setting visibility for product without catalog ID"""
        from meta_integration.catalog_service import MetaCatalogService
        
        mock_config = MagicMock()
        mock_config.api_version = 'v19.0'
        mock_config.access_token = 'test_token'
        mock_config.catalog_id = 'test_catalog_id'
        mock_get_config.return_value = mock_config
        
        # Create product without catalog ID
        product_no_catalog = Product.objects.create(
            name='No Catalog Product',
            sku='NO-CAT-001',
            product_type='hardware',
            category=self.category,
            price=50.00,
            is_active=True
        )
        
        service = MetaCatalogService()
        
        with self.assertRaises(ValueError) as context:
            service.set_product_visibility(product_no_catalog, 'published')
        
        self.assertIn('Catalog ID', str(context.exception))


# Zoho Integration Tests

from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


class ZohoProductSyncTest(TestCase):
    """Tests for Zoho product synchronization."""
    
    def setUp(self):
        """Set up test data."""
        from integrations.models import ZohoCredential
        
        # Create Zoho credentials
        self.zoho_cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret',
            access_token='test_token',
            refresh_token='test_refresh',
            organization_id='test_org',
            expires_in=timezone.now() + timedelta(hours=1)
        )
    
    @patch('integrations.utils.requests.get')
    def test_fetch_products_success(self, mock_get):
        """Test successful product fetch from Zoho."""
        from integrations.utils import ZohoClient
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'items': [
                {
                    'item_id': '123',
                    'name': 'Test Product',
                    'sku': 'TEST-001',
                    'rate': 99.99,
                    'stock_on_hand': 10,
                    'status': 'active'
                }
            ],
            'page_context': {'has_more_page': False}
        }
        mock_get.return_value = mock_response
        
        # Test fetch
        client = ZohoClient()
        result = client.fetch_products(page=1)
        
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['item_id'], '123')
    
    @patch('integrations.utils.ZohoClient.fetch_all_products')
    def test_sync_zoho_products_to_db(self, mock_fetch):
        """Test syncing products from Zoho to database."""
        from products_and_services.services import sync_zoho_products_to_db
        
        # Mock Zoho API response
        mock_fetch.return_value = [
            {
                'item_id': '123',
                'name': 'Test Product',
                'sku': 'TEST-001',
                'description': 'Test Description',
                'rate': 99.99,
                'stock_on_hand': 10,
                'status': 'active'
            },
            {
                'item_id': '456',
                'name': 'Another Product',
                'sku': 'TEST-002',
                'rate': 149.99,
                'stock_on_hand': 5,
                'status': 'active'
            }
        ]
        
        # Run sync
        result = sync_zoho_products_to_db()
        
        # Check results
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['created'], 2)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['failed'], 0)
        
        # Verify products were created
        self.assertEqual(Product.objects.count(), 2)
        
        product1 = Product.objects.get(zoho_item_id='123')
        self.assertEqual(product1.name, 'Test Product')
        self.assertEqual(product1.sku, 'TEST-001')
        self.assertEqual(product1.price, Decimal('99.99'))
        self.assertEqual(product1.stock_quantity, 10)
        self.assertTrue(product1.is_active)
    
    @patch('integrations.utils.ZohoClient.fetch_all_products')
    def test_sync_updates_existing_product(self, mock_fetch):
        """Test that sync updates existing products."""
        from products_and_services.services import sync_zoho_products_to_db
        
        # Create existing product
        existing_product = Product.objects.create(
            name='Old Name',
            zoho_item_id='123',
            sku='TEST-001',
            price=Decimal('50.00'),
            stock_quantity=5,
            product_type='hardware'
        )
        
        # Mock updated data from Zoho
        mock_fetch.return_value = [
            {
                'item_id': '123',
                'name': 'Updated Product Name',
                'sku': 'TEST-001',
                'rate': 99.99,
                'stock_on_hand': 15,
                'status': 'active'
            }
        ]
        
        # Run sync
        result = sync_zoho_products_to_db()
        
        # Check results
        self.assertEqual(result['created'], 0)
        self.assertEqual(result['updated'], 1)
        
        # Verify product was updated
        existing_product.refresh_from_db()
        self.assertEqual(existing_product.name, 'Updated Product Name')
        self.assertEqual(existing_product.price, Decimal('99.99'))
        self.assertEqual(existing_product.stock_quantity, 15)
    
    @patch('integrations.utils.ZohoClient.fetch_all_products')
    def test_sync_handles_missing_item_id(self, mock_fetch):
        """Test that sync handles items without item_id gracefully."""
        from products_and_services.services import sync_zoho_products_to_db
        
        # Mock data with missing item_id
        mock_fetch.return_value = [
            {
                'name': 'Product Without ID',
                'sku': 'NO-ID',
                'rate': 50.00
            }
        ]
        
        # Run sync
        result = sync_zoho_products_to_db()
        
        # Should fail gracefully
        self.assertEqual(result['failed'], 1)
        self.assertGreater(len(result['errors']), 0)
        self.assertEqual(Product.objects.count(), 0)
    
    @patch('integrations.utils.ZohoClient.fetch_all_products')
    def test_sync_skips_duplicate_skus(self, mock_fetch):
        """Test that sync skips products with duplicate SKUs within the same sync run."""
        from products_and_services.services import sync_zoho_products_to_db
        
        # Mock data with duplicate SKUs
        mock_fetch.return_value = [
            {
                'item_id': '123',
                'name': 'First Product',
                'sku': 'DUPLICATE-SKU',
                'rate': 99.99,
                'stock_on_hand': 10,
                'status': 'active'
            },
            {
                'item_id': '456',
                'name': 'Second Product',
                'sku': 'DUPLICATE-SKU',  # Same SKU as first product
                'rate': 149.99,
                'stock_on_hand': 5,
                'status': 'active'
            },
            {
                'item_id': '789',
                'name': 'Third Product',
                'sku': 'UNIQUE-SKU',
                'rate': 199.99,
                'stock_on_hand': 3,
                'status': 'active'
            }
        ]
        
        # Run sync
        result = sync_zoho_products_to_db()
        
        # Check results - first product should be created, second should be skipped
        self.assertEqual(result['total'], 3)
        self.assertEqual(result['created'], 2)  # First and Third products
        self.assertEqual(result['skipped'], 1)  # Second product (duplicate SKU)
        self.assertEqual(result['failed'], 0)
        
        # Verify only 2 products were created
        self.assertEqual(Product.objects.count(), 2)
        
        # Verify the first product with duplicate SKU was created
        product1 = Product.objects.get(zoho_item_id='123')
        self.assertEqual(product1.name, 'First Product')
        self.assertEqual(product1.sku, 'DUPLICATE-SKU')
        
        # Verify the second product with duplicate SKU was NOT created
        self.assertFalse(Product.objects.filter(zoho_item_id='456').exists())
        
        # Verify the unique product was created
        product3 = Product.objects.get(zoho_item_id='789')
        self.assertEqual(product3.name, 'Third Product')
        self.assertEqual(product3.sku, 'UNIQUE-SKU')
    
    @patch('integrations.utils.ZohoClient.fetch_all_products')
    def test_sync_handles_existing_duplicate_sku(self, mock_fetch):
        """Test that sync skips products when SKU already exists in database."""
        from products_and_services.services import sync_zoho_products_to_db
        
        # Create existing product with a SKU
        existing_product = Product.objects.create(
            name='Existing Product',
            zoho_item_id='999',
            sku='EXISTING-SKU',
            price=Decimal('50.00'),
            stock_quantity=5,
            product_type='hardware'
        )
        
        # Mock data with a different Zoho item that has the same SKU
        mock_fetch.return_value = [
            {
                'item_id': '888',
                'name': 'New Product With Existing SKU',
                'sku': 'EXISTING-SKU',  # Same as existing product
                'rate': 99.99,
                'stock_on_hand': 15,
                'status': 'active'
            }
        ]
        
        # Run sync
        result = sync_zoho_products_to_db()
        
        # Check results - should skip due to duplicate SKU
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['created'], 0)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['skipped'], 1)
        
        # Verify only the original product exists
        self.assertEqual(Product.objects.count(), 1)
        
        # Verify the existing product was not modified
        existing_product.refresh_from_db()
        self.assertEqual(existing_product.name, 'Existing Product')
        self.assertEqual(existing_product.price, Decimal('50.00'))
        
        # Verify the new product was NOT created
        self.assertFalse(Product.objects.filter(zoho_item_id='888').exists())
    
    @patch('integrations.utils.requests.get')
    def test_fetch_products_with_400_error_detailed_logging(self, mock_get):
        """Test that 400 errors from Zoho API are logged with detailed information."""
        from integrations.utils import ZohoClient
        import logging
        
        # Mock API response with 400 error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.reason = 'Bad Request'
        mock_response.url = 'https://www.zohoapis.com/inventory/v1/items?organization_id=test_org&page=1&per_page=200'
        mock_response.json.return_value = {
            'code': 400,
            'message': 'Invalid organization ID'
        }
        mock_get.return_value = mock_response
        
        # Test fetch - should raise exception with detailed error
        client = ZohoClient()
        with self.assertRaises(Exception) as context:
            client.fetch_products(page=1)
        
        # Verify the exception contains the Zoho error message
        self.assertIn('Invalid organization ID', str(context.exception))
        self.assertIn('400', str(context.exception))
    
    @patch('integrations.utils.requests.get')
    def test_fetch_products_with_non_json_error_response(self, mock_get):
        """Test handling of non-JSON error responses from Zoho API."""
        from integrations.utils import ZohoClient
        from json import JSONDecodeError
        
        # Mock API response with 400 error and non-JSON body
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.reason = 'Bad Request'
        mock_response.url = 'https://www.zohoapis.com/inventory/v1/items?organization_id=test_org'
        mock_response.json.side_effect = JSONDecodeError('Not JSON', '', 0)
        mock_response.text = 'HTML error page or plain text error'
        mock_get.return_value = mock_response
        
        # Test fetch - should handle non-JSON response gracefully
        client = ZohoClient()
        with self.assertRaises(Exception) as context:
            client.fetch_products(page=1)
        
        # Verify the exception contains error info
        self.assertIn('400', str(context.exception))
    
    def test_celery_task_exists(self):
        """Test that the Celery task is defined."""
        from products_and_services.tasks import task_sync_zoho_products
        
        # Task should be defined and callable
        self.assertTrue(callable(task_sync_zoho_products))


class ZohoAdminViewTest(TestCase):
    """Tests for Zoho admin views."""
    
    def setUp(self):
        """Set up test user."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.force_login(self.admin_user)
    
    @patch('products_and_services.tasks.task_sync_zoho_products.delay')
    def test_trigger_sync_view(self, mock_task):
        """Test the trigger_sync_view endpoint."""
        # Mock task
        mock_task.return_value = MagicMock(id='test-task-id')
        
        # Call the view
        response = self.client.get('/crm-api/products/admin/sync-zoho/')
        
        # Should redirect to product list
        self.assertEqual(response.status_code, 302)
        
        # Task should be triggered
        mock_task.assert_called_once()
