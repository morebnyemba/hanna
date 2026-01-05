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
    """Validate that the Product model has the google_product_category field"""
    print("✓ Checking Product model for google_product_category field...")
    
    with open('whatsappcrm_backend/products_and_services/models.py', 'r') as f:
        content = f.read()
        
    # Check for the field definition
    if 'google_product_category' not in content:
        print("✗ FAIL: google_product_category field not found in Product model")
        return False
    
    # Check for proper field type
    if 'models.CharField' not in content or 'Google Product Category' not in content:
        print("✗ FAIL: google_product_category field not properly defined")
        return False
        
    print("  ✓ google_product_category field found in Product model")
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
    
    # Check that google_product_category is in fieldsets
    if 'google_product_category' not in content:
        print("✗ FAIL: google_product_category not added to admin fieldsets")
        return False
    
    print("  ✓ google_product_category added to admin fieldsets")
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
    
    # Check that it's added to product data
    if 'product.google_product_category' not in content:
        print("✗ FAIL: product.google_product_category not used in _get_product_data")
        return False
    
    print("  ✓ google_product_category integrated in catalog service")
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
    
    # Check for test methods
    expected_tests = [
        'test_product_with_google_category_includes_in_payload',
        'test_product_without_google_category_excludes_from_payload',
        'test_product_with_category_id_includes_in_payload'
    ]
    
    for test in expected_tests:
        if test not in content:
            print(f"✗ FAIL: Test method {test} not found")
            return False
    
    print("  ✓ All test cases added")
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
