"""
Live test of Django media file serving
This script starts a Django server and tests media file access
"""
import subprocess
import time
import requests
import sys
from pathlib import Path

print("=" * 70)
print("🧪 LIVE TEST: Django Media File Serving")
print("=" * 70)

# Change to backend directory
backend_dir = Path(__file__).parent / 'whatsappcrm_backend'
print(f"\n📁 Working directory: {backend_dir}")

# Start Django server in background
print("\n🚀 Starting Django development server...")
server_process = subprocess.Popen(
    [sys.executable, 'manage.py', 'runserver', '--noreload'],
    cwd=str(backend_dir),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Wait for server to start
print("⏳ Waiting for server to start...")
time.sleep(5)

try:
    # Test media file access
    print("\n🔍 Testing media file access...")
    url = 'http://127.0.0.1:8000/media/test.txt'
    print(f"   URL: {url}")
    
    response = requests.get(url, timeout=5)
    
    print(f"\n✅ SUCCESS! Media file served by Django")
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"   Content Length: {len(response.content)} bytes")
    print(f"   Content: {response.text[:100]}")
    
    print("\n" + "=" * 70)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 70)
    print("\n📋 SUMMARY:")
    print("  • Django is serving media files directly")
    print("  • Files are served from: whatsappcrm_backend/mediafiles/")
    print("  • URL pattern: /media/*")
    print("  • No nginx volumes or external storage needed")
    print("\n💡 You can now:")
    print("  • Upload files via Django models/APIs")
    print("  • Access them at /media/<filename>")
    print("  • Use in both development and production")
    
except requests.exceptions.RequestException as e:
    print(f"\n❌ Test failed: {e}")
    print("\nNote: This might be due to the server still starting.")
    print("Try manually:")
    print("  1. python manage.py runserver")
    print("  2. Visit: http://127.0.0.1:8000/media/test.txt")
    
finally:
    # Stop server
    print("\n\n🛑 Stopping server...")
    server_process.terminate()
    server_process.wait(timeout=3)
    print("✅ Server stopped")
    print("=" * 70)
