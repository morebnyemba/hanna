# whatsappcrm_backend/users/urls.py

from django.urls import path
from .views import UserListView, UserInviteView, UserDetailView

app_name = 'users_api'

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('invite/', UserInviteView.as_view(), name='user-invite'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
