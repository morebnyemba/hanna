# whatsappcrm_backend/users/views.py

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Retailer, RetailerBranch
from .permissions import IsAdminUser, IsRetailer, IsRetailerOrAdmin, IsRetailerBranch
from .serializers import (
    UserSerializer, 
    UserInviteSerializer,
    RetailerSerializer,
    RetailerRegistrationSerializer,
    RetailerUpdateSerializer,
    RetailerBranchSerializer,
    RetailerBranchCreateSerializer,
    RetailerBranchUpdateSerializer,
    RetailerSelectSerializer,
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


class RetailerListForSelectionView(generics.ListAPIView):
    """
    Public API view to list retailers for branch login selection.
    Returns only active retailers with minimal info (id, company_name).
    """
    serializer_class = RetailerSelectSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Retailer.objects.filter(is_active=True).order_by('company_name')


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
    Retailers can view and update their own profile and manage branches.
    """
    queryset = Retailer.objects.select_related('user').prefetch_related('branches').all()
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
            return Retailer.objects.select_related('user').prefetch_related('branches').all()
        elif hasattr(user, 'retailer_profile'):
            return Retailer.objects.filter(user=user).select_related('user').prefetch_related('branches')
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
        Get the current retailer's profile with their branches.
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

    @action(detail=False, methods=['get'], url_path='me/branches')
    def my_branches(self, request):
        """
        Get all branches for the current retailer.
        """
        if not hasattr(request.user, 'retailer_profile'):
            return Response(
                {"detail": "You are not registered as a retailer."},
                status=status.HTTP_404_NOT_FOUND
            )
        branches = request.user.retailer_profile.branches.all()
        serializer = RetailerBranchSerializer(branches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='me/branches/create')
    def create_branch(self, request):
        """
        Create a new branch for the current retailer.
        """
        if not hasattr(request.user, 'retailer_profile'):
            return Response(
                {"detail": "You are not registered as a retailer."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = RetailerBranchCreateSerializer(
            data=request.data,
            context={'retailer': request.user.retailer_profile}
        )
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        return Response(
            {
                "message": "Branch created successfully.",
                "branch": RetailerBranchSerializer(branch).data
            },
            status=status.HTTP_201_CREATED
        )


class RetailerBranchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing retailer branches.
    Retailers can manage their own branches.
    Branches can view their own profile.
    Admins can view all branches.
    """
    queryset = RetailerBranch.objects.select_related('user', 'retailer').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return RetailerBranchCreateSerializer
        if self.action in ['update', 'partial_update']:
            return RetailerBranchUpdateSerializer
        return RetailerBranchSerializer

    def get_queryset(self):
        """
        Admins see all branches.
        Retailers see only their own branches.
        Branches see only their own profile.
        """
        user = self.request.user
        if user.is_staff:
            return RetailerBranch.objects.select_related('user', 'retailer').all()
        elif hasattr(user, 'retailer_profile'):
            return RetailerBranch.objects.filter(retailer=user.retailer_profile).select_related('user', 'retailer')
        elif hasattr(user, 'retailer_branch_profile'):
            return RetailerBranch.objects.filter(user=user).select_related('user', 'retailer')
        return RetailerBranch.objects.none()

    def get_permissions(self):
        """
        Only retailers or admins can create/delete branches.
        Branches can view their own profile.
        """
        if self.action in ['create', 'destroy']:
            return [IsRetailerOrAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Set retailer context when creating a branch."""
        if hasattr(self.request.user, 'retailer_profile'):
            serializer.context['retailer'] = self.request.user.retailer_profile
            serializer.save()
        else:
            raise serializers.ValidationError("Only retailers can create branches.")

    @action(detail=False, methods=['get'], url_path='me')
    def my_profile(self, request):
        """
        Get the current branch's profile.
        """
        if not hasattr(request.user, 'retailer_branch_profile'):
            return Response(
                {"detail": "You are not registered as a retailer branch."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = RetailerBranchSerializer(request.user.retailer_branch_profile)
        return Response(serializer.data)


class RetailerSolarPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retailers to view available solar packages.
    Read-only access to active solar packages.
    """
    from products_and_services.models import SolarPackage
    from products_and_services.serializers import SolarPackageSerializer
    
    queryset = SolarPackage.objects.filter(is_active=True).prefetch_related(
        'package_products__product__images'
    )
    serializer_class = SolarPackageSerializer
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrAdmin]
    
    def get_queryset(self):
        """Only show active solar packages"""
        return super().get_queryset().filter(is_active=True)


class RetailerOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for retailers to create and manage customer orders.
    - POST: Create a new order with customer details and solar package
    - GET: List all orders created by the retailer
    - GET /<id>: View order details
    """
    from customer_data.models import Order
    from customer_data.serializers import OrderSerializer, RetailerOrderCreationSerializer
    
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrAdmin]
    
    def get_queryset(self):
        """
        Retailers see orders they created or from their retailer account.
        Admins see all orders.
        """
        user = self.request.user
        queryset = Order.objects.select_related('customer', 'assigned_agent').prefetch_related('items__product')
        
        if user.is_staff:
            return queryset.all()
        
        # Filter by retailer or retailer branch
        if hasattr(user, 'retailer_profile'):
            # Get orders where the assigned agent is the retailer or any of their branches
            retailer_users = [user]
            retailer_users.extend([branch.user for branch in user.retailer_profile.branches.all()])
            return queryset.filter(assigned_agent__in=retailer_users)
        elif hasattr(user, 'retailer_branch_profile'):
            # Get orders created by this branch
            return queryset.filter(assigned_agent=user)
        
        return Order.objects.none()
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            from customer_data.serializers import RetailerOrderCreationSerializer
            return RetailerOrderCreationSerializer
        from customer_data.serializers import OrderSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new order with complete workflow.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        # Return the created order data
        from customer_data.serializers import OrderSerializer
        order_serializer = OrderSerializer(result['order'])
        
        return Response(
            {
                'message': 'Order created successfully',
                'order': order_serializer.data,
                'order_number': result['order'].order_number,
            },
            status=status.HTTP_201_CREATED
        )