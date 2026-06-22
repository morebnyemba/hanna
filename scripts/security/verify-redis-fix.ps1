# Verify Redis Password Fix Script
# Run this on your production server to verify the Redis connection and backend status

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           Redis Password Verification Script                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get the new password from backup
Write-Host "═══ Step 1: Reading New Redis Password ═══" -ForegroundColor Yellow
Write-Host ""

if (Test-Path ".redis-password-backup") {
    $passwordLine = Get-Content ".redis-password-backup" | Select-String "REDIS_PASSWORD"
    $newPassword = ($passwordLine -split "=" | Select-Object -Last 1).Trim("'").Trim('"')
    Write-Host "✓ Found new password in backup file" -ForegroundColor Green
    Write-Host "  Password (first 8 chars): $($newPassword.Substring(0, [Math]::Min(8, $newPassword.Length)))..." -ForegroundColor Gray
} else {
    Write-Host "✗ Backup file not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Test Redis connection
Write-Host "═══ Step 2: Testing Redis Connection ═══" -ForegroundColor Yellow
Write-Host ""

try {
    Write-Host "Testing connection to Redis with new password..." -ForegroundColor Gray
    
    # Try to ping Redis with the new password
    $result = docker-compose exec -T redis redis-cli -a $newPassword ping 2>&1
    
    if ($result -match "PONG") {
        Write-Host "✓ Redis is responding correctly!" -ForegroundColor Green
        Write-Host "  Response: $result"
    } elseif ($result -match "WRONGPASS|NOAUTH") {
        Write-Host "✗ Authentication failed" -ForegroundColor Red
        Write-Host "  Response: $result"
        Write-Host ""
        Write-Host "Trying to verify password file was updated..." -ForegroundColor Yellow
        docker-compose exec -T redis cat /etc/redis/redis.conf | Select-String "requirepass"
    } else {
        Write-Host "? Unexpected response from Redis:" -ForegroundColor Yellow
        Write-Host "  Response: $result"
    }
} catch {
    Write-Host "✗ Error testing Redis: $_" -ForegroundColor Red
}

Write-Host ""

# Step 3: Check backend logs for Celery/Redis errors
Write-Host "═══ Step 3: Checking Backend Logs for Errors ═══" -ForegroundColor Yellow
Write-Host ""

Write-Host "Recent backend logs (last 50 lines):" -ForegroundColor Gray
$logs = docker-compose logs --tail=50 backend 2>&1
$logs | Where-Object { $_ -match "error|ERROR|redis|REDIS|FOuP|WRONGPASS|NOAUTH|connection" } | ForEach-Object {
    if ($_ -match "ERROR|error|WRONGPASS|NOAUTH|FOuP") {
        Write-Host "$_" -ForegroundColor Red
    } elseif ($_ -match "redis|REDIS|connection") {
        Write-Host "$_" -ForegroundColor Yellow
    } else {
        Write-Host "$_"
    }
}

Write-Host ""

# Step 4: Check if Celery tasks are queueing properly
Write-Host "═══ Step 4: Checking Celery Queue Status ═══" -ForegroundColor Yellow
Write-Host ""

try {
    $celeryLogs = docker-compose logs --tail=30 celery_io_worker 2>&1
    $celeryLogs | Where-Object { $_ -match "error|ERROR|connection|Connected" } | ForEach-Object {
        if ($_ -match "ERROR|error|connection failed") {
            Write-Host "$_" -ForegroundColor Red
        } else {
            Write-Host "$_" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "Could not check Celery logs: $_" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Summary and recommendations
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    Verification Complete                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. If Redis connection succeeded (PONG), the password reset worked!"
Write-Host "2. Monitor backend logs: docker-compose logs -f backend"
Write-Host "3. Look for 'Port could not be cast to integer value' errors - should be gone"
Write-Host "4. Celery tasks should now queue without errors"
Write-Host ""
Write-Host "To clean up:" -ForegroundColor Yellow
Write-Host "  rm .redis-password-backup   # Delete password backup file"
Write-Host ""
