#!/usr/bin/env python3
"""
Validation script for google_product_category changes.
This script validates the changes without requiring a full Django setup.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'whatsappcrm_backend'))

def validate_model_changes():
    """Validate that the ProductCategory model has the google_product_category field"""
    print("✓ Checking ProductCategory model for google_product_category field...")
    
    with open('whatsappcrm_backend/products_and_services/models.py', 'r') as f:
        content = f.read()
        
    # Check for the field definition in ProductCategory
    if 'google_product_category' not in content:
        print("✗ FAIL: google_product_category field not found in models")
        return False
    
    # Check it's in ProductCategory, not Product
    # Find ProductCategory class and check field is there
    category_section = content.split('class ProductCategory')[1].split('class Product(')[0]
    if 'google_product_category' not in category_section:
        print("✗ FAIL: google_product_category field not in ProductCategory model")
        return False
    
    # Check it's NOT in Product model
    product_section = content.split('class Product(')[1].split('class ProductImage')[0]
    if 'google_product_category' in product_section:
        print("✗ FAIL: google_product_category field should not be in Product model")
        return False
        
    print("  ✓ google_product_category field found in ProductCategory model")
    print("  ✓ google_product_category field correctly NOT in Product model")
    return True

def validate_admin_changes():
    """Validate admin.py changes"""
    print("\n✓ Checking admin.py changes...")
    
    with open('whatsappcrm_backend/products_and_services/admin.py', 'r') as f:
        content = f.read()
    
    # Check that filter_horizontal line was removed
    if 'filter_horizontal = (\'products\',)' in content:
        print("✗ FAIL: filter_horizontal line still present (should be removed)")
        return False
    
    print("  ✓ filter_horizontal line removed")
    
    # Check that google_product_category is in ProductCategoryAdmin
    category_admin_section = content.split('class ProductCategoryAdmin')[1].split('class ProductImageInline')[0]
    if 'google_product_category' not in category_admin_section:
        print("✗ FAIL: google_product_category not added to ProductCategoryAdmin")
        return False
    
    print("  ✓ google_product_category added to ProductCategoryAdmin")
    
    # Check that google_product_category is NOT in ProductAdmin fieldsets
    product_admin_section = content.split('class ProductAdmin')[1]
    # Look specifically in fieldsets for google_product_category on Product
    if 'fieldsets' in product_admin_section:
        fieldsets_section = product_admin_section.split('fieldsets')[1].split('readonly_fields')[0]
        if 'google_product_category' in fieldsets_section:
            print("✗ FAIL: google_product_category should not be in ProductAdmin fieldsets")
            return False
    
    print("  ✓ google_product_category correctly NOT in ProductAdmin")
    return True

def validate_catalog_service_changes():
    """Validate catalog_service.py changes"""
    print("\n✓ Checking catalog_service.py changes...")
    
    with open('whatsappcrm_backend/meta_integration/catalog_service.py', 'r') as f:
        content = f.read()
    
    # Check for google_product_category in documentation
    if 'google_product_category' not in content:
        print("✗ FAIL: google_product_category not mentioned in catalog_service.py")
        return False
    
    # Check that it's getting category from product.category.google_product_category
    if 'product.category.google_product_category' not in content:
        print("✗ FAIL: catalog service should use product.category.google_product_category")
        return False
    
    # Make sure it's NOT using product.google_product_category directly
    if 'if product.google_product_category:' in content:
        print("✗ FAIL: catalog service should not use product.google_product_category directly")
        return False
    
    print("  ✓ google_product_category integrated correctly via product.category")
    return True

def validate_test_changes():
    """Validate test additions"""
    print("\n✓ Checking test additions...")
    
    with open('whatsappcrm_backend/meta_integration/tests.py', 'r') as f:
        content = f.read()
    
    # Check for GoogleProductCategoryTestCase
    if 'GoogleProductCategoryTestCase' not in content:
        print("✗ FAIL: GoogleProductCategoryTestCase test class not found")
        return False
    
    # Check for updated test methods (reflecting category-based approach)
    expected_tests = [
        'test_product_with_google_category_includes_in_payload',
        'test_product_without_category_excludes_google_category_from_payload',
        'test_product_with_category_without_google_mapping_excludes_from_payload'
    ]
    
    for test in expected_tests:
        if test not in content:
            print(f"✗ FAIL: Test method {test} not found")
            return False
    
    print("  ✓ All test cases added (category-based approach)")
    return True

def validate_documentation():
    """Validate documentation"""
    print("\n✓ Checking documentation...")
    
    if not os.path.exists('GOOGLE_PRODUCT_CATEGORY_GUIDE.md'):
        print("✗ FAIL: GOOGLE_PRODUCT_CATEGORY_GUIDE.md not found")
        return False
    
    with open('GOOGLE_PRODUCT_CATEGORY_GUIDE.md', 'r') as f:
        content = f.read()
    
    # Check for key sections
    expected_sections = [
        'Overview',
        'How to Set Product Category',
        'Best Practices',
        'Meta Catalog',
        'Migration Note'
    ]
    
    for section in expected_sections:
        if section not in content:
            print(f"✗ FAIL: Documentation missing section: {section}")
            return False
    
    print("  ✓ Documentation complete")
    return True

def main():
    """Run all validations"""
    print("=" * 60)
    print("Validating google_product_category changes")
    print("=" * 60)
    
    results = [
        validate_model_changes(),
        validate_admin_changes(),
        validate_catalog_service_changes(),
        validate_test_changes(),
        validate_documentation()
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL VALIDATIONS PASSED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: cd whatsappcrm_backend && python manage.py makemigrations products_and_services")
        print("2. Run: python manage.py migrate")
        print("3. Run: python manage.py test meta_integration.tests.GoogleProductCategoryTestCase")
        print("4. Update products with google_product_category via Django Admin")
        print("5. Sync products to Meta Catalog")
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
