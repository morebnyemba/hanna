# whatsappcrm_backend/opensolar_integration/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OpenSolarProjectViewSet, OpenSolarWebhookView

router = DefaultRouter()
router.register(r'projects', OpenSolarProjectViewSet, basename='opensolar-project')

app_name = 'opensolar_integration'

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', OpenSolarWebhookView.as_view(), name='webhook'),
]
