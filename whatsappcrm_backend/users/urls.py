# whatsappcrm_backend/users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserListView, 
    UserInviteView, 
    UserDetailView,
    RetailerRegistrationView,
    RetailerListForSelectionView,
    RetailerViewSet,
    RetailerBranchViewSet,
    RetailerSolarPackageViewSet,
    RetailerOrderViewSet,
)
from .retailer_views import (
    RetailerInstallationTrackingViewSet,
    RetailerWarrantyTrackingViewSet,
    RetailerProductMovementViewSet,
)

app_name = 'users_api'

router = DefaultRouter()
router.register(r'retailers', RetailerViewSet, basename='retailer')
router.register(r'retailer-branches', RetailerBranchViewSet, basename='retailer-branch')
router.register(r'retailer/solar-packages', RetailerSolarPackageViewSet, basename='retailer-solar-package')
router.register(r'retailer/orders', RetailerOrderViewSet, basename='retailer-order')
router.register(r'retailer/installations', RetailerInstallationTrackingViewSet, basename='retailer-installation')
router.register(r'retailer/warranties', RetailerWarrantyTrackingViewSet, basename='retailer-warranty')
router.register(r'retailer/product-movements', RetailerProductMovementViewSet, basename='retailer-product-movement')

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('invite/', UserInviteView.as_view(), name='user-invite'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('retailer/register/', RetailerRegistrationView.as_view(), name='retailer-register'),
    path('retailers-list/', RetailerListForSelectionView.as_view(), name='retailer-list-for-selection'),
    path('', include(router.urls)),
]
