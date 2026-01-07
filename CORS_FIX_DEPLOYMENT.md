# CORS Fix Deployment Guide

## Problem
The management dashboard at `https://hanna.co.zw` was unable to log in to the backend at `https://backend.hanna.co.zw` with the error:

```
Access to fetch at 'https://backend.hanna.co.zw/crm-api/auth/token/' from origin 'https://hanna.co.zw' 
has been blocked by CORS policy: Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
- Browser sends OPTIONS preflight request before POST login request
- Nginx was not handling OPTIONS requests properly for CORS
- Django's CORS middleware handles regular requests but preflight requests need nginx-level handling for efficiency

## Solution Implemented
Updated `nginx_proxy/nginx.conf` to:
1. Add a map directive to validate allowed origins
2. Add OPTIONS request handler in the backend server block to return proper CORS headers
3. Allow specific origins: `https://dashboard.hanna.co.zw`, `https://hanna.co.zw`, and localhost for development

## Deployment Steps

### 1. Verify Changes
```bash
# Check that nginx config has the CORS map directive
grep -A 5 "map.*cors_origin" nginx_proxy/nginx.conf

# Check that OPTIONS handler is present
grep -A 10 "request_method.*OPTIONS" nginx_proxy/nginx.conf
```

### 2. Test Nginx Configuration
```bash
# Test nginx config syntax in the container
docker-compose exec nginx_proxy nginx -t

# Should output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 3. Apply Changes
```bash
# Option 1: Reload nginx without downtime (recommended)
docker-compose exec nginx_proxy nginx -s reload

# Option 2: Restart the nginx container (if reload fails)
docker-compose restart nginx_proxy

# Wait a few seconds for nginx to reload
sleep 5
```

### 4. Verify CORS Headers
Test that the CORS preflight request works:

```bash
# Test from management dashboard origin
curl -v -X OPTIONS \
  -H "Origin: https://hanna.co.zw" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization, Content-Type" \
  https://backend.hanna.co.zw/crm-api/auth/token/

# Should return:
# HTTP/1.1 204 No Content
# Access-Control-Allow-Origin: https://hanna.co.zw
# Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
# Access-Control-Allow-Credentials: true
# Access-Control-Allow-Headers: Authorization, Content-Type, Accept, Origin, X-Requested-With, X-CSRFToken
# Access-Control-Max-Age: 3600
```

Test from dashboard origin:
```bash
curl -v -X OPTIONS \
  -H "Origin: https://dashboard.hanna.co.zw" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization, Content-Type" \
  https://backend.hanna.co.zw/crm-api/auth/token/

# Should also return CORS headers
```

Test with unauthorized origin (should not have valid CORS headers):
```bash
curl -v -X OPTIONS \
  -H "Origin: https://unauthorized.com" \
  -H "Access-Control-Request-Method: POST" \
  https://backend.hanna.co.zw/crm-api/auth/token/

# Should return 204 but with Access-Control-Allow-Origin: (empty)
# Browser will reject this as invalid CORS per specification
```

### 5. Test Login Functionality
1. Open browser and navigate to `https://hanna.co.zw/admin/login`
2. Open browser developer tools (F12) → Network tab
3. Enter valid admin credentials and click "Sign in"
4. Verify:
   - No CORS errors in console
   - POST request to `/crm-api/auth/token/` succeeds
   - You're redirected to the admin dashboard

## Security Considerations
- **Origin Validation**: Only explicitly allowed origins receive valid CORS headers
- **Empty Origin Handling**: Unauthorized origins get an empty `Access-Control-Allow-Origin` header, which is invalid per CORS specification and causes browsers to block the request
- **Map Directive**: The map directive ensures that requests from unknown origins are automatically rejected by setting an invalid CORS header value
- **Credentials**: Cookies and authorization headers are allowed only for origins that match the allowed list
- **Development Origins**: Localhost origins (http://localhost:5173 and http://127.0.0.1:5173) are only accessible during local development and won't match in production since browsers send the actual HTTPS origin
- **No Wildcards**: The configuration does not use wildcards (*) for origins, ensuring explicit control over which domains can access the API
- **Follows CORS Best Practices**: Implementation aligns with W3C CORS specification and OWASP security guidelines

## Allowed Origins
The following origins are configured to access the backend:
- `https://dashboard.hanna.co.zw` - React dashboard frontend
- `https://hanna.co.zw` - Next.js management frontend
- `http://localhost:5173` - Local development (Vite dev server)
- `http://127.0.0.1:5173` - Local development (alternative)

## Adding New Origins
To add a new origin:

1. Update the map directive in `nginx_proxy/nginx.conf`:
```nginx
map $http_origin $cors_origin {
    default "";
    "~^https://dashboard\.hanna\.co\.zw$" $http_origin;
    "~^https://hanna\.co\.zw$" $http_origin;
    "~^https://your-new-origin\.com$" $http_origin;  # Add this line
    "~^http://localhost:5173$" $http_origin;
    "~^http://127\.0\.0\.1:5173$" $http_origin;
}
```

2. Update Django CORS settings in `whatsappcrm_backend/.env.prod`:
```bash
CORS_ALLOWED_ORIGINS='https://dashboard.hanna.co.zw,http://dashboard.hanna.co.zw,https://hanna.co.zw,https://your-new-origin.com'
```

3. Reload nginx and restart the backend:
```bash
docker-compose exec nginx_proxy nginx -s reload
docker-compose restart backend
```

## Rollback Instructions
If the fix causes issues:

1. Revert the nginx configuration:
```bash
git revert HEAD
docker-compose exec nginx_proxy nginx -s reload
```

2. Or manually remove the CORS map and OPTIONS handler from `nginx_proxy/nginx.conf`

## Troubleshooting

### CORS errors still appear
- Check browser console for the exact error message
- Verify the origin in the error matches one of the allowed origins
- Check nginx logs: `docker-compose logs nginx_proxy`
- Check backend logs: `docker-compose logs backend`

### Nginx fails to reload
- Check nginx config syntax: `docker-compose exec nginx_proxy nginx -t`
- Check nginx logs for errors: `docker-compose logs nginx_proxy --tail=50`
- If syntax is invalid, fix and try again

### Login still fails
- Verify Django CORS settings: Check that `CORS_ALLOWED_ORIGINS` environment variable is set correctly in `.env.prod`
- Check if the backend is running: `docker-compose ps backend`
- Check backend logs: `docker-compose logs backend --tail=50`

## Related Files
- `nginx_proxy/nginx.conf` - Nginx configuration with CORS handling
- `whatsappcrm_backend/.env.prod` - Django environment variables including CORS settings
- `whatsappcrm_backend/whatsappcrm_backend/settings.py` - Django CORS configuration
- `hanna-management-frontend/app/store/authStore.ts` - Frontend authentication logic
- `hanna-management-frontend/app/lib/apiClient.ts` - Frontend API client with CORS settings

## References
- [MDN CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Django CORS Headers Documentation](https://github.com/adamchainz/django-cors-headers)
- [Nginx CORS Configuration Guide](https://enable-cors.org/server_nginx.html)
