from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import InstallationSystemRecord
from .serializers import (
    InstallationSystemRecordListSerializer,
    InstallationSystemRecordDetailSerializer,
    InstallationSystemRecordCreateUpdateSerializer,
)


class InstallationSystemRecordPermission(permissions.BasePermission):
    """
    Custom permission for InstallationSystemRecord:
    - Admin users: Full CRUD access
    - Technician users: Can view and update assigned installations
    - Client users: Can view their own installations (read-only)
    - Unauthenticated: No access
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view"""
        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins and staff have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Technicians can view and update
        if hasattr(request.user, 'technician_profile'):
            return request.method in permissions.SAFE_METHODS or request.method in ['PUT', 'PATCH']
        
        # Clients can only view (read-only)
        if hasattr(request.user, 'customer_profile'):
            return request.method in permissions.SAFE_METHODS
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object"""
        # Admins and staff have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Technicians can view and update their assigned installations
        if hasattr(request.user, 'technician_profile'):
            technician = request.user.technician_profile
            if obj.technicians.filter(id=technician.id).exists():
                return request.method in permissions.SAFE_METHODS or request.method in ['PUT', 'PATCH']
            return False
        
        # Clients can only view their own installations
        if hasattr(request.user, 'customer_profile'):
            return obj.customer == request.user.customer_profile and request.method in permissions.SAFE_METHODS
        
        return False


class InstallationSystemRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Installation System Records (ISR).
    
    Provides CRUD operations with the following access control:
    - Admin: Full access to all records
    - Technician: Can view and update assigned installations
    - Client: Can view own installations only (read-only)
    
    Filtering:
    - By installation_type: ?installation_type=solar
    - By installation_status: ?installation_status=active
    - By system_classification: ?system_classification=residential
    - By customer: ?customer=<customer_id>
    - By technician: ?technicians=<technician_id>
    
    Search:
    - By customer name, address, remote monitoring ID
    
    Ordering:
    - By any field using ?ordering=field_name
    - Default: -created_at (newest first)
    """
    
    queryset = InstallationSystemRecord.objects.all()
    permission_classes = [InstallationSystemRecordPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'installation_type',
        'installation_status',
        'system_classification',
        'capacity_unit',
        'customer',
        'order',
    ]
    search_fields = [
        'customer__first_name',
        'customer__last_name',
        'customer__contact__whatsapp_id',
        'installation_address',
        'remote_monitoring_id',
    ]
    ordering_fields = [
        'created_at',
        'updated_at',
        'installation_date',
        'commissioning_date',
        'installation_status',
        'system_size',
    ]
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return InstallationSystemRecordListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return InstallationSystemRecordCreateUpdateSerializer
        return InstallationSystemRecordDetailSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        
        - Admin/Staff: See all records
        - Technician: See only assigned installations
        - Client: See only their own installations
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Prefetch related objects for performance
        queryset = queryset.select_related(
            'customer',
            'customer__contact',
            'order',
            'installation_request',
        ).prefetch_related(
            'technicians',
            'installed_components',
            'warranties',
            'job_cards',
        )
        
        # Admin and staff see all
        if user.is_staff or user.is_superuser:
            return queryset
        
        # Technicians see only their assigned installations
        if hasattr(user, 'technician_profile'):
            technician = user.technician_profile
            return queryset.filter(technicians=technician)
        
        # Clients see only their own installations
        if hasattr(user, 'customer_profile'):
            customer = user.customer_profile
            return queryset.filter(customer=customer)
        
        # No access for other users
        return queryset.none()
    
    @action(detail=False, methods=['get'])
    def my_installations(self, request):
        """
        Get installations for the current user (client view).
        Returns only active and commissioned installations.
        """
        if not hasattr(request.user, 'customer_profile'):
            return Response({'error': 'Not a customer user'}, status=400)
        
        customer = request.user.customer_profile
        installations = self.get_queryset().filter(
            customer=customer,
            installation_status__in=['active', 'commissioned']
        )
        
        serializer = self.get_serializer(installations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def assigned_installations(self, request):
        """
        Get installations assigned to the current technician.
        Returns installations that are in progress or need attention.
        """
        if not hasattr(request.user, 'technician_profile'):
            return Response({'error': 'Not a technician user'}, status=400)
        
        technician = request.user.technician_profile
        installations = self.get_queryset().filter(
            technicians=technician,
            installation_status__in=['pending', 'in_progress']
        )
        
        serializer = self.get_serializer(installations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update the installation status.
        Allowed for technicians and admins.
        """
        installation = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(InstallationSystemRecord.InstallationStatus.choices):
            return Response({'error': 'Invalid status'}, status=400)
        
        installation.installation_status = new_status
        installation.save(update_fields=['installation_status', 'updated_at'])
        
        serializer = self.get_serializer(installation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_technician(self, request, pk=None):
        """
        Assign a technician to the installation.
        Admin only.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Admin access required'}, status=403)
        
        installation = self.get_object()
        technician_id = request.data.get('technician_id')
        
        if not technician_id:
            return Response({'error': 'technician_id required'}, status=400)
        
        from warranty.models import Technician
        try:
            technician = Technician.objects.get(id=technician_id)
            installation.technicians.add(technician)
            
            serializer = self.get_serializer(installation)
            return Response(serializer.data)
        except Technician.DoesNotExist:
            return Response({'error': 'Technician not found'}, status=404)
    
    @action(detail=True, methods=['post'])
    def add_component(self, request, pk=None):
        """
        Add an installed component (SerializedItem) to the installation.
        Technician or admin.
        """
        installation = self.get_object()
        component_id = request.data.get('component_id')
        
        if not component_id:
            return Response({'error': 'component_id required'}, status=400)
        
        from products_and_services.models import SerializedItem
        try:
            component = SerializedItem.objects.get(id=component_id)
            installation.installed_components.add(component)
            
            serializer = self.get_serializer(installation)
            return Response(serializer.data)
        except SerializedItem.DoesNotExist:
            return Response({'error': 'Component not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get installation statistics.
        Admin only.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Admin access required'}, status=403)
        
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'by_type': {},
            'by_status': {},
            'by_classification': {},
        }
        
        # Count by installation type
        for choice in InstallationSystemRecord.InstallationType.choices:
            count = queryset.filter(installation_type=choice[0]).count()
            stats['by_type'][choice[0]] = {
                'count': count,
                'label': choice[1],
            }
        
        # Count by installation status
        for choice in InstallationSystemRecord.InstallationStatus.choices:
            count = queryset.filter(installation_status=choice[0]).count()
            stats['by_status'][choice[0]] = {
                'count': count,
                'label': choice[1],
            }
        
        # Count by system classification
        for choice in InstallationSystemRecord.SystemClassification.choices:
            count = queryset.filter(system_classification=choice[0]).count()
            stats['by_classification'][choice[0]] = {
                'count': count,
                'label': choice[1],
            }
        
        return Response(stats)
