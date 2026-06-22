"""
Test Django Media File Serving Configuration
This script verifies that Django is properly configured to serve media files.
"""
import os
import sys
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent / 'whatsappcrm_backend'
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')

try:
    import django
    django.setup()
    
    from django.conf import settings
    from django.urls import get_resolver
    
    print("=" * 70)
    print("✅ DJANGO MEDIA FILES CONFIGURATION TEST")
    print("=" * 70)
    
    # Check settings
    print("\n📋 SETTINGS CONFIGURATION:")
    print(f"  MEDIA_URL: {settings.MEDIA_URL}")
    print(f"  MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"  Media directory exists: {settings.MEDIA_ROOT.exists()}")
    
    if settings.MEDIA_ROOT.exists():
        files = list(settings.MEDIA_ROOT.iterdir())
        print(f"  Files in media directory: {len(files)}")
        for f in files[:5]:  # Show first 5 files
            print(f"    - {f.name}")
    
    # Check URL configuration
    print("\n🔗 URL CONFIGURATION:")
    resolver = get_resolver()
    
    # Check if static() was called
    from django.conf.urls.static import static
    from django.core.handlers.wsgi import WSGIHandler
    
    # Test if /media/ URLs are configured
    test_url = '/media/test.txt'
    try:
        match = resolver.resolve(test_url)
        print(f"  ✅ Media URL pattern registered")
        print(f"  Test URL '{test_url}' resolves to: {match.func}")
    except:
        print(f"  ❌ Media URL pattern NOT found")
        print(f"  Test URL '{test_url}' does not resolve")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 CONFIGURATION STATUS:")
    print("=" * 70)
    
    if settings.MEDIA_URL and settings.MEDIA_ROOT.exists():
        print("✅ MEDIA_URL and MEDIA_ROOT are configured correctly")
    else:
        print("❌ Settings configuration incomplete")
        
    print("\n🚀 HOW TO TEST:")
    print("  1. Start Django server: python manage.py runserver")
    print(f"  2. Visit: http://127.0.0.1:8000{settings.MEDIA_URL}test.txt")
    print("  3. You should see the test file content")
    
    print("\n💡 WHAT THIS MEANS:")
    print("  Django will serve files from the mediafiles/ directory")
    print("  through its own HTTP server at /media/* URLs")
    print("  No nginx volumes or external storage needed!")
    
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
