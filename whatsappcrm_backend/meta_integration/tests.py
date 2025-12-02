from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock, PropertyMock
from .catalog_service import MetaCatalogService, PLACEHOLDER_IMAGE_PATH
from products_and_services.models import Product, ProductCategory, ProductImage


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
    
    def _mock_product_images(self, product, mock_image):
        """
        Helper method to mock product.images.first() return value.
        Uses PropertyMock to properly mock the Django RelatedManager.
        """
        mock_images = MagicMock()
        mock_images.first.return_value = mock_image
        return patch.object(type(product), 'images', new_callable=PropertyMock, return_value=mock_images)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_relative_image_url(self, mock_config):
        """Test that relative image URLs are converted to absolute URLs"""
        self._setup_mock_config(mock_config)
        
        # Create a product image with relative URL
        mock_image = MagicMock()
        mock_image.image.url = '/media/product_images/test.png'
        
        # Mock the images queryset using PropertyMock for Django RelatedManager
        with self._mock_product_images(self.product, mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
                product_data = service._get_product_data(self.product)
            
            # Verify image_link is absolute URL
            self.assertIn('image_link', product_data)
            self.assertTrue(product_data['image_link'].startswith('https://'))
            self.assertIn('backend.hanna.co.zw', product_data['image_link'])
            self.assertEqual(
                product_data['image_link'],
                'https://backend.hanna.co.zw/media/product_images/test.png'
            )
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_absolute_image_url(self, mock_config):
        """Test that absolute image URLs are not modified"""
        self._setup_mock_config(mock_config)
        
        # Create a product image with absolute URL
        mock_image = MagicMock()
        mock_image.image.url = 'https://cdn.example.com/images/test.png'
        
        # Mock the images queryset using PropertyMock for Django RelatedManager
        with self._mock_product_images(self.product, mock_image):
            service = MetaCatalogService()
            product_data = service._get_product_data(self.product)
            
            # Verify image_link remains absolute URL
            self.assertIn('image_link', product_data)
            self.assertEqual(
                product_data['image_link'],
                'https://cdn.example.com/images/test.png'
            )
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_without_image(self, mock_config):
        """Test that products without images use a static placeholder URL"""
        self._setup_mock_config(mock_config)
        
        service = MetaCatalogService()
        
        with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
            product_data = service._get_product_data(self.product)
        
        # Verify image_link is present with publicly accessible placeholder URL
        # (Meta API does not accept data URIs)
        self.assertIn('image_link', product_data)
        # Should use a static placeholder URL, not a data URI
        self.assertFalse(product_data['image_link'].startswith('data:'))
        self.assertTrue(product_data['image_link'].startswith('https://'))
        # Verify it uses the placeholder path
        expected_placeholder_url = f'https://backend.hanna.co.zw{PLACEHOLDER_IMAGE_PATH}'
        self.assertEqual(product_data['image_link'], expected_placeholder_url)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_empty_image_url(self, mock_config):
        """Test that products with empty image URLs use placeholder URL"""
        self._setup_mock_config(mock_config)
        
        # Create a product image with empty URL
        mock_image = MagicMock()
        mock_image.image.url = ''  # Empty string
        
        # Mock the images queryset using PropertyMock for Django RelatedManager
        with self._mock_product_images(self.product, mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
                product_data = service._get_product_data(self.product)
            
            # Verify image_link uses placeholder URL when URL is empty
            self.assertIn('image_link', product_data)
            expected_placeholder_url = f'https://backend.hanna.co.zw{PLACEHOLDER_IMAGE_PATH}'
            self.assertEqual(product_data['image_link'], expected_placeholder_url)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_none_image_url(self, mock_config):
        """Test that products with None image URLs use placeholder URL"""
        self._setup_mock_config(mock_config)
        
        # Create a product image with None URL
        mock_image = MagicMock()
        mock_image.image.url = None  # None value
        
        # Mock the images queryset using PropertyMock for Django RelatedManager
        with self._mock_product_images(self.product, mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
                product_data = service._get_product_data(self.product)
            
            # Verify image_link uses placeholder URL when URL is None
            self.assertIn('image_link', product_data)
            expected_placeholder_url = f'https://backend.hanna.co.zw{PLACEHOLDER_IMAGE_PATH}'
            self.assertEqual(product_data['image_link'], expected_placeholder_url)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_whitespace_image_url(self, mock_config):
        """Test that products with whitespace-only image URLs use placeholder URL"""
        self._setup_mock_config(mock_config)
        
        # Create a product image with whitespace-only URL
        mock_image = MagicMock()
        mock_image.image.url = '   '  # Whitespace only
        
        # Mock the images queryset using PropertyMock for Django RelatedManager
        with self._mock_product_images(self.product, mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP='backend.hanna.co.zw'):
                product_data = service._get_product_data(self.product)
            
            # Verify image_link uses placeholder URL when URL is only whitespace
            self.assertIn('image_link', product_data)
            expected_placeholder_url = f'https://backend.hanna.co.zw{PLACEHOLDER_IMAGE_PATH}'
            self.assertEqual(product_data['image_link'], expected_placeholder_url)
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_url_containing_whitespace(self, mock_config):
        """Test that URLs with leading/trailing whitespace are properly trimmed"""
        self._setup_mock_config(mock_config)
        
        # Test data: URL with leading and trailing whitespace around valid path
        test_domain = 'backend.hanna.co.zw'
        url_with_whitespace = '  /media/product_images/test.png  '
        expected_trimmed_url = f'https://{test_domain}/media/product_images/test.png'
        
        # Create a product image with URL containing whitespace
        mock_image = MagicMock()
        mock_image.image.url = url_with_whitespace
        
        # Mock the images queryset using PropertyMock for Django RelatedManager
        with self._mock_product_images(self.product, mock_image):
            service = MetaCatalogService()
            
            with override_settings(BACKEND_DOMAIN_FOR_CSP=test_domain):
                product_data = service._get_product_data(self.product)
            
            # Verify image_link is properly trimmed and converted to absolute URL
            self.assertIn('image_link', product_data)
            self.assertEqual(product_data['image_link'], expected_trimmed_url)
            # Ensure no whitespace in the final URL
            self.assertNotIn(' ', product_data['image_link'])
    
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
        
        # Create product and then manually clear the SKU
        # (SKU is auto-generated in save(), so we need to update it after creation)
        product_no_sku = Product.objects.create(
            name='Product No SKU',
            description='Test product without SKU',
            product_type='service',
            category=self.category,
            price=50.00,
            currency='USD',
            is_active=True
        )
        # Clear the auto-generated SKU
        Product.objects.filter(pk=product_no_sku.pk).update(sku=None)
        product_no_sku.refresh_from_db()
        
        service = MetaCatalogService()
        
        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            service._get_product_data(product_no_sku)
        
        self.assertIn('missing an SKU', str(context.exception))
