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
)

app_name = 'warranty_api'

router = DefaultRouter()
router.register(r'manufacturer/products', ManufacturerProductViewSet, basename='manufacturer-product')

manufacturer_patterns = [
    path('dashboard-stats/', ManufacturerDashboardStatsAPIView.as_view(), name='manufacturer_dashboard_stats'),
    path('warranty-claims/', ManufacturerWarrantyClaimListView.as_view(), name='manufacturer_warranty_claims_list'),
    path('warranty-claims/<str:claim_id>/', ManufacturerWarrantyClaimDetailView.as_view(), name='manufacturer_warranty_claim_detail'),
    path('job-cards/', ManufacturerJobCardListView.as_view(), name='manufacturer_job_cards_list'),
    path('job-cards/<str:job_card_number>/', ManufacturerJobCardDetailView.as_view(), name='manufacturer_job_card_detail'),
    path('products/', ManufacturerProductListView.as_view(), name='manufacturer_product_list'),
    path('profile/', ManufacturerProfileView.as_view(), name='manufacturer_profile'),
]

urlpatterns = [
    path('manufacturer/', include(manufacturer_patterns)),
    path('dashboards/technician/', TechnicianDashboardStatsAPIView.as_view(), name='technician_dashboard_stats'),
    path('claims/', AdminWarrantyClaimListView.as_view(), name='admin_warranty_claims_list'),
    path('claims/create/', AdminWarrantyClaimCreateView.as_view(), name='admin_warranty_claim_create'),
    path('', include(router.urls)),
]