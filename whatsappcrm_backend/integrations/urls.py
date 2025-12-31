"""
URL configuration for integrations app.
"""
from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    # Zoho OAuth endpoints
    path('zoho/initiate/', views.zoho_oauth_initiate, name='zoho_oauth_initiate'),
    path('callback', views.zoho_oauth_callback, name='zoho_oauth_callback'),
]
