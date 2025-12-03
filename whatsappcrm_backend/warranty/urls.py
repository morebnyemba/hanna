from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ManufacturerDashboardStatsAPIView, 
    TechnicianDashboardStatsAPIView,
    AdminWarrantyClaimListView,
    AdminWarrantyClaimCreateView,
    ManufacturerWarrantyClaimListView,
    ManufacturerWarrantyClaimDetailView,
    ManufacturerJobCardListView,
    ManufacturerJobCardDetailView,
    ManufacturerProductListView,
    ManufacturerProfileView,
    ManufacturerProductViewSet,
    ManufacturerWarrantyViewSet,
    ManufacturerProductTrackingView,
    TechnicianJobCardViewSet,
    TechnicianInstallationHistoryView,
    TechnicianInstallationDetailView,
)

app_name = 'warranty_api'

router = DefaultRouter()
router.register(r'manufacturer/products', ManufacturerProductViewSet, basename='manufacturer-product')
router.register(r'manufacturer/warranties', ManufacturerWarrantyViewSet, basename='manufacturer-warranty')
router.register(r'technician/job-cards', TechnicianJobCardViewSet, basename='technician-job-card')

manufacturer_patterns = [
    path('dashboard-stats/', ManufacturerDashboardStatsAPIView.as_view(), name='manufacturer_dashboard_stats'),
    path('warranty-claims/', ManufacturerWarrantyClaimListView.as_view(), name='manufacturer_warranty_claims_list'),
    path('warranty-claims/<str:claim_id>/', ManufacturerWarrantyClaimDetailView.as_view(), name='manufacturer_warranty_claim_detail'),
    path('job-cards/', ManufacturerJobCardListView.as_view(), name='manufacturer_job_cards_list'),
    path('job-cards/<str:job_card_number>/', ManufacturerJobCardDetailView.as_view(), name='manufacturer_job_card_detail'),
    path('products/', ManufacturerProductListView.as_view(), name='manufacturer_product_list'),
    path('product-tracking/', ManufacturerProductTrackingView.as_view(), name='manufacturer_product_tracking'),
    path('profile/', ManufacturerProfileView.as_view(), name='manufacturer_profile'),
]

technician_patterns = [
    path('installation-history/', TechnicianInstallationHistoryView.as_view(), name='technician_installation_history'),
    path('installation-history/<int:pk>/', TechnicianInstallationDetailView.as_view(), name='technician_installation_detail'),
]

urlpatterns = [
    path('manufacturer/', include(manufacturer_patterns)),
    path('technician/', include(technician_patterns)),
    path('dashboards/technician/', TechnicianDashboardStatsAPIView.as_view(), name='technician_dashboard_stats'),
    path('claims/', AdminWarrantyClaimListView.as_view(), name='admin_warranty_claims_list'),
    path('claims/create/', AdminWarrantyClaimCreateView.as_view(), name='admin_warranty_claim_create'),
    path('', include(router.urls)),
]