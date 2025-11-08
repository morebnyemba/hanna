# whatsappcrm_backend/users/views.py

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import UserSerializer, UserInviteSerializer

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class UserListView(generics.ListAPIView):
    """
    API view to list all users. Only accessible by admins.
    """
    queryset = User.objects.all().order_by('first_name')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class UserInviteView(generics.CreateAPIView):
    """
    API view for an admin to invite a new user.
    """
    serializer_class = UserInviteSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": f"Invitation sent to {user.email} successfully."},
            status=status.HTTP_201_CREATED
        )

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def perform_destroy(self, instance):
        # Instead of deleting, we just deactivate the user
        instance.is_active = False
        instance.save()