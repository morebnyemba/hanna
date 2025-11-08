# whatsappcrm_backend/analytics/urls.py

from django.urls import path
from .views import AdminAnalyticsView, ManufacturerAnalyticsView, TechnicianAnalyticsView

urlpatterns = [
    path('admin/', AdminAnalyticsView.as_view(), name='admin-analytics'),
    path('manufacturer/', ManufacturerAnalyticsView.as_view(), name='manufacturer-analytics'),
    path('technician/', TechnicianAnalyticsView.as_view(), name='technician-analytics'),
]