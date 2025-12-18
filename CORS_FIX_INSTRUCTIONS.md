# CORS Error Fix - Implementation Guide

## Problem Summary

The frontend at `https://dashboard.hanna.co.zw` was unable to access the backend API at `https://backend.hanna.co.zw/crm-api/auth/token/` due to:

1. **CORS Policy Error**: Browser blocking requests due to missing `Access-Control-Allow-Origin` header
2. **Nginx Configuration Error**: Nginx container failing to start with error:
   ```
   [emerg] "add_header" directive is not allowed here in /etc/nginx/conf.d/default.conf:115
   ```

## Root Cause

The nginx configuration had CORS headers being added in multiple places, including inside an `if` block which is not allowed in nginx. Additionally, having nginx handle CORS headers was conflicting with Django's `django-cors-headers` middleware, leading to inconsistent CORS behavior.

## Solution Implemented

### 1. Nginx Configuration Changes (`nginx_proxy/nginx.conf`)

**Removed:**
- CORS origin mapping (`map $http_origin $cors_origin` block)
- All `add_header` CORS directives from the backend server block
- The problematic `if ($request_method = 'OPTIONS')` block containing `add_header` directives

**Result:**
- Nginx now acts as a simple reverse proxy
- No CORS headers are added by nginx
- All CORS handling is delegated to Django

### 2. Django Settings Enhancement (`whatsappcrm_backend/whatsappcrm_backend/settings.py`)

**Added explicit CORS configuration:**

```python
# Explicitly define allowed methods for CORS
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Explicitly define allowed headers for CORS
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

**Existing configuration (already correct):**
```python
CORS_ALLOWED_ORIGINS = [
    'https://dashboard.hanna.co.zw',
    'http://dashboard.hanna.co.zw',
    'https://hanna.co.zw',
    # ... development origins
]
CORS_ALLOW_CREDENTIALS = True
```

## How It Works

1. **Browser makes request** from `https://dashboard.hanna.co.zw` to `https://backend.hanna.co.zw/crm-api/auth/token/`
2. **Nginx receives the request** and forwards it to Django backend (no CORS headers added)
3. **Django's CorsMiddleware processes the request:**
   - Checks if origin is in `CORS_ALLOWED_ORIGINS`
   - If allowed, adds appropriate CORS headers to the response
   - Handles OPTIONS preflight requests automatically
4. **Browser receives response** with proper CORS headers and allows the request

## Deployment Steps

To apply this fix:

1. **Pull the latest changes:**
   ```bash
   git pull origin copilot/fix-cors-policy-error
   ```

2. **Restart the services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **Verify nginx starts successfully:**
   ```bash
   docker-compose logs nginx
   ```
   Should see: `Configuration complete; ready for start up` without any `[emerg]` errors

4. **Test the frontend:**
   - Open `https://dashboard.hanna.co.zw` in browser
   - Open browser console (F12)
   - Try logging in or making API requests
   - Should see successful requests without CORS errors

## Verification

### Check Nginx Status
```bash
docker-compose ps nginx
# Should show "Up" status
```

### Check Nginx Logs
```bash
docker-compose logs nginx | grep -i error
# Should not show any "add_header" errors
```

### Test CORS Headers
```bash
curl -I -X OPTIONS https://backend.hanna.co.zw/crm-api/auth/token/ \
  -H "Origin: https://dashboard.hanna.co.zw" \
  -H "Access-Control-Request-Method: POST"
```

Expected response headers:
```
Access-Control-Allow-Origin: https://dashboard.hanna.co.zw
Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: accept, accept-encoding, authorization, content-type, dnt, origin, user-agent, x-csrftoken, x-requested-with
Access-Control-Allow-Credentials: true
```

## Troubleshooting

### If CORS errors persist:

1. **Check Django settings:**
   ```bash
   docker-compose exec backend python manage.py shell
   ```
   ```python
   from django.conf import settings
   print(settings.CORS_ALLOWED_ORIGINS)
   print(settings.CORS_ALLOW_CREDENTIALS)
   ```

2. **Verify middleware order:**
   - `CorsMiddleware` should be early in the MIDDLEWARE list
   - It's currently placed correctly in settings.py

3. **Check environment variables:**
   ```bash
   docker-compose exec backend env | grep CORS
   ```

4. **Browser cache:**
   - Clear browser cache and cookies
   - Try in incognito/private mode
   - Hard refresh (Ctrl+F5)

## Additional Notes

- Django's `django-cors-headers` middleware handles both simple and preflight (OPTIONS) requests automatically
- The middleware is well-tested and maintained, making it the preferred approach over manual nginx CORS configuration
- This approach centralizes CORS logic in one place (Django), making it easier to maintain and debug
- Security headers (HSTS, X-Content-Type-Options, etc.) are still handled by nginx as they should be

## References

- [django-cors-headers documentation](https://github.com/adamchainz/django-cors-headers)
- [MDN CORS documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Nginx add_header directive](http://nginx.org/en/docs/http/ngx_http_headers_module.html#add_header)
