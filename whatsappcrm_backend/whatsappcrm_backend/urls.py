# whatsappcrm_backend/whatsappcrm_backend/urls.py

from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView, TokenBlacklistView
from django.conf import settings
from django.conf.urls.static import static

# Import the custom view to replace the default one
from customer_data.views import MyTokenObtainPairView, UserRegistrationView
from stats.views import DashboardSummaryStatsAPIView
from warranty.views import ManufacturerDashboardStatsAPIView, ManufacturerJobCardListView, ManufacturerJobCardDetailView, ManufacturerWarrantyClaimListView
# Import the new landing page view and admin redirect
from .views import LandingPageView, AdminRedirectView

urlpatterns = [
    # Landing Page at the root
    path('', LandingPageView.as_view(), name='landing_page'),

    # Django Admin interface - redirected to frontend for centralized management
    # To access the Django admin for development, use a superuser account
    # and navigate directly to /django-admin/
    path('admin/', AdminRedirectView.as_view(), name='admin_redirect'),
    path('django-admin/', admin.site.urls),  # Alternative path for Django admin access if needed
    path('prometheus/', include('django_prometheus.urls')),
    # API endpoints for 'meta_integration' application
    # This includes:
    #   - The webhook receiver for Meta (e.g., /crm-api/meta/webhook/)
    #   - DRF APIs for MetaAppConfig and WebhookEventLog (e.g., /crm-api/meta/api/configs/)
    path('crm-api/meta/', include('meta_integration.urls', namespace='meta_integration_api')),
    
    path('crm-api/media/', include('media_manager.urls', namespace='media_manager_api')),
    
    path('crm-api/conversations/', include('conversations.urls', namespace='conversations_api')),
path('crm-api/customer-data/', include('customer_data.urls', namespace='customer_data_api')),
    path('crm-api/stats/', include('stats.urls', namespace='stats_api')),
    path('crm-api/analytics/', include('analytics.urls')),
    # API endpoints for 'flows' application
    path('crm-api/flows/', include('flows.urls', namespace='flows_api')),
    path('crm-api/', include('warranty.urls', namespace='warranty_api')),
    path('crm-api/products/', include('products_and_services.urls', namespace='products_and_services_api')),
    path('crm-api/users/', include('users.urls', namespace='users_api')),
    path('crm-api/paynow/', include('paynow_integration.urls', namespace='paynow_integration_api')),


    # JWT Token Endpoints for authentication from your React Vite frontend
    # Use our custom view to ensure refresh token and user data are returned
    path('crm-api/auth/register/', UserRegistrationView.as_view(), name='user_registration'),
    path('crm-api/auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),    
    # The admin dashboard overview now uses the more comprehensive summary view from the 'stats' app.
    # This keeps the endpoint stable while improving the data source.
    path('crm-api/admin/dashboard-stats/', DashboardSummaryStatsAPIView.as_view(), name='admin_dashboard_stats'),
    path('crm-api/admin/warranty/', include('warranty.admin_urls', namespace='warranty_admin_api')),




    # Your frontend will POST to 'token_refresh' with a valid refresh token
    path('crm-api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Optional: Your frontend can POST to 'token_verify' with a token to check its validity
    path('crm-api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Add the blacklist endpoint to fix 404 on logout
    path('crm-api/auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # DRF's built-in login/logout views for the browsable API.
    # These are helpful for testing your APIs directly in the browser during development.
    # They use SessionAuthentication.
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# --- Serve Media Files ---
# In this setup with Nginx Proxy Manager, media requests are proxied to Django.
# We serve media files via Django even in production mode since NPM proxies all requests.
# For optimal performance in production, consider configuring NPM to serve media files
# directly from a shared volume, or use a CDN.

# NOTE: The static() helper only works when DEBUG=True. Since we need to serve media
# files in production (DEBUG=False), we explicitly add the URL pattern.
# This is necessary because NPM proxies /media/ requests to Django.
if settings.DEBUG:
    # Use the helper in debug mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production (DEBUG=False), explicitly serve media files through Django
    # Using re_path to match any path under /media/
    from django.views.static import serve
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]

# Note on Namespaces:
# The 'namespace' argument in include() is useful for URL reversing 
# (e.g., using reverse('meta_integration_api:meta_webhook_receiver') in Python code).
# It helps avoid URL name collisions between apps.
