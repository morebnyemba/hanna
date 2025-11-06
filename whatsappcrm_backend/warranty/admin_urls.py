from django.urls import path
from .admin_views import ManufacturerCreateView

app_name = 'warranty_admin_api'

urlpatterns = [
    path('manufacturers/create/', ManufacturerCreateView.as_view(), name='manufacturer_create'),
]
