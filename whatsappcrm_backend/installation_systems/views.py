from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
import logging

from warranty.models import Technician
from products_and_services.models import SerializedItem
from .models import (
    InstallationSystemRecord, 
    InstallationPhoto,
    PayoutConfiguration,
    InstallerPayout
)
from .serializers import (
    InstallationSystemRecordListSerializer,
    InstallationSystemRecordDetailSerializer,
    InstallationSystemRecordCreateUpdateSerializer,
    InstallationPhotoListSerializer,
    InstallationPhotoDetailSerializer,
    InstallationPhotoCreateSerializer,
    InstallationPhotoUpdateSerializer,
    PayoutConfigurationSerializer,
    InstallerPayoutListSerializer,
    InstallerPayoutDetailSerializer,
    InstallerPayoutCreateSerializer,
    InstallerPayoutUpdateSerializer,
    InstallerPayoutApprovalSerializer,
    InstallerPayoutPaymentSerializer,
)

logger = logging.getLogger(__name__)


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


class InstallationPhotoPermission(permissions.BasePermission):
    """
    Custom permission for InstallationPhoto:
    - Admin users: Full CRUD access
    - Technician users: Can upload (create) and view photos for assigned installations
    - Client users: Can view photos for their installations (read-only)
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
        
        # Technicians can upload and view
        if hasattr(request.user, 'technician_profile'):
            return request.method in list(permissions.SAFE_METHODS) + ['POST']
        
        # Clients can only view (read-only)
        if hasattr(request.user, 'customer_profile'):
            return request.method in permissions.SAFE_METHODS
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific photo"""
        # Admins and staff have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Technicians can view and update photos for their assigned installations
        if hasattr(request.user, 'technician_profile'):
            technician = request.user.technician_profile
            installation = obj.installation_record
            if installation.technicians.filter(id=technician.id).exists():
                return request.method in permissions.SAFE_METHODS or request.method in ['PUT', 'PATCH', 'DELETE']
            return False
        
        # Clients can only view photos for their own installations
        if hasattr(request.user, 'customer_profile'):
            customer = request.user.customer_profile
            return obj.installation_record.customer == customer and request.method in permissions.SAFE_METHODS
        
        return False


class InstallationPhotoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Installation Photos.
    
    Provides CRUD operations with the following access control:
    - Admin: Full access to all photos
    - Technician: Can upload and view photos for assigned installations
    - Client: Can view photos for own installations only (read-only)
    
    Filtering:
    - By installation_record: ?installation_record=<uuid>
    - By photo_type: ?photo_type=serial_number
    - By uploaded_by: ?uploaded_by=<technician_id>
    - By is_required: ?is_required=true
    
    Search:
    - By caption, description
    
    Ordering:
    - By any field using ?ordering=field_name
    - Default: -uploaded_at (newest first)
    """
    
    queryset = InstallationPhoto.objects.all()
    permission_classes = [InstallationPhotoPermission]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'installation_record',
        'photo_type',
        'uploaded_by',
        'is_required',
        'checklist_item',
    ]
    search_fields = [
        'caption',
        'description',
    ]
    ordering_fields = [
        'uploaded_at',
        'photo_type',
    ]
    ordering = ['-uploaded_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return InstallationPhotoListSerializer
        elif self.action == 'create':
            return InstallationPhotoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InstallationPhotoUpdateSerializer
        return InstallationPhotoDetailSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        
        - Admin/Staff: See all photos
        - Technician: See only photos for assigned installations
        - Client: See only photos for their own installations
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Prefetch related objects for performance
        queryset = queryset.select_related(
            'installation_record',
            'installation_record__customer',
            'media_asset',
            'uploaded_by',
            'uploaded_by__user',
        )
        
        # Admin and staff see all
        if user.is_staff or user.is_superuser:
            return queryset
        
        # Technicians see photos for their assigned installations
        if hasattr(user, 'technician_profile'):
            technician = user.technician_profile
            return queryset.filter(installation_record__technicians=technician)
        
        # Clients see photos for their own installations
        if hasattr(user, 'customer_profile'):
            customer = user.customer_profile
            return queryset.filter(installation_record__customer=customer)
        
        # No access for other users
        return queryset.none()
    
    def perform_create(self, serializer):
        """Set uploaded_by to current technician if applicable"""
        uploaded_by = None
        if hasattr(self.request.user, 'technician_profile'):
            uploaded_by = self.request.user.technician_profile
        
        serializer.save(uploaded_by=uploaded_by)
    
    @action(detail=False, methods=['get'])
    def by_installation(self, request):
        """
        Get all photos for a specific installation, grouped by photo type.
        Query parameter: installation_id
        """
        installation_id = request.query_params.get('installation_id')
        
        if not installation_id:
            return Response(
                {'error': 'installation_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            installation = InstallationSystemRecord.objects.get(id=installation_id)
        except InstallationSystemRecord.DoesNotExist:
            return Response(
                {'error': 'Installation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if not self.check_installation_access(request.user, installation):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get photos grouped by type
        photos = self.get_queryset().filter(installation_record=installation)
        
        grouped_photos = {}
        for photo_type in InstallationPhoto.PhotoType.values:
            type_photos = photos.filter(photo_type=photo_type)
            if type_photos.exists():
                serializer = self.get_serializer(type_photos, many=True)
                grouped_photos[photo_type] = serializer.data
        
        # Also include required photo types
        required_types = installation.get_required_photo_types()
        all_uploaded, missing_types = installation.are_all_required_photos_uploaded()
        
        return Response({
            'installation_id': str(installation.id),
            'installation_short_id': f"ISR-{str(installation.id)[:8]}",
            'photos_by_type': grouped_photos,
            'required_photo_types': required_types,
            'missing_photo_types': missing_types,
            'all_required_uploaded': all_uploaded,
            'total_photos': photos.count(),
        })
    
    @action(detail=False, methods=['get'])
    def required_photos_status(self, request):
        """
        Check status of required photos for an installation.
        Query parameter: installation_id
        """
        installation_id = request.query_params.get('installation_id')
        
        if not installation_id:
            return Response(
                {'error': 'installation_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            installation = InstallationSystemRecord.objects.get(id=installation_id)
        except InstallationSystemRecord.DoesNotExist:
            return Response(
                {'error': 'Installation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if not self.check_installation_access(request.user, installation):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        required_types = installation.get_required_photo_types()
        all_uploaded, missing_types = installation.are_all_required_photos_uploaded()
        
        uploaded_counts = {}
        for photo_type in required_types:
            count = installation.photos.filter(photo_type=photo_type).count()
            uploaded_counts[photo_type] = count
        
        return Response({
            'installation_id': str(installation.id),
            'required_photo_types': required_types,
            'missing_photo_types': missing_types,
            'uploaded_counts': uploaded_counts,
            'all_required_uploaded': all_uploaded,
        })
    
    def check_installation_access(self, user, installation):
        """Helper method to check if user has access to installation"""
        if user.is_staff or user.is_superuser:
            return True
        
        if hasattr(user, 'technician_profile'):
            return installation.technicians.filter(id=user.technician_profile.id).exists()
        
        if hasattr(user, 'customer_profile'):
            return installation.customer == user.customer_profile
        
        return False


class PayoutConfigurationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payout configurations.
    Admin-only access.
    """
    queryset = PayoutConfiguration.objects.all()
    serializer_class = PayoutConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['installation_type', 'is_active', 'rate_type', 'capacity_unit']
    search_fields = ['name']
    ordering_fields = ['priority', 'name', 'created_at']
    ordering = ['-priority', 'installation_type', 'min_system_size']
    
    def get_permissions(self):
        """Only admins can manage payout configurations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active payout configurations"""
        active_configs = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_configs, many=True)
        return Response(serializer.data)


class InstallerPayoutViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing installer payouts.
    Supports filtering, approval workflow, and payment tracking.
    """
    queryset = InstallerPayout.objects.select_related(
        'technician__user',
        'configuration',
        'approved_by'
    ).prefetch_related('installations').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['technician', 'status', 'approved_by']
    search_fields = ['technician__user__first_name', 'technician__user__last_name', 'payment_reference', 'notes']
    ordering_fields = ['created_at', 'payout_amount', 'approved_at', 'paid_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return InstallerPayoutListSerializer
        elif self.action == 'create':
            return InstallerPayoutCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InstallerPayoutUpdateSerializer
        elif self.action == 'approve':
            return InstallerPayoutApprovalSerializer
        elif self.action == 'mark_paid':
            return InstallerPayoutPaymentSerializer
        return InstallerPayoutDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admins see all payouts
        if user.is_staff or user.is_superuser:
            return queryset
        
        # Technicians see only their own payouts
        if hasattr(user, 'technician_profile'):
            return queryset.filter(technician=user.technician_profile)
        
        # Other users see no payouts
        return queryset.none()
    
    def get_permissions(self):
        """Control access based on action"""
        if self.action in ['create', 'approve', 'mark_paid', 'sync_to_zoho']:
            return [permissions.IsAdminUser()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve or reject a payout.
        
        POST /api/installer-payouts/{id}/approve/
        Body: {
            "action": "approve" | "reject",
            "rejection_reason": "..." (required if action is reject),
            "admin_notes": "..." (optional)
        }
        """
        payout = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        admin_notes = serializer.validated_data.get('admin_notes', '')
        
        # Check if payout can be approved/rejected
        if payout.status != InstallerPayout.PayoutStatus.PENDING:
            return Response(
                {'error': f'Cannot {action} payout with status {payout.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action == 'approve':
            payout.status = InstallerPayout.PayoutStatus.APPROVED
            payout.approved_by = request.user
            payout.approved_at = timezone.now()
            if admin_notes:
                payout.admin_notes = admin_notes
            payout.save()
            
            # Trigger Zoho sync
            try:
                from .tasks import sync_payout_to_zoho
                sync_payout_to_zoho.delay(str(payout.id))
            except Exception as e:
                logger.warning(f"Failed to queue Zoho sync task: {e}")
            
            # Send notification to technician
            try:
                from .tasks import send_payout_approval_email
                send_payout_approval_email.delay(str(payout.id))
            except Exception as e:
                logger.warning(f"Failed to queue email notification: {e}")
            
            message = 'Payout approved successfully'
        else:  # reject
            payout.status = InstallerPayout.PayoutStatus.REJECTED
            payout.rejection_reason = rejection_reason
            if admin_notes:
                payout.admin_notes = admin_notes
            payout.save()
            
            # Send rejection notification to technician
            try:
                from .tasks import send_payout_rejection_email
                send_payout_rejection_email.delay(str(payout.id))
            except Exception as e:
                logger.warning(f"Failed to queue email notification: {e}")
            
            message = 'Payout rejected'
        
        return Response({
            'message': message,
            'payout': InstallerPayoutDetailSerializer(payout, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """
        Mark a payout as paid.
        
        POST /api/installer-payouts/{id}/mark_paid/
        Body: {
            "payment_reference": "...",
            "payment_date": "2024-01-15T10:30:00Z" (optional),
            "notes": "..." (optional)
        }
        """
        payout = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if payout can be marked as paid
        if payout.status != InstallerPayout.PayoutStatus.APPROVED:
            return Response(
                {'error': 'Only approved payouts can be marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_reference = serializer.validated_data['payment_reference']
        payment_date = serializer.validated_data.get('payment_date', timezone.now())
        notes = serializer.validated_data.get('notes', '')
        
        payout.status = InstallerPayout.PayoutStatus.PAID
        payout.payment_reference = payment_reference
        payout.paid_at = payment_date
        if notes:
            if payout.admin_notes:
                payout.admin_notes += f"\n\nPayment notes: {notes}"
            else:
                payout.admin_notes = f"Payment notes: {notes}"
        payout.save()
        
        # Send payment confirmation to technician
        try:
            from .tasks import send_payout_payment_email
            send_payout_payment_email.delay(str(payout.id))
        except Exception as e:
            logger.warning(f"Failed to queue email notification: {e}")
        
        return Response({
            'message': 'Payout marked as paid successfully',
            'payout': InstallerPayoutDetailSerializer(payout, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def sync_to_zoho(self, request, pk=None):
        """
        Manually trigger Zoho sync for a payout.
        
        POST /api/installer-payouts/{id}/sync_to_zoho/
        """
        payout = self.get_object()
        
        if payout.status not in [InstallerPayout.PayoutStatus.APPROVED, InstallerPayout.PayoutStatus.PAID]:
            return Response(
                {'error': 'Only approved or paid payouts can be synced to Zoho'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .tasks import sync_payout_to_zoho
            task = sync_payout_to_zoho.delay(str(payout.id))
            
            return Response({
                'message': 'Zoho sync queued successfully',
                'task_id': task.id
            })
        except Exception as e:
            logger.error(f"Failed to queue Zoho sync: {e}")
            return Response(
                {'error': f'Failed to queue Zoho sync: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending payouts"""
        pending_payouts = self.get_queryset().filter(status=InstallerPayout.PayoutStatus.PENDING)
        page = self.paginate_queryset(pending_payouts)
        if page is not None:
            serializer = InstallerPayoutListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = InstallerPayoutListSerializer(pending_payouts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get payout history (approved, rejected, paid)"""
        history_payouts = self.get_queryset().exclude(status=InstallerPayout.PayoutStatus.PENDING)
        page = self.paginate_queryset(history_payouts)
        if page is not None:
            serializer = InstallerPayoutListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = InstallerPayoutListSerializer(history_payouts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_technician(self, request):
        """
        Get payouts grouped by technician with totals.
        
        GET /api/installer-payouts/by_technician/?status=approved
        """
        from django.db.models import Sum, Count
        
        queryset = self.get_queryset()
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Group by technician
        technician_stats = queryset.values(
            'technician',
            'technician__user__first_name',
            'technician__user__last_name',
            'technician__user__email'
        ).annotate(
            total_payouts=Count('id'),
            total_amount=Sum('payout_amount')
        ).order_by('-total_amount')
        
        return Response(technician_stats)
