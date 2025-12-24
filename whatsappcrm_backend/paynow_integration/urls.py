# whatsappcrm_backend/paynow_integration/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaynowConfigViewSet, initiate_whatsapp_payment, submit_omari_otp, paynow_ipn_handler

router = DefaultRouter()
router.register(r'config', PaynowConfigViewSet, basename='paynow-config')

app_name = 'paynow_integration_api'

urlpatterns = [
    path('', include(router.urls)),
    path('initiate-payment/', initiate_whatsapp_payment, name='initiate-whatsapp-payment'),
    path('submit-otp/', submit_omari_otp, name='submit-omari-otp'),
    path('ipn/', paynow_ipn_handler, name='paynow-ipn'),
]