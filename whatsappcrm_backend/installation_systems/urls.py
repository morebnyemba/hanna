from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstallationSystemRecordViewSet

app_name = 'installation_systems'

router = DefaultRouter()
router.register(r'installation-system-records', InstallationSystemRecordViewSet, basename='installation-system-record')

urlpatterns = [
    path('', include(router.urls)),
]
