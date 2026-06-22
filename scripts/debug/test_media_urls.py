#!/usr/bin/env python3
"""
Test Django Media URL Configuration
Tests that media files can be served in both DEBUG=True and DEBUG=False modes
"""
import os
import sys
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent / 'whatsappcrm_backend'
sys.path.insert(0, str(BASE_DIR))

def test_urls(debug_mode):
    """Test URL configuration with specified DEBUG mode"""
    print(f"\n{'='*70}")
    print(f"Testing with DEBUG={debug_mode}")
    print('='*70)
    
    # Set DEBUG mode
    os.environ['DJANGO_DEBUG'] = str(debug_mode)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
    
    # Import Django after setting env vars
    import django
    if django.VERSION >= (1, 7):
        django.setup()
    
    from django.conf import settings
    from django.urls import get_resolver, resolve
    
    print(f"✓ Django loaded with DEBUG={settings.DEBUG}")
    print(f"  MEDIA_URL: {settings.MEDIA_URL}")
    print(f"  MEDIA_ROOT: {settings.MEDIA_ROOT}")
    
    # Test media URL resolution
    test_urls = [
        '/media/test.txt',
        '/media/product_images/test.png',
        '/media/attachments/file.pdf',
    ]
    
    print(f"\nTesting URL resolution:")
    all_passed = True
    
    for test_url in test_urls:
        try:
            match = resolve(test_url)
            print(f"  ✓ {test_url}")
            print(f"    → Resolves to: {match.func.__name__}")
            if hasattr(match, 'kwargs'):
                print(f"    → Path arg: {match.kwargs.get('path', 'N/A')}")
        except Exception as e:
            print(f"  ✗ {test_url}")
            print(f"    → Error: {e}")
            all_passed = False
    
    return all_passed

if __name__ == '__main__':
    print("="*70)
    print("Django Media URLs Test")
    print("="*70)
    
    # Test with DEBUG=False (production mode)
    prod_ok = test_urls(False)
    
    # Clear Django modules to reload with different settings
    for module in list(sys.modules.keys()):
        if module.startswith('django') or module.startswith('whatsappcrm_backend'):
            del sys.modules[module]
    
    # Test with DEBUG=True (development mode)
    dev_ok = test_urls(True)
    
    # Summary
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    
    if prod_ok and dev_ok:
        print("✓ All tests passed!")
        print("✓ Media URLs work in both DEBUG=True and DEBUG=False modes")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        if not prod_ok:
            print("✗ Media URLs not working in production mode (DEBUG=False)")
        if not dev_ok:
            print("✗ Media URLs not working in development mode (DEBUG=True)")
        sys.exit(1)
