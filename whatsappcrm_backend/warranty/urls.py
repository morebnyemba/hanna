from django.urls import path, include
from .views import (
    ManufacturerDashboardStatsAPIView, 
    TechnicianDashboardStatsAPIView,
    AdminWarrantyClaimListView,
    AdminWarrantyClaimCreateView,
    ManufacturerWarrantyClaimListView,
    ManufacturerJobCardListView,
    ManufacturerJobCardDetailView,
)

app_name = 'warranty_api'

manufacturer_patterns = [
    path('dashboard-stats/', ManufacturerDashboardStatsAPIView.as_view(), name='manufacturer_dashboard_stats'),
    path('warranty-claims/', ManufacturerWarrantyClaimListView.as_view(), name='manufacturer_warranty_claims_list'),
    path('job-cards/', ManufacturerJobCardListView.as_view(), name='manufacturer_job_cards_list'),
    path('job-cards/<str:job_card_number>/', ManufacturerJobCardDetailView.as_view(), name='manufacturer_job_card_detail'),
]

urlpatterns = [
    path('manufacturer/', include(manufacturer_patterns)),
    path('dashboards/technician/', TechnicianDashboardStatsAPIView.as_view(), name='technician_dashboard_stats'),
    path('claims/', AdminWarrantyClaimListView.as_view(), name='admin_warranty_claims_list'),
    path('claims/create/', AdminWarrantyClaimCreateView.as_view(), name='admin_warranty_claim_create'),
]