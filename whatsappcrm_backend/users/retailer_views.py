# whatsappcrm_backend/users/retailer_views.py
"""
Views for retailer portal - Installation & Warranty Tracking
Provides read-only access to installation and warranty data for products sold by retailers.
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from datetime import timedelta

from installation_systems.models import InstallationSystemRecord, InstallationPhoto
from warranty.models import Warranty, WarrantyClaim
from products_and_services.models import SerializedItem
from customer_data.models import Order, OrderItem
from .models import Retailer, RetailerBranch
from .permissions import IsRetailerOrBranch
from .retailer_serializers import (
    RetailerInstallationTrackingSerializer,
    RetailerInstallationDetailSerializer,
    RetailerWarrantySerializer,
    RetailerWarrantyDetailSerializer,
    RetailerProductMovementSerializer,
)


class RetailerInstallationTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retailers to track installations of products they sold.
    Read-only access with filtering and search.
    
    Retailers can only view installations for:
    - Products sold through their orders
    - Orders associated with their retailer account
    """
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrBranch]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['installation_status', 'installation_type', 'system_classification']
    search_fields = [
        'customer__first_name', 
        'customer__last_name',
        'customer__contact__whatsapp_id',
        'installation_address',
        'order__order_number'
    ]
    ordering_fields = ['installation_date', 'commissioning_date', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return RetailerInstallationDetailSerializer
        return RetailerInstallationTrackingSerializer
    
    def get_retailer(self):
        """Get the retailer instance for the current user"""
        user = self.request.user
        if hasattr(user, 'retailer_profile'):
            return user.retailer_profile
        elif hasattr(user, 'retailer_branch_profile'):
            return user.retailer_branch_profile.retailer
        return None
    
    def get_queryset(self):
        """
        Filter installations to only those for products sold by this retailer.
        Returns installations where the associated order was created by the retailer.
        """
        retailer = self.get_retailer()
        if not retailer:
            return InstallationSystemRecord.objects.none()
        
        # Get all orders associated with this retailer
        # This includes orders where the retailer is explicitly linked
        # or orders created through the retailer's system
        retailer_orders = Order.objects.filter(
            Q(notes__icontains=f"retailer: {retailer.company_name}") |
            Q(acquisition_source__icontains=f"Retailer: {retailer.company_name}")
        )
        
        # Get installations for these orders
        queryset = InstallationSystemRecord.objects.filter(
            order__in=retailer_orders
        ).select_related(
            'customer',
            'customer__contact',
            'order',
            'installation_request'
        ).prefetch_related(
            'technicians',
            'technicians__user',
            'checklist_entries',
            'checklist_entries__template',
            'photos',
            'photos__media_asset'
        )
        
        # Apply filters from query params
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(installation_status=status_filter)
        
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(installation_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(installation_date__lte=date_to)
        
        return queryset.distinct()
    
    @action(detail=False, methods=['get'])
    def summary_stats(self, request):
        """
        Get summary statistics for installations.
        Returns counts by status, recent installations, etc.
        """
        queryset = self.get_queryset()
        
        # Count by status
        status_counts = {}
        for status_choice in InstallationSystemRecord.InstallationStatus.choices:
            status_value = status_choice[0]
            count = queryset.filter(installation_status=status_value).count()
            status_counts[status_value] = {
                'label': status_choice[1],
                'count': count
            }
        
        # Recent installations (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_count = queryset.filter(created_at__gte=thirty_days_ago).count()
        
        # Installations by type
        type_counts = {}
        for type_choice in InstallationSystemRecord.InstallationType.choices:
            type_value = type_choice[0]
            count = queryset.filter(installation_type=type_value).count()
            if count > 0:
                type_counts[type_value] = {
                    'label': type_choice[1],
                    'count': count
                }
        
        return Response({
            'total_installations': queryset.count(),
            'by_status': status_counts,
            'by_type': type_counts,
            'recent_installations': recent_count,
        })


class RetailerWarrantyTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retailers to track warranties for products they sold.
    Read-only access with filtering and search.
    
    Retailers can only view warranties for:
    - Products sold through their orders
    - Warranties associated with their sold products
    """
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrBranch]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = [
        'serialized_item__serial_number',
        'serialized_item__product__name',
        'customer__first_name',
        'customer__last_name',
        'customer__contact__whatsapp_id',
    ]
    ordering_fields = ['start_date', 'end_date', 'created_at', 'updated_at']
    ordering = ['-end_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return RetailerWarrantyDetailSerializer
        return RetailerWarrantySerializer
    
    def get_retailer(self):
        """Get the retailer instance for the current user"""
        user = self.request.user
        if hasattr(user, 'retailer_profile'):
            return user.retailer_profile
        elif hasattr(user, 'retailer_branch_profile'):
            return user.retailer_branch_profile.retailer
        return None
    
    def get_queryset(self):
        """
        Filter warranties to only those for products sold by this retailer.
        Returns warranties where the associated order was created by the retailer.
        """
        retailer = self.get_retailer()
        if not retailer:
            return Warranty.objects.none()
        
        # Get all orders associated with this retailer
        retailer_orders = Order.objects.filter(
            Q(notes__icontains=f"retailer: {retailer.company_name}") |
            Q(acquisition_source__icontains=f"Retailer: {retailer.company_name}")
        )
        
        # Get warranties for these orders
        queryset = Warranty.objects.filter(
            associated_order__in=retailer_orders
        ).select_related(
            'customer',
            'customer__contact',
            'serialized_item',
            'serialized_item__product',
            'manufacturer',
            'associated_order'
        ).prefetch_related(
            'claims'
        )
        
        # Apply filters from query params
        status_filter = self.request.query_params.get('warranty_status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by expiration
        expiring_soon = self.request.query_params.get('expiring_soon', None)
        if expiring_soon:
            # Show warranties expiring in next 30 days
            today = timezone.now().date()
            thirty_days = today + timedelta(days=30)
            queryset = queryset.filter(end_date__gte=today, end_date__lte=thirty_days)
        
        # Filter by active claims
        has_active_claims = self.request.query_params.get('has_active_claims', None)
        if has_active_claims:
            queryset = queryset.annotate(
                active_claims_count=Count('claims', filter=Q(claims__status__in=['pending', 'approved', 'in_progress']))
            ).filter(active_claims_count__gt=0)
        
        return queryset.distinct()
    
    @action(detail=False, methods=['get'])
    def summary_stats(self, request):
        """
        Get summary statistics for warranties.
        Returns counts by status, expiring soon, active claims, etc.
        """
        queryset = self.get_queryset()
        today = timezone.now().date()
        
        # Count by status
        active_count = queryset.filter(status='active').count()
        expired_count = queryset.filter(status='expired').count()
        void_count = queryset.filter(status='void').count()
        
        # Expiring soon (next 30 days)
        thirty_days = today + timedelta(days=30)
        expiring_soon = queryset.filter(
            status='active',
            end_date__gte=today,
            end_date__lte=thirty_days
        ).count()
        
        # Active claims
        warranties_with_active_claims = queryset.annotate(
            active_claims_count=Count('claims', filter=Q(claims__status__in=['pending', 'approved', 'in_progress']))
        ).filter(active_claims_count__gt=0).count()
        
        return Response({
            'total_warranties': queryset.count(),
            'active': active_count,
            'expired': expired_count,
            'void': void_count,
            'expiring_soon': expiring_soon,
            'warranties_with_active_claims': warranties_with_active_claims,
        })
    
    @action(detail=True, methods=['get'])
    def claims(self, request, pk=None):
        """
        Get all claims for a specific warranty.
        """
        warranty = self.get_object()
        claims = warranty.claims.all().order_by('-created_at')
        
        claims_data = [{
            'id': str(claim.id),
            'claim_id': claim.claim_id,
            'description_of_fault': claim.description_of_fault,
            'status': claim.status,
            'status_display': claim.get_status_display(),
            'resolution_notes': claim.resolution_notes or '',
            'created_at': claim.created_at,
            'updated_at': claim.updated_at,
        } for claim in claims]
        
        return Response({
            'warranty_id': str(warranty.id),
            'product_name': warranty.serialized_item.product.name if warranty.serialized_item else 'N/A',
            'claims': claims_data
        })


class RetailerProductMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retailers to track product movements (scanned in/out).
    Read-only access to see where products are located.
    
    Retailers can only view movements for:
    - Products they sold
    - SerializedItems associated with their orders
    """
    serializer_class = RetailerProductMovementSerializer
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrBranch]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'location']
    search_fields = [
        'serial_number',
        'barcode',
        'product__name',
        'product__sku',
    ]
    ordering_fields = ['checked_in_at', 'checked_out_at', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_retailer(self):
        """Get the retailer instance for the current user"""
        user = self.request.user
        if hasattr(user, 'retailer_profile'):
            return user.retailer_profile
        elif hasattr(user, 'retailer_branch_profile'):
            return user.retailer_branch_profile.retailer
        return None
    
    def get_queryset(self):
        """
        Filter products to only those sold by this retailer.
        Returns SerializedItems that are part of retailer's orders.
        """
        retailer = self.get_retailer()
        if not retailer:
            return SerializedItem.objects.none()
        
        # Get all orders associated with this retailer
        retailer_orders = Order.objects.filter(
            Q(notes__icontains=f"retailer: {retailer.company_name}") |
            Q(acquisition_source__icontains=f"Retailer: {retailer.company_name}")
        )
        
        # Get order items from these orders
        retailer_order_items = OrderItem.objects.filter(order__in=retailer_orders)
        
        # Get serialized items from these order items
        queryset = SerializedItem.objects.filter(
            order_item__in=retailer_order_items
        ).select_related(
            'product',
            'order_item',
            'order_item__order',
            'order_item__order__customer',
            'order_item__order__customer__contact',
            'current_holder'
        )
        
        # Apply filters from query params
        status_filter = self.request.query_params.get('item_status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        location_filter = self.request.query_params.get('item_location', None)
        if location_filter:
            queryset = queryset.filter(location=location_filter)
        
        return queryset.distinct()
    
    @action(detail=False, methods=['get'])
    def summary_stats(self, request):
        """
        Get summary statistics for product movements.
        Returns counts by status and location.
        """
        queryset = self.get_queryset()
        
        # Count by status
        status_counts = {}
        for status_choice in SerializedItem.Status.choices:
            status_value = status_choice[0]
            count = queryset.filter(status=status_value).count()
            if count > 0:
                status_counts[status_value] = {
                    'label': status_choice[1],
                    'count': count
                }
        
        # Count by location
        location_counts = {}
        for location_choice in SerializedItem.Location.choices:
            location_value = location_choice[0]
            count = queryset.filter(location=location_value).count()
            if count > 0:
                location_counts[location_value] = {
                    'label': location_choice[1],
                    'count': count
                }
        
        return Response({
            'total_items': queryset.count(),
            'by_status': status_counts,
            'by_location': location_counts,
        })
