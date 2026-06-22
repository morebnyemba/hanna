# Media Files Diagnostic Script for Docker Setup (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Media Files Configuration Diagnostic" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Checking Docker containers..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "2. Checking media volume contents (from backend)..." -ForegroundColor Yellow
docker-compose exec backend ls -lah /app/mediafiles/

Write-Host ""
Write-Host "3. Checking media volume contents (from NPM)..." -ForegroundColor Yellow
docker-compose exec npm ls -lah /srv/www/media/

Write-Host ""
Write-Host "4. Creating test file from backend..." -ForegroundColor Yellow
docker-compose exec backend sh -c "echo 'Docker media test - created at `$(date)' > /app/mediafiles/docker-test.txt"
docker-compose exec backend cat /app/mediafiles/docker-test.txt

Write-Host ""
Write-Host "5. Checking if NPM sees the same file..." -ForegroundColor Yellow
docker-compose exec npm cat /srv/www/media/docker-test.txt

Write-Host ""
Write-Host "6. Testing Django media URL (internal)..." -ForegroundColor Yellow
Write-Host "Attempting to fetch: http://localhost:8000/media/docker-test.txt"
docker-compose exec backend curl -s http://localhost:8000/media/docker-test.txt

Write-Host ""
Write-Host "7. Checking Django settings..." -ForegroundColor Yellow
docker-compose exec backend python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings'); import django; django.setup(); from django.conf import settings; print(f'MEDIA_URL: {settings.MEDIA_URL}'); print(f'MEDIA_ROOT: {settings.MEDIA_ROOT}'); print(f'Exists: {settings.MEDIA_ROOT.exists()}')"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "If Django serves media internally but external access fails,"
Write-Host "check your Nginx Proxy Manager configuration at:"
Write-Host "http://your-server:81" -ForegroundColor Green
Write-Host ""
Write-Host "Ensure backend.hanna.co.zw forwards ALL paths to backend:8000"
Write-Host "==========================================" -ForegroundColor Cyan
