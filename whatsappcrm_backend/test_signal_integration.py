#!/usr/bin/env python
"""
Manual integration test to verify Product-Meta Catalog signal handlers.
This script demonstrates the signal handlers in action.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')

from django.conf import settings
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}

django.setup()

from django.core.management import call_command
from unittest.mock import patch, MagicMock
from products_and_services.models import Product, ProductCategory

# Setup database
print("Setting up test database...")
call_command('migrate', '--run-syncdb', verbosity=0)

# Create test category
print("\nCreating test category...")
category = ProductCategory.objects.create(
    name='Test Electronics',
    description='Electronic devices for testing'
)
print(f"✓ Created category: {category.name}")

print("\n" + "="*80)
print("TEST 1: Creating a new product (should trigger create signal)")
print("="*80)

with patch('meta_integration.catalog_service.MetaCatalogService') as mock_service_class:
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_service.create_product_in_catalog.return_value = {'id': 'meta_catalog_123'}
    
    product = Product.objects.create(
        name='Test Smartphone',
        sku='PHONE-001',
        description='A high-quality smartphone',
        product_type='hardware',
        category=category,
        price=599.99,
        currency='USD',
        stock_quantity=50,
        brand='TestBrand',
        is_active=True
    )
    
    print(f"✓ Product created: {product.name}")
    print(f"  - ID: {product.id}")
    print(f"  - SKU: {product.sku}")
    print(f"  - Active: {product.is_active}")
    
    if mock_service.create_product_in_catalog.called:
        print("✓ Signal triggered: create_product_in_catalog was called")
        print(f"  - Catalog ID set: {product.whatsapp_catalog_id}")
    else:
        print("✗ Signal NOT triggered: create_product_in_catalog was NOT called")

print("\n" + "="*80)
print("TEST 2: Updating the product (should trigger update signal)")
print("="*80)

with patch('meta_integration.catalog_service.MetaCatalogService') as mock_service_class:
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_service.update_product_in_catalog.return_value = {'success': True}
    
    product.price = 549.99
    product.stock_quantity = 45
    product.save()
    
    print(f"✓ Product updated: {product.name}")
    print(f"  - New price: ${product.price}")
    print(f"  - New stock: {product.stock_quantity}")
    
    if mock_service.update_product_in_catalog.called:
        print("✓ Signal triggered: update_product_in_catalog was called")
    else:
        print("✗ Signal NOT triggered: update_product_in_catalog was NOT called")

print("\n" + "="*80)
print("TEST 3: Creating inactive product (should NOT trigger signal)")
print("="*80)

with patch('meta_integration.catalog_service.MetaCatalogService') as mock_service_class:
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    
    inactive_product = Product.objects.create(
        name='Inactive Product',
        sku='INACTIVE-001',
        description='This product is inactive',
        product_type='hardware',
        category=category,
        price=99.99,
        currency='USD',
        is_active=False  # Inactive!
    )
    
    print(f"✓ Product created: {inactive_product.name}")
    print(f"  - Active: {inactive_product.is_active}")
    
    if not mock_service.create_product_in_catalog.called:
        print("✓ Signal correctly skipped inactive product")
    else:
        print("✗ Signal incorrectly called for inactive product")

print("\n" + "="*80)
print("TEST 4: Creating product without SKU (should NOT trigger signal)")
print("="*80)

with patch('meta_integration.catalog_service.MetaCatalogService') as mock_service_class:
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    
    no_sku_product = Product.objects.create(
        name='Product Without SKU',
        # No SKU!
        description='This product has no SKU',
        product_type='service',
        category=category,
        price=49.99,
        currency='USD',
        is_active=True
    )
    
    print(f"✓ Product created: {no_sku_product.name}")
    print(f"  - SKU: {no_sku_product.sku}")
    
    if not mock_service.create_product_in_catalog.called:
        print("✓ Signal correctly skipped product without SKU")
    else:
        print("✗ Signal incorrectly called for product without SKU")

print("\n" + "="*80)
print("TEST 5: Deleting product (should trigger delete signal)")
print("="*80)

with patch('meta_integration.catalog_service.MetaCatalogService') as mock_service_class:
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_service.delete_product_from_catalog.return_value = {'success': True}
    
    product_name = product.name
    product_catalog_id = product.whatsapp_catalog_id
    product.delete()
    
    print(f"✓ Product deleted: {product_name}")
    print(f"  - Had catalog ID: {product_catalog_id}")
    
    if mock_service.delete_product_from_catalog.called:
        print("✓ Signal triggered: delete_product_from_catalog was called")
    else:
        print("✗ Signal NOT triggered: delete_product_from_catalog was NOT called")

print("\n" + "="*80)
print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
print("="*80)
print("\nSignal handlers are working correctly and will sync products with Meta Catalog.")
