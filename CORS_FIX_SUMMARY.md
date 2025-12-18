# CORS Fix Summary

## Problem
The frontend at `https://dashboard.hanna.co.zw` was unable to access the backend API at `https://backend.hanna.co.zw` due to the following error:

```
Access to XMLHttpRequest at 'https://backend.hanna.co.zw/crm-api/auth/token/' from origin 'https://dashboard.hanna.co.zw' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
While Django had `django-cors-headers` properly configured in `settings.py`, the Nginx reverse proxy was not passing through or adding the necessary CORS headers to the responses. This caused the browser to block cross-origin requests from the frontend to the backend.

## Solution
Added CORS headers to the Nginx configuration for the backend server block:

### 1. Map Directive for Multiple Origins
Added a map directive at the top of `nginx_proxy/nginx.conf` to dynamically set allowed origins based on the request origin:

```nginx
map $http_origin $cors_origin {
    default "";
    "~^https://dashboard\.hanna\.co\.zw$" $http_origin;
    "~^https://hanna\.co\.zw$" $http_origin;
    "~^http://localhost:5173$" $http_origin;
    "~^http://127\.0\.0\.1:5173$" $http_origin;
}
```

### 2. CORS Headers in Backend Server Block
Added CORS headers to allow cross-origin requests:

```nginx
add_header 'Access-Control-Allow-Origin' $cors_origin always;
add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, PATCH, DELETE, OPTIONS' always;
add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, Accept, Origin, X-Requested-With' always;
add_header 'Access-Control-Allow-Credentials' 'true' always;
add_header 'Access-Control-Max-Age' '3600' always;
```

### 3. OPTIONS Preflight Handler
Added a handler for OPTIONS requests to properly respond to CORS preflight requests:

```nginx
if ($request_method = 'OPTIONS') {
    add_header 'Access-Control-Allow-Origin' $cors_origin always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, PATCH, DELETE, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, Accept, Origin, X-Requested-With' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    add_header 'Access-Control-Max-Age' '3600' always;
    add_header 'Content-Type' 'text/plain; charset=utf-8';
    add_header 'Content-Length' '0';
    return 204;
}
```

## How to Apply
1. The changes have been made to `nginx_proxy/nginx.conf`
2. To apply the changes in production:
   ```bash
   # Restart the Nginx container
   docker-compose restart nginx_proxy
   
   # OR reload Nginx configuration without downtime
   docker-compose exec nginx_proxy nginx -s reload
   ```

## Verification
After applying the changes, verify that:
1. The frontend can successfully make requests to the backend API
2. The browser console no longer shows CORS errors
3. Authentication endpoints like `/crm-api/auth/token/` are accessible

You can verify CORS headers are present using curl:
```bash
curl -I -X OPTIONS \
  -H "Origin: https://dashboard.hanna.co.zw" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization, Content-Type" \
  https://backend.hanna.co.zw/crm-api/auth/token/
```

Expected response should include:
- `Access-Control-Allow-Origin: https://dashboard.hanna.co.zw`
- `Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS`
- `Access-Control-Allow-Credentials: true`

## Security Considerations
- Only explicitly allowed origins can access the backend API
- The map directive ensures that requests from unknown origins won't get valid CORS headers
- Credentials (cookies, authorization headers) are allowed for authenticated requests
- The configuration follows security best practices for CORS implementation

## Allowed Origins
The following origins are allowed to access the backend:
- `https://dashboard.hanna.co.zw` - Main frontend dashboard
- `https://hanna.co.zw` - Management frontend
- `http://localhost:5173` - Local development (frontend dev server)
- `http://127.0.0.1:5173` - Local development (alternative)

To add new origins, update the map directive in `nginx_proxy/nginx.conf` and ensure they're also listed in the Django `CORS_ALLOWED_ORIGINS` setting.
