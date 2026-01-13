from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.ProductCategoryViewSet, basename='productcategory')
router.register(r'serialized-items', views.SerializedItemViewSet, basename='serializeditem')
router.register(r'barcode', views.BarcodeScanViewSet, basename='barcode')
router.register(r'cart', views.CartViewSet, basename='cart')
# Item tracking endpoints
router.register(r'items', views.ItemTrackingViewSet, basename='item-tracking')
# Item location history endpoints
router.register(r'item-location-history', views.ItemLocationHistoryViewSet, basename='item-location-history')
# Retailer portal endpoints (deprecated - for backward compatibility)
router.register(r'retailer', views.RetailerPortalViewSet, basename='retailer-portal')
# Retailer Branch portal endpoints (main portal for branch operations)
router.register(r'retailer-branch', views.RetailerBranchPortalViewSet, basename='retailer-branch-portal')
# System Bundle endpoints
router.register(r'system-bundles', views.SystemBundleViewSet, basename='system-bundle')

app_name = 'products_and_services_api'

urlpatterns = [
    path('', include(router.urls)),
    path('csrf/', views.csrf_cookie, name='csrf-cookie'),
    path('admin/sync-zoho/', views.trigger_sync_view, name='sync-zoho'),
]
