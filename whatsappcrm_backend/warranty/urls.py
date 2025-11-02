from django.urls import path
from .views import ManufacturerDashboardStatsAPIView, TechnicianDashboardStatsAPIView
# Import the main dashboard view from the stats app to create a consistent URL structure
from stats.views import DashboardSummaryStatsAPIView

app_name = 'warranty_api'

urlpatterns = [
    # This new endpoint provides a consistent URL for the main admin/management dashboard.
    # The frontend should call `/crm-api/warranty/dashboards/admin/`
    path('dashboards/admin/', DashboardSummaryStatsAPIView.as_view(), name='admin_dashboard_stats_v2'),
    path('dashboards/manufacturer/', ManufacturerDashboardStatsAPIView.as_view(), name='manufacturer_dashboard_stats'),
    path('dashboards/technician/', TechnicianDashboardStatsAPIView.as_view(), name='technician_dashboard_stats'),
]
