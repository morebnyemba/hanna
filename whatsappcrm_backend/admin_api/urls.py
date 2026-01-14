# whatsappcrm_backend/admin_api/urls.py
"""
URL Configuration for Admin API
All admin functionality exposed via REST API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'admin_api'

router = DefaultRouter()

# User Management
router.register(r'users', views.UserViewSet, basename='user')

# Notifications
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'notification-templates', views.NotificationTemplateViewSet, basename='notification-template')

# AI Integration
router.register(r'ai-providers', views.AIProviderViewSet, basename='ai-provider')

# Email Integration
router.register(r'smtp-configs', views.SMTPConfigViewSet, basename='smtp-config')
router.register(r'email-accounts', views.EmailAccountViewSet, basename='email-account')
router.register(r'email-attachments', views.EmailAttachmentViewSet, basename='email-attachment')
router.register(r'parsed-invoices', views.ParsedInvoiceViewSet, basename='parsed-invoice')
router.register(r'admin-email-recipients', views.AdminEmailRecipientViewSet, basename='admin-email-recipient')

# Users (Retailers, Branches)
router.register(r'retailers', views.AdminRetailerViewSet, basename='retailer')
router.register(r'retailer-branches', views.AdminRetailerBranchViewSet, basename='retailer-branch')

# Warranty Management
router.register(r'manufacturers', views.AdminManufacturerViewSet, basename='manufacturer')
router.register(r'technicians', views.AdminTechnicianViewSet, basename='technician')
router.register(r'warranties', views.AdminWarrantyViewSet, basename='warranty')
router.register(r'warranty-claims', views.AdminWarrantyClaimViewSet, basename='warranty-claim')

# Stats
router.register(r'daily-stats', views.AdminDailyStatViewSet, basename='daily-stat')

# Products (Cart management)
router.register(r'carts', views.AdminCartViewSet, basename='cart')
router.register(r'cart-items', views.AdminCartItemViewSet, basename='cart-item')

# Installation Requests
router.register(r'installation-requests', views.AdminInstallationRequestViewSet, basename='installation-request')

# Installation System Records (SSR)
router.register(r'installation-system-records', views.AdminInstallationSystemRecordViewSet, basename='installation-system-record')

# Site Assessment Requests
router.register(r'site-assessment-requests', views.AdminSiteAssessmentRequestViewSet, basename='site-assessment-request')

# Loan Applications
router.register(r'loan-applications', views.AdminLoanApplicationViewSet, basename='loan-application')

urlpatterns = [
    path('', include(router.urls)),
]
