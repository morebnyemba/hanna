from django.urls import path
from .views import ManufacturerDashboardStatsAPIView
from .views import ManufacturerDashboardStatsAPIView, TechnicianDashboardStatsAPIView

app_name = 'warranty_api'

urlpatterns = [
    path('dashboards/manufacturer/', ManufacturerDashboardStatsAPIView.as_view(), name='manufacturer_dashboard_stats'),
    path('dashboards/technician/', TechnicianDashboardStatsAPIView.as_view(), name='technician_dashboard_stats'),
]

