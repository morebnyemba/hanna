"""
URL configuration for Solar Integration API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    SolarAlertViewSet,
    SolarAPICredentialViewSet,
    SolarDashboardView,
    SolarInverterBrandViewSet,
    SolarInverterViewSet,
    SolarStationViewSet,
)

app_name = 'solar_integration'

router = DefaultRouter()
router.register(r'brands', SolarInverterBrandViewSet, basename='solar-brand')
router.register(r'credentials', SolarAPICredentialViewSet, basename='solar-credential')
router.register(r'stations', SolarStationViewSet, basename='solar-station')
router.register(r'inverters', SolarInverterViewSet, basename='solar-inverter')
router.register(r'alerts', SolarAlertViewSet, basename='solar-alert')

urlpatterns = [
    path('dashboard/', SolarDashboardView.as_view(), name='solar-dashboard'),
    path('', include(router.urls)),
]
