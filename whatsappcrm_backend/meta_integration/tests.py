from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock, PropertyMock
from .catalog_service import MetaCatalogService, PLACEHOLDER_IMAGE_PATH
from products_and_services.models import Product, ProductCategory, ProductImage
from .signals import message_send_failed


class MetaCatalogServiceTestCase(TestCase):
    """
    Test cases for MetaCatalogService functionality.
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = ProductCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        # Create a test product
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST-SKU-001',
            description='Test product description',
            product_type='hardware',
            category=self.category,
            price=100.00,
            currency='USD',
            stock_quantity=10,
            brand='TestBrand',
            website_url='https://example.com/product',
            is_active=True
        )
    
    def _setup_mock_config(self, mock_config):
        """Helper method to setup mock MetaAppConfig"""
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        return mock_active_config
    
    def _mock_product_image_queryset(self, mock_image):
        """
        Returns a context manager to mock ProductImage.objects.filter().first() return value.
        This is needed because _get_product_data now queries ProductImage directly
        to avoid Django ORM caching issues with related objects.
        
        Usage:
            with self._mock_product_image_queryset(mock_image):
                # ProductImage.objects.filter(product_id=...).first() will return mock_image
                pass
        """
        mock_queryset = MagicMock()
        mock_queryset.first.return_value = mock_image
        mock_queryset.count.return_value = 1 if mock_image else 0
        return patch('products_and_services.models.ProductImage.objects.filter', return_value=mock_queryset)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_relative_image_url(self, mock_config):
        """Test that relative image URLs are converted to absolute URLs"""
        self._setup_mock_config(mock_config)
        
        # Create a mock image with relative URL
        mock_image = MagicMock()
        mock_image.image.url = '/media/product_images/test.png'
        
        # Mock the ProductImage.objects.filter() call
        with self._mock_product_image_queryset(mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
                product_data = service._get_product_data(self.product)
            
            # Verify image_url is absolute URL
            self.assertIn('image_url', product_data)
            self.assertTrue(product_data['image_url'].startswith('https://'))
            self.assertIn('backend.hanna.co.zw', product_data['image_url'])
            self.assertEqual(
                product_data['image_url'],
                'https://backend.hanna.co.zw/media/product_images/test.png'
            )
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_absolute_image_url(self, mock_config):
        """Test that absolute image URLs are not modified"""
        self._setup_mock_config(mock_config)
        
        # Create a mock image with absolute URL
        mock_image = MagicMock()
        mock_image.image.url = 'https://cdn.example.com/images/test.png'
        
        # Mock the ProductImage.objects.filter() call
        with self._mock_product_image_queryset(mock_image):
            service = MetaCatalogService()
            product_data = service._get_product_data(self.product)
            
            # Verify image_url remains absolute URL
            self.assertIn('image_url', product_data)
            self.assertEqual(
                product_data['image_url'],
                'https://cdn.example.com/images/test.png'
            )
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_without_image(self, mock_config):
        """Test that products without images use a static placeholder URL"""
        self._setup_mock_config(mock_config)
        
        service = MetaCatalogService()
        
        with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
            product_data = service._get_product_data(self.product)
        
        # Verify image_url is present with publicly accessible placeholder URL
        # (Meta API does not accept data URIs)
        self.assertIn('image_url', product_data)
        # Should use a static placeholder URL, not a data URI
        self.assertFalse(product_data['image_url'].startswith('data:'))
        self.assertTrue(product_data['image_url'].startswith('https://'))
        # Verify it uses the placeholder path
        expected_placeholder_url = f'https://backend.hanna.co.zw{PLACEHOLDER_IMAGE_PATH}'
        self.assertEqual(product_data['image_url'], expected_placeholder_url)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_empty_image_url(self, mock_config):
        """Test that products with empty image URLs use placeholder URL"""
        self._setup_mock_config(mock_config)
        
        # Create a mock image with empty URL
        mock_image = MagicMock()
        mock_image.image.url = ''  # Empty string
        
        # Mock the ProductImage.objects.filter() call
        with self._mock_product_image_queryset(mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
                product_data = service._get_product_data(self.product)
            
            # Verify image_url uses placeholder URL when URL is empty
            self.assertIn('image_url', product_data)
            expected_placeholder_url = f'https://backend.hanna.co.zw{PLACEHOLDER_IMAGE_PATH}'
            self.assertEqual(product_data['image_url'], expected_placeholder_url)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_none_image_url(self, mock_config):
        """Test that products with None image URLs use placeholder URL"""
        self._setup_mock_config(mock_config)
        
        # Create a mock image with None URL
        mock_image = MagicMock()
        mock_image.image.url = None  # None value
        
        # Mock the ProductImage.objects.filter() call
        with self._mock_product_image_queryset(mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
                product_data = service._get_product_data(self.product)
            
            # Verify image_url uses placeholder URL when URL is None
            self.assertIn('image_url', product_data)
            expected_placeholder_url = f'https://backend.hanna.co.zw{PLACEHOLDER_IMAGE_PATH}'
            self.assertEqual(product_data['image_url'], expected_placeholder_url)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_whitespace_image_url(self, mock_config):
        """Test that products with whitespace-only image URLs use placeholder URL"""
        self._setup_mock_config(mock_config)
        
        # Create a mock image with whitespace-only URL
        mock_image = MagicMock()
        mock_image.image.url = '   '  # Whitespace only
        
        # Mock the ProductImage.objects.filter() call
        with self._mock_product_image_queryset(mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
                product_data = service._get_product_data(self.product)
            
            # Verify image_url uses placeholder URL when URL is only whitespace
            self.assertIn('image_url', product_data)
            expected_placeholder_url = f'https://backend.hanna.co.zw{PLACEHOLDER_IMAGE_PATH}'
            self.assertEqual(product_data['image_url'], expected_placeholder_url)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_url_containing_whitespace(self, mock_config):
        """Test that URLs with leading/trailing whitespace are properly trimmed"""
        self._setup_mock_config(mock_config)
        
        # Test data: URL with leading and trailing whitespace around valid path
        test_domain = 'backend.hanna.co.zw'
        url_with_whitespace = '  /media/product_images/test.png  '
        expected_trimmed_url = f'https://{test_domain}/media/product_images/test.png'
        
        # Create a mock image with URL containing whitespace
        mock_image = MagicMock()
        mock_image.image.url = url_with_whitespace
        
        # Mock the ProductImage.objects.filter() call
        with self._mock_product_image_queryset(mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP=test_domain):
                product_data = service._get_product_data(self.product)
            
            # Verify image_url is properly trimmed and converted to absolute URL
            self.assertIn('image_url', product_data)
            self.assertEqual(product_data['image_url'], expected_trimmed_url)
            # Ensure no whitespace in the final URL
            self.assertNotIn(' ', product_data['image_url'])
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_required_fields(self, mock_config):
        """Test that all required fields are present in product data"""
        self._setup_mock_config(mock_config)
        
        service = MetaCatalogService()
        product_data = service._get_product_data(self.product)
        
        # Verify all required fields are present
        required_fields = ['retailer_id', 'name', 'price', 'currency', 'condition', 'availability', 'link']
        for field in required_fields:
            self.assertIn(field, product_data, f"Required field '{field}' missing from product data")
        
        # Verify optional fields are present when data exists
        self.assertIn('description', product_data)
        self.assertIn('brand', product_data)
        
        # Verify values are correct
        self.assertEqual(product_data['retailer_id'], 'TEST-SKU-001')
        self.assertEqual(product_data['name'], 'Test Product')
        self.assertEqual(product_data['price'], 10000)  # Price in cents: $100.00 = 10000 cents
        self.assertEqual(product_data['currency'], 'USD')
        self.assertEqual(product_data['condition'], 'new')
        self.assertEqual(product_data['availability'], 'in stock')
        self.assertEqual(product_data['brand'], 'TestBrand')
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_out_of_stock(self, mock_config):
        """Test that products with zero stock show as out of stock"""
        self._setup_mock_config(mock_config)
        
        # Set product stock to zero
        self.product.stock_quantity = 0
        self.product.save()
        
        service = MetaCatalogService()
        product_data = service._get_product_data(self.product)
        
        # Verify availability is out of stock
        self.assertEqual(product_data['availability'], 'out of stock')
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_without_sku_raises_error(self, mock_config):
        """Test that products without SKU raise ValueError"""
        self._setup_mock_config(mock_config)
        
        # Create a mock product with no SKU to test the validation
        # Using a mock avoids the auto-generation of SKU in the Product.save() method
        mock_product = MagicMock()
        mock_product.name = 'Product No SKU'
        mock_product.id = 999
        mock_product.sku = None  # No SKU
        
        service = MetaCatalogService()
        
        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            service._get_product_data(mock_product)
        
        self.assertIn('missing an SKU', str(context.exception))


class SignalImportTest(TestCase):
    """Test case to ensure signal is properly imported in tasks.py"""
    
    def test_message_send_failed_signal_import(self):
        """Test that message_send_failed signal is properly imported in tasks module"""
        # Import the tasks module
        from . import tasks
        
        # Verify that message_send_failed is accessible in the tasks module
        self.assertTrue(hasattr(tasks, 'message_send_failed'))
        
        # Verify it's the correct signal from signals module
        from .signals import message_send_failed as expected_signal
        self.assertIs(tasks.message_send_failed, expected_signal)
    
    def test_signal_can_be_sent(self):
        """Test that signal can be sent without errors"""
        # This test ensures the signal is properly defined and can be used
        from .signals import message_send_failed
        
        # Create a mock message instance
        mock_message = MagicMock()
        mock_message.id = 999
        mock_message.status = 'failed'
        
        # Signal.send() should not raise any errors
        # The send() method returns a list of (receiver, response) tuples
        result = message_send_failed.send(sender=self.__class__, message_instance=mock_message)
        
        # Verify the result is a list (even if empty)
        self.assertIsInstance(result, list)


class GoogleProductCategoryTestCase(TestCase):
    """Test cases for google_product_category functionality"""
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_product_with_google_category_includes_in_payload(self, mock_config):
        """Test that google_product_category is included in Meta API payload when set"""
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
        # Create product with google_product_category
        product = Product.objects.create(
            name='Solar Panel Test',
            sku='SOLAR-001',
            description='100W Solar Panel',
            product_type='hardware',
            price=150.00,
            currency='USD',
            stock_quantity=5,
            brand='SolarTech',
            google_product_category='Electronics > Renewable Energy > Solar Panels',
            is_active=True
        )
        
        service = MetaCatalogService()
        product_data = service._get_product_data(product)
        
        # Verify google_product_category is in the payload
        self.assertIn('google_product_category', product_data)
        self.assertEqual(product_data['google_product_category'], 'Electronics > Renewable Energy > Solar Panels')
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_product_without_google_category_excludes_from_payload(self, mock_config):
        """Test that google_product_category is not included when not set"""
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
        # Create product without google_product_category
        product = Product.objects.create(
            name='Generic Product',
            sku='GENERIC-001',
            description='Generic Product',
            product_type='hardware',
            price=100.00,
            currency='USD',
            stock_quantity=10,
            is_active=True
        )
        
        service = MetaCatalogService()
        product_data = service._get_product_data(product)
        
        # Verify google_product_category is NOT in the payload
        self.assertNotIn('google_product_category', product_data)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_product_with_category_id_includes_in_payload(self, mock_config):
        """Test that google_product_category works with category IDs (numeric format)"""
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
        # Create product with category ID
        product = Product.objects.create(
            name='Laptop Test',
            sku='LAPTOP-001',
            description='Business Laptop',
            product_type='hardware',
            price=800.00,
            currency='USD',
            stock_quantity=3,
            google_product_category='328',  # Electronics > Computers > Laptops
            is_active=True
        )
        
        service = MetaCatalogService()
        product_data = service._get_product_data(product)
        
        # Verify category ID is in the payload
        self.assertIn('google_product_category', product_data)
        self.assertEqual(product_data['google_product_category'], '328')
