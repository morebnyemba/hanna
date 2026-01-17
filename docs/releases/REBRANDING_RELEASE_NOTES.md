# Hanna by Pfungwa - Release Notes

## Rebranding from AutoWhats to Hanna by Pfungwa

**Release Date:** December 18, 2024

### Overview
This release completes the comprehensive rebranding from "AutoWhats" to "Hanna by Pfungwa" and introduces centralized admin management through the frontend applications.

---

## Changes

### 1. Frontend Dashboard Branding
**Location:** `whatsapp-crm-frontend/`

- **Updated index.html:**
  - Page title changed to "Hanna by Pfungwa"
  - Meta description updated to reflect new brand
  - Author meta tag updated
  
- **Updated LoginPage.jsx:**
  - Footer copyright now shows "© [Year] Hanna by Pfungwa"

### 2. Backend Branding
**Location:** `whatsappcrm_backend/`

- **Django Settings (settings.py):**
  - `site_header`: Changed to "Hanna by Pfungwa"
  - `welcome_sign`: Changed to "Welcome to Hanna by Pfungwa Admin"
  
- **Landing Page (landing_page.html):**
  - Page title updated to "Hanna by Pfungwa Backend"
  - Welcome message and description updated

### 3. Admin Management Centralization

#### What Changed
The Django admin interface has been reconfigured to redirect users to the frontend dashboard for centralized management.

#### URLs
- **`/admin/`** → Redirects to frontend dashboard (https://dashboard.hanna.co.zw)
- **`/django-admin/`** → Direct access to Django admin (for development/debugging)

#### Configuration
A new setting has been added for environment flexibility:

```python
# In settings.py
FRONTEND_DASHBOARD_URL = os.getenv('FRONTEND_DASHBOARD_URL', 'https://dashboard.hanna.co.zw')
```

**Environment Variable:**
- `FRONTEND_DASHBOARD_URL` - URL to redirect admin requests to (default: https://dashboard.hanna.co.zw)

#### For Developers
If you need to access the Django admin interface for development or debugging:
1. Navigate to: `https://backend.hanna.co.zw/django-admin/`
2. Log in with your superuser credentials

---

## Migration Guide

### For Administrators
1. **Accessing Management Features:**
   - Use the frontend dashboard at https://dashboard.hanna.co.zw
   - All management features are centralized in the React dashboard
   - The Next.js management frontend at https://hanna.co.zw provides additional admin capabilities

2. **Bookmarks/Links:**
   - Update any bookmarks from `backend.hanna.co.zw/admin/` to `dashboard.hanna.co.zw`

### For Developers
1. **Environment Variables:**
   - Add `FRONTEND_DASHBOARD_URL` to your `.env` files if you need to customize the redirect
   - For local development, you might want to set it to `http://localhost:5173`

2. **Django Admin Access:**
   - Use `/django-admin/` instead of `/admin/` for direct Django admin access
   - This is useful for database management, model inspection, and debugging

---

## Security

### Security Scan Results
✅ **CodeQL Security Scan: PASSED**
- No security vulnerabilities detected
- All changes have been validated for security issues

### Security Features Maintained
- HTTPS with Let's Encrypt SSL certificates
- Automatic certificate renewal
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS enabled
- OCSP stapling
- Security headers (X-Frame-Options, CSP, etc.)

---

## Testing

### Recommended Tests
1. **Frontend Dashboard:**
   - Verify login page displays new branding
   - Check footer copyright shows "Hanna by Pfungwa"
   - Confirm page title is "Hanna by Pfungwa"

2. **Backend:**
   - Navigate to `backend.hanna.co.zw/admin/` and verify redirect to dashboard
   - Navigate to `backend.hanna.co.zw/django-admin/` and verify Django admin loads
   - Check landing page shows updated branding

3. **API Functionality:**
   - Verify all API endpoints continue to work correctly
   - Test authentication flows
   - Confirm WebSocket connections work

---

## Rollback Plan

If you need to rollback these changes:

1. **Restore Admin Access:**
   ```python
   # In urls.py, change:
   path('admin/', AdminRedirectView.as_view(), name='admin_redirect'),
   # To:
   path('admin/', admin.site.urls),
   ```

2. **Revert Branding:**
   - Use git to revert the commits:
   ```bash
   git revert <commit-hash>
   ```

---

## Support

For issues or questions related to this release:
1. Check the updated documentation
2. Review service logs: `docker-compose logs <service>`
3. Open an issue on GitHub

---

## Contributors
- GitHub Copilot
- Project Maintainers

---

## Next Steps
- Update any external documentation or marketing materials
- Inform users of the rebranding
- Update email templates if they reference the old brand name
- Review and update any third-party integrations that display the brand name
