from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from .catalog_service import MetaCatalogService
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
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_with_relative_image_url(self, mock_config):
        """Test that relative image URLs are converted to absolute URLs"""
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
        # Create a product image with relative URL
        mock_image = MagicMock()
        mock_image.image.url = '/media/product_images/test.png'
        
        # Mock the images queryset
        with patch.object(self.product.images, 'first', return_value=mock_image):
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
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
        # Create a product image with absolute URL
        mock_image = MagicMock()
        mock_image.image.url = 'https://cdn.example.com/images/test.png'
        
        # Mock the images queryset
        with patch.object(self.product.images, 'first', return_value=mock_image):
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
        """Test that products without images use a placeholder image_link"""
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
        service = MetaCatalogService()
        product_data = service._get_product_data(self.product)
        
        # Verify image_link is present with placeholder URL (Meta API requires it)
        self.assertIn('image_link', product_data)
        self.assertIn('placeholder', product_data['image_link'].lower())
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_required_fields(self, mock_config):
        """Test that all required fields are present in product data"""
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
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
        self.assertEqual(product_data['price'], '100.0')
        self.assertEqual(product_data['currency'], 'USD')
        self.assertEqual(product_data['condition'], 'new')
        self.assertEqual(product_data['availability'], 'in stock')
        self.assertEqual(product_data['brand'], 'TestBrand')
    
    @patch('meta_integration.catalog_service.MetaAppConfig')
    def test_get_product_data_out_of_stock(self, mock_config):
        """Test that products with zero stock show as out of stock"""
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
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
        # Setup mock config
        mock_active_config = MagicMock()
        mock_active_config.api_version = 'v23.0'
        mock_active_config.access_token = 'test_token'
        mock_active_config.catalog_id = 'test_catalog_id'
        mock_config.objects.get_active_config.return_value = mock_active_config
        
        # Create product without SKU
        product_no_sku = Product.objects.create(
            name='Product No SKU',
            description='Test product without SKU',
            product_type='service',
            category=self.category,
            price=50.00,
            currency='USD',
            is_active=True
        )
        
        service = MetaCatalogService()
        
        # Verify ValueError is raised
        with self.assertRaises(ValueError) as context:
            service._get_product_data(product_no_sku)
        
        self.assertIn('missing an SKU', str(context.exception))
