# CORS Fix Deployment Guide - Hanna Management Dashboard

## Issue Fixed
**Problem**: CORS error when trying to login on the Hanna Management Dashboard at `https://hanna.co.zw`

**Error Message**:
```
Access to fetch at 'https://backend.hanna.co.zw/crm-api/auth/token/' from origin 'https://hanna.co.zw' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
The `loginAction` function in the Next.js management frontend was making a fetch request without the `credentials: 'include'` option, which is required for cross-origin requests with credentials.

## Changes Made

### File Modified
**`hanna-management-frontend/app/store/authStore.ts`** (line 83)

**Before**:
```typescript
const response = await fetch(`${apiUrl}/crm-api/auth/token/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password }),
});
```

**After**:
```typescript
const response = await fetch(`${apiUrl}/crm-api/auth/token/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password }),
  credentials: 'include', // Required for CORS requests with cookies
});
```

## Deployment Steps

### Option 1: Docker Compose (Recommended for Production)

1. **Pull the latest changes**:
   ```bash
   cd /path/to/hanna
   git pull origin <branch-name>
   ```

2. **Rebuild the management frontend container**:
   ```bash
   docker-compose build hanna-management-frontend
   ```

3. **Restart the container**:
   ```bash
   docker-compose up -d hanna-management-frontend
   ```

4. **Verify the container is running**:
   ```bash
   docker-compose ps hanna-management-frontend
   docker-compose logs -f hanna-management-frontend
   ```

### Option 2: Full Stack Restart (If Issues Persist)

If you encounter any issues, restart the entire stack:

```bash
docker-compose down
docker-compose up -d
```

Then check all services are running:
```bash
docker-compose ps
```

## Verification

### 1. Browser Console Test
1. Open `https://hanna.co.zw/admin/login` in a browser
2. Open browser DevTools (F12) → Console tab
3. Enter valid admin credentials
4. Click Login
5. **Expected**: No CORS errors in console
6. **Expected**: Successful redirect to dashboard

### 2. Network Tab Test
1. Open browser DevTools (F12) → Network tab
2. Try to login
3. Look for the request to `/crm-api/auth/token/`
4. **Expected**: Status 200 (success)
5. **Expected**: Response contains `access` and `refresh` tokens

### 3. CORS Headers Test (Optional)
Use curl to verify CORS headers:

```bash
curl -I -X OPTIONS https://backend.hanna.co.zw/crm-api/auth/token/ \
  -H "Origin: https://hanna.co.zw" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

**Expected headers in response**:
```
Access-Control-Allow-Origin: https://hanna.co.zw
Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Credentials: true
```

## Troubleshooting

### Issue: Still Getting CORS Errors

**Check 1 - Backend Configuration**:
```bash
docker-compose exec backend python manage.py shell
```
```python
from django.conf import settings
print(settings.CORS_ALLOWED_ORIGINS)
print(settings.CORS_ALLOW_CREDENTIALS)
```

Should see:
```python
['https://dashboard.hanna.co.zw', 'http://dashboard.hanna.co.zw', 'https://hanna.co.zw']
True
```

**Check 2 - Environment Variables**:
```bash
docker-compose exec backend env | grep CORS
```

Should see:
```
CORS_ALLOWED_ORIGINS=https://dashboard.hanna.co.zw,http://dashboard.hanna.co.zw,https://hanna.co.zw
```

**Check 3 - Container Logs**:
```bash
docker-compose logs -f backend | grep -i cors
docker-compose logs -f hanna-management-frontend
docker-compose logs -f nginx
```

### Issue: Login Works But Session Not Persisting

This is a separate issue from CORS. Check:
1. Cookie settings in Django (`SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE`)
2. Browser blocking third-party cookies
3. Cookie domain configuration

### Issue: 404 or Connection Refused

Check nginx is routing correctly:
```bash
docker-compose logs nginx | grep hanna.co.zw
```

Verify nginx configuration:
```bash
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf | grep hanna.co.zw
```

## Rollback Plan

If issues occur after deployment:

1. **Quick rollback**:
   ```bash
   git revert <commit-hash>
   docker-compose build hanna-management-frontend
   docker-compose up -d hanna-management-frontend
   ```

2. **Full rollback**:
   ```bash
   git checkout <previous-commit>
   docker-compose down
   docker-compose up -d
   ```

## Technical Background

### Why `credentials: 'include'` Is Required

1. **CORS Preflight**: Modern browsers send an OPTIONS preflight request before POST requests to different origins
2. **Credentials Flag**: Without `credentials: 'include'`, the browser won't send cookies or set response cookies
3. **Django CORS**: Django's `django-cors-headers` middleware checks for credentials and adds appropriate headers
4. **Security**: This is a security feature to prevent unauthorized cross-origin requests

### Why the Backend Configuration Was Already Correct

The Django backend already had:
- ✅ `django-cors-headers` installed and configured
- ✅ `https://hanna.co.zw` in `CORS_ALLOWED_ORIGINS`
- ✅ `CORS_ALLOW_CREDENTIALS = True`
- ✅ Correct middleware order
- ✅ Nginx delegating CORS to Django

The issue was **only** on the frontend side - the fetch request needed the credentials option.

## Security Note

✅ **Security scan completed**: CodeQL found no vulnerabilities in the changed code.

The `credentials: 'include'` option is safe because:
1. The backend explicitly whitelists allowed origins
2. Django validates the Origin header on every request
3. CSRF protection is still enforced for state-changing operations
4. This is the recommended approach for modern web applications with separate frontend/backend domains

## Support

If you encounter any issues during deployment:
1. Check the logs using the commands above
2. Verify the browser console shows the request with the correct headers
3. Ensure the Django backend environment variables are correct
4. Test with curl to isolate whether it's a browser or server issue

## Related Documentation

- [CORS_FIX_INSTRUCTIONS.md](./CORS_FIX_INSTRUCTIONS.md) - Previous CORS fixes
- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)
- [MDN CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Fetch API Credentials](https://developer.mozilla.org/en-US/docs/Web/API/fetch#credentials)
