from django.urls import path
from .views import ManufacturerDashboardStatsAPIView

app_name = 'warranty_api'

urlpatterns = [
    path('dashboards/manufacturer/', ManufacturerDashboardStatsAPIView.as_view(), name='manufacturer_dashboard_stats'),
]

