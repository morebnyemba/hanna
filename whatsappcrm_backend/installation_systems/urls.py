from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InstallationSystemRecordViewSet, 
    InstallationPhotoViewSet,
    PayoutConfigurationViewSet,
    InstallerPayoutViewSet
)

app_name = 'installation_systems'

router = DefaultRouter()
router.register(r'installation-system-records', InstallationSystemRecordViewSet, basename='installation-system-record')
router.register(r'installation-photos', InstallationPhotoViewSet, basename='installation-photo')
router.register(r'payout-configurations', PayoutConfigurationViewSet, basename='payout-configuration')
router.register(r'installer-payouts', InstallerPayoutViewSet, basename='installer-payout')

urlpatterns = [
    path('', include(router.urls)),
]
