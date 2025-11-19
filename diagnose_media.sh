#!/bin/bash
# Media Files Diagnostic Script for Docker Setup

echo "=========================================="
echo "Media Files Configuration Diagnostic"
echo "=========================================="
echo ""

echo "1. Checking Docker containers..."
docker-compose ps

echo ""
echo "2. Checking media volume contents (from backend)..."
docker-compose exec backend ls -lah /app/mediafiles/ 2>/dev/null || echo "Backend not running or error accessing path"

echo ""
echo "3. Checking media volume contents (from NPM)..."
docker-compose exec npm ls -lah /srv/www/media/ 2>/dev/null || echo "NPM not running or error accessing path"

echo ""
echo "4. Creating test file from backend..."
docker-compose exec backend sh -c "echo 'Docker media test - created at $(date)' > /app/mediafiles/docker-test.txt"
docker-compose exec backend cat /app/mediafiles/docker-test.txt

echo ""
echo "5. Checking if NPM sees the same file..."
docker-compose exec npm cat /srv/www/media/docker-test.txt 2>/dev/null || echo "NPM cannot see the file (path mismatch or volume issue)"

echo ""
echo "6. Testing Django media URL..."
echo "Attempting to fetch: http://backend:8000/media/docker-test.txt"
docker-compose exec backend curl -s http://localhost:8000/media/docker-test.txt || echo "Django not serving media files"

echo ""
echo "7. Checking Django settings..."
docker-compose exec backend python manage.py shell -c "
from django.conf import settings
print(f'MEDIA_URL: {settings.MEDIA_URL}')
print(f'MEDIA_ROOT: {settings.MEDIA_ROOT}')
print(f'Media directory exists: {settings.MEDIA_ROOT.exists()}')
" 2>/dev/null || echo "Cannot check Django settings"

echo ""
echo "8. Checking URL configuration..."
docker-compose exec backend python -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')
import django
django.setup()
from django.urls import get_resolver
try:
    match = get_resolver().resolve('/media/test.txt')
    print('✅ Media URL pattern registered')
except:
    print('❌ Media URL pattern NOT found')
" 2>/dev/null || echo "Cannot check URL configuration"

echo ""
echo "=========================================="
echo "Summary:"
echo "=========================================="
echo "If Django serves media internally but external access fails,"
echo "check your Nginx Proxy Manager configuration at:"
echo "http://your-server:81"
echo ""
echo "Ensure backend.hanna.co.zw forwards ALL paths to backend:8000"
echo "=========================================="
