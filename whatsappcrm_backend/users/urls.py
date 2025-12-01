# whatsappcrm_backend/users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserListView, 
    UserInviteView, 
    UserDetailView,
    RetailerRegistrationView,
    RetailerViewSet,
    RetailerBranchViewSet,
)

app_name = 'users_api'

router = DefaultRouter()
router.register(r'retailers', RetailerViewSet, basename='retailer')
router.register(r'retailer-branches', RetailerBranchViewSet, basename='retailer-branch')

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('invite/', UserInviteView.as_view(), name='user-invite'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('retailer/register/', RetailerRegistrationView.as_view(), name='retailer-register'),
    path('', include(router.urls)),
]
