# whatsappcrm_backend/users/views.py

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Retailer
from .permissions import IsAdminUser, IsRetailer, IsRetailerOrAdmin
from .serializers import (
    UserSerializer, 
    UserInviteSerializer,
    RetailerSerializer,
    RetailerRegistrationSerializer,
    RetailerUpdateSerializer,
)


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


class RetailerRegistrationView(generics.CreateAPIView):
    """
    API view for retailer registration.
    Creates a user account and retailer profile.
    """
    serializer_class = RetailerRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        retailer = serializer.save()
        return Response(
            {
                "message": "Retailer registration successful.",
                "retailer": RetailerSerializer(retailer).data
            },
            status=status.HTTP_201_CREATED
        )


class RetailerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing retailers.
    Admins can list/retrieve/update all retailers.
    Retailers can view and update their own profile.
    """
    queryset = Retailer.objects.select_related('user').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return RetailerUpdateSerializer
        return RetailerSerializer

    def get_queryset(self):
        """
        Admins see all retailers.
        Retailers see only their own profile.
        """
        user = self.request.user
        if user.is_staff:
            return Retailer.objects.select_related('user').all()
        elif hasattr(user, 'retailer_profile'):
            return Retailer.objects.filter(user=user).select_related('user')
        return Retailer.objects.none()

    def get_permissions(self):
        """
        Only admins can create or delete retailers.
        Retailers can view and update their own profile.
        """
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [IsRetailerOrAdmin()]

    @action(detail=False, methods=['get'], url_path='me')
    def my_profile(self, request):
        """
        Get the current retailer's profile.
        """
        if not hasattr(request.user, 'retailer_profile'):
            return Response(
                {"detail": "You are not registered as a retailer."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = RetailerSerializer(request.user.retailer_profile)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], url_path='me/update')
    def update_my_profile(self, request):
        """
        Update the current retailer's profile.
        """
        if not hasattr(request.user, 'retailer_profile'):
            return Response(
                {"detail": "You are not registered as a retailer."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = RetailerUpdateSerializer(
            request.user.retailer_profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RetailerSerializer(request.user.retailer_profile).data)