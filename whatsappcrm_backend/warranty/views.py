from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from .models import Warranty, WarrantyClaim
from customer_data.models import JobCard, CustomerProfile
from customer_data.serializers import JobCardSerializer, JobCardDetailSerializer
from products_and_services.models import Product
from products_and_services.serializers import ProductSerializer
from .permissions import IsManufacturer, IsTechnician
from .serializers import WarrantyClaimListSerializer, WarrantyClaimCreateSerializer, ManufacturerSerializer, WarrantySerializer
from .pdf_utils import WarrantyCertificateGenerator, InstallationReportGenerator
from installation_systems.models import InstallationSystemRecord

class AdminWarrantyClaimListView(generics.ListAPIView):
    """
    Provides a paginated list of all warranty claims for admin users.
    """
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return WarrantyClaim.objects.all().select_related('warranty__serialized_item__product', 'warranty__customer').order_by('-created_at')

class AdminWarrantyClaimCreateView(generics.CreateAPIView):
    serializer_class = WarrantyClaimCreateSerializer
    permission_classes = [IsAdminUser]

class ManufacturerDashboardStatsAPIView(APIView):
    permission_classes = [IsManufacturer]

    def get(self, request, *args, **kwargs):
        manufacturer = request.user.manufacturer_profile

        total_orders = 0  # Replace with actual logic
        pending_orders = 0  # Replace with actual logic
        completed_orders = 0  # Replace with actual logic
        warranty_claims = WarrantyClaim.objects.filter(warranty__serialized_item__product__manufacturer=manufacturer).count()

        stats = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'warranty_claims': warranty_claims,
        }

        return Response(stats)

class ManufacturerJobCardListView(generics.ListAPIView):
    serializer_class = JobCardSerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return JobCard.objects.filter(serialized_item__product__manufacturer=self.request.user.manufacturer_profile)

class ManufacturerJobCardDetailView(generics.RetrieveAPIView):
    serializer_class = JobCardDetailSerializer
    permission_classes = [IsManufacturer]
    lookup_field = 'job_card_number'

    def get_queryset(self):
        return JobCard.objects.filter(serialized_item__product__manufacturer=self.request.user.manufacturer_profile)

class ManufacturerWarrantyClaimListView(generics.ListAPIView):
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return WarrantyClaim.objects.filter(warranty__serialized_item__product__manufacturer=self.request.user.manufacturer_profile)

class TechnicianDashboardStatsAPIView(APIView):
    permission_classes = [IsTechnician]

    def get(self, request, *args, **kwargs):
        technician = request.user.technician_profile

        assigned_job_cards = JobCard.objects.filter(technician=technician)
        completed_job_cards = assigned_job_cards.filter(status='completed').count()
        pending_job_cards = assigned_job_cards.filter(status__in=['open', 'in_progress']).count()

        stats = {
            'assigned_job_cards': assigned_job_cards.count(),
            'completed_job_cards': completed_job_cards,
            'pending_job_cards': pending_job_cards,
        }

        return Response(stats)

class ManufacturerProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return Product.objects.filter(manufacturer=self.request.user.manufacturer_profile)

class ManufacturerProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return Product.objects.filter(manufacturer=self.request.user.manufacturer_profile)

    def perform_create(self, serializer):
        serializer.save(manufacturer=self.request.user.manufacturer_profile)

class ManufacturerWarrantyClaimDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [IsManufacturer]
    lookup_field = 'claim_id'

    def get_queryset(self):
        return WarrantyClaim.objects.filter(warranty__serialized_item__product__manufacturer=self.request.user.manufacturer_profile)

class ManufacturerWarrantyViewSet(viewsets.ModelViewSet):
    serializer_class = WarrantySerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return Warranty.objects.filter(manufacturer=self.request.user.manufacturer_profile)

    def perform_create(self, serializer):
        serializer.save(manufacturer=self.request.user.manufacturer_profile)

class ManufacturerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ManufacturerSerializer
    permission_classes = [IsManufacturer]

    def get_object(self):
        return self.request.user.manufacturer_profile


class ManufacturerProductTrackingView(APIView):
    """
    Get all products with their serialized items for tracking by manufacturer.
    Shows item locations, statuses, and lifecycle information.
    """
    permission_classes = [IsManufacturer]

    def get(self, request, *args, **kwargs):
        manufacturer = request.user.manufacturer_profile
        products = Product.objects.filter(
            manufacturer=manufacturer
        ).prefetch_related(
            'serialized_items'
        ).order_by('name')
        
        data = []
        for product in products:
            items = product.serialized_items.all()
            serialized_items = []
            items_in_stock = 0
            items_sold = 0
            items_in_repair = 0
            
            for item in items:
                serialized_items.append({
                    'id': item.id,
                    'serial_number': item.serial_number,
                    'barcode': item.barcode,
                    'status': item.status,
                    'status_display': item.get_status_display(),
                    'current_location': item.current_location,
                    'current_location_display': item.get_current_location_display(),
                    'location_notes': item.location_notes,
                    'created_at': item.created_at.isoformat(),
                    'updated_at': item.updated_at.isoformat(),
                })
                
                # Count items by status
                if item.status == 'in_stock':
                    items_in_stock += 1
                elif item.status == 'sold':
                    items_sold += 1
                elif item.status in ['in_repair', 'awaiting_parts', 'outsourced']:
                    items_in_repair += 1
            
            data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'product_type': product.product_type,
                'serialized_items': serialized_items,
                'total_items': len(items),
                'items_in_stock': items_in_stock,
                'items_sold': items_sold,
                'items_in_repair': items_in_repair,
            })
        
        return Response(data)

class TechnicianJobCardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobCardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobCard.objects.filter(technician=self.request.user.technician_profile)


class TechnicianInstallationHistoryView(generics.ListAPIView):
    """
    Get installation history for the logged-in technician/installer.
    Includes all installations assigned to this technician with their order details.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from customer_data.models import InstallationRequest
        from django.db.models import Q
        from django.utils.dateparse import parse_date
        
        technician = self.request.user.technician_profile
        queryset = InstallationRequest.objects.filter(
            technicians=technician
        ).select_related(
            'customer', 'associated_order'
        ).prefetch_related(
            'associated_order__items', 
            'associated_order__items__product',
            'associated_order__items__assigned_items'
        ).order_by('-created_at')
        
        # Date filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(created_at__date__lte=parse_date(end_date))
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = []
        for installation in queryset:
            data.append({
                'id': installation.id,
                'full_name': installation.full_name,
                'address': installation.address,
                'contact_phone': installation.contact_phone,
                'installation_type': installation.installation_type,
                'installation_type_display': installation.get_installation_type_display(),
                'status': installation.status,
                'status_display': installation.get_status_display(),
                'order_number': installation.order_number,
                'created_at': installation.created_at.isoformat(),
                'updated_at': installation.updated_at.isoformat(),
                'notes': installation.notes,
            })
        return Response(data)


class TechnicianInstallationDetailView(generics.RetrieveAPIView):
    """
    Get detailed installation info including assigned products with serial numbers.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        from customer_data.models import InstallationRequest
        
        technician = self.request.user.technician_profile
        installation_id = self.kwargs.get('pk')
        
        return InstallationRequest.objects.filter(
            id=installation_id,
            technicians=technician
        ).select_related(
            'customer', 'associated_order'
        ).prefetch_related(
            'associated_order__items', 
            'associated_order__items__product',
            'associated_order__items__assigned_items'
        ).first()

    def retrieve(self, request, *args, **kwargs):
        installation = self.get_object()
        if not installation:
            return Response({'error': 'Installation not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Build detailed response with order items and serial numbers
        order_data = None
        if installation.associated_order:
            items_data = []
            for item in installation.associated_order.items.all():
                serial_numbers = [si.serial_number for si in item.assigned_items.all()]
                items_data.append({
                    'id': str(item.id),
                    'product_name': item.product.name,
                    'product_sku': item.product.sku,
                    'quantity': item.quantity,
                    'serial_numbers': serial_numbers,
                })
            order_data = {
                'id': str(installation.associated_order.id),
                'order_number': installation.associated_order.order_number,
                'items': items_data,
            }
        
        data = {
            'id': installation.id,
            'full_name': installation.full_name,
            'address': installation.address,
            'contact_phone': installation.contact_phone,
            'installation_type': installation.installation_type,
            'installation_type_display': installation.get_installation_type_display(),
            'status': installation.status,
            'status_display': installation.get_status_display(),
            'order_number': installation.order_number,
            'created_at': installation.created_at.isoformat(),
            'updated_at': installation.updated_at.isoformat(),
            'notes': installation.notes,
            'associated_order': order_data,
        }
        return Response(data)


class WarrantyCertificatePDFView(APIView):
    """
    Generate and download warranty certificate PDF.
    Accessible by authenticated users (customers, admins, manufacturers).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, warranty_id):
        """Generate warranty certificate PDF"""
        # Get warranty object with optimized query
        warranty = get_object_or_404(
            Warranty.objects.select_related(
                'manufacturer',
                'serialized_item',
                'serialized_item__product',
                'customer',
                'customer__contact'
            ),
            id=warranty_id
        )
        
        # Check permissions
        user = request.user
        has_permission = False
        
        # Admin users can access all warranties
        if user.is_staff or user.is_superuser:
            has_permission = True
        # Manufacturers can access their warranties
        elif hasattr(user, 'manufacturer_profile'):
            if warranty.manufacturer == user.manufacturer_profile:
                has_permission = True
        # Customers can access their own warranties
        elif hasattr(user, 'customer_profile'):
            if warranty.customer == user.customer_profile:
                has_permission = True
        
        if not has_permission:
            return Response(
                {'error': 'You do not have permission to access this warranty certificate.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check cache for existing PDF
        cache_key = f'warranty_certificate_{warranty_id}'
        cached_pdf = cache.get(cache_key)
        
        if cached_pdf:
            # Return cached PDF
            response = HttpResponse(cached_pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="warranty_certificate_{warranty_id}.pdf"'
            return response
        
        # Generate new PDF
        try:
            generator = WarrantyCertificateGenerator()
            pdf_buffer = generator.generate(warranty)
            pdf_data = pdf_buffer.getvalue()
            
            # Cache the PDF for 1 hour
            cache.set(cache_key, pdf_data, 60 * 60)
            
            # Return PDF response
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="warranty_certificate_{warranty_id}.pdf"'
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate warranty certificate: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InstallationReportPDFView(APIView):
    """
    Generate and download installation report PDF.
    Accessible by authenticated users (customers, admins, technicians).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, installation_id):
        """Generate installation report PDF"""
        # Get installation record with optimized query
        installation = get_object_or_404(
            InstallationSystemRecord.objects.select_related(
                'customer',
                'customer__contact',
                'order',
                'installation_request'
            ).prefetch_related(
                'technicians',
                'technicians__user',
                'installed_components',
                'installed_components__product',
                'checklist_entries',
                'checklist_entries__template',
                'photos',
                'photos__media_asset'
            ),
            id=installation_id
        )
        
        # Check permissions
        user = request.user
        has_permission = False
        
        # Admin users can access all installation reports
        if user.is_staff or user.is_superuser:
            has_permission = True
        # Technicians can access installations they worked on
        elif hasattr(user, 'technician_profile'):
            if installation.technicians.filter(id=user.technician_profile.id).exists():
                has_permission = True
        # Customers can access their own installation reports
        elif hasattr(user, 'customer_profile'):
            if installation.customer == user.customer_profile:
                has_permission = True
        
        if not has_permission:
            return Response(
                {'error': 'You do not have permission to access this installation report.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check cache for existing PDF
        cache_key = f'installation_report_{installation_id}'
        cached_pdf = cache.get(cache_key)
        
        if cached_pdf:
            # Return cached PDF
            response = HttpResponse(cached_pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="installation_report_{installation_id}.pdf"'
            return response
        
        # Generate new PDF
        try:
            generator = InstallationReportGenerator()
            pdf_buffer = generator.generate(installation)
            pdf_data = pdf_buffer.getvalue()
            
            # Cache the PDF for 1 hour
            cache.set(cache_key, pdf_data, 60 * 60)
            
            # Return PDF response
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="installation_report_{installation_id}.pdf"'
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate installation report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TechnicianChecklistViewSet(viewsets.ModelViewSet):
    """
    API endpoint for technicians to view and update their assigned checklists.
    Shows checklists for installations where the technician is assigned.
    """
    permission_classes = [permissions.IsAuthenticated, IsTechnician]
    
    def get_serializer_class(self):
        """Use TechnicianChecklistSerializer from installation_systems for the correct format"""
        from installation_systems.serializers import TechnicianChecklistSerializer
        return TechnicianChecklistSerializer
    
    def get_queryset(self):
        """
        Get checklists for installations assigned to this technician.
        Includes checklists where:
        - The technician is directly assigned to the checklist, OR
        - The technician is assigned to the installation
        """
        from installation_systems.models import InstallationChecklistEntry, InstallationSystemRecord
        from django.db.models import Q
        
        if not hasattr(self.request.user, 'technician_profile'):
            return InstallationChecklistEntry.objects.none()
        
        technician = self.request.user.technician_profile
        
        # Get installation IDs where this technician is assigned
        assigned_installations = InstallationSystemRecord.objects.filter(
            installation_request__technicians=technician
        ).values_list('id', flat=True)
        
        return InstallationChecklistEntry.objects.filter(
            Q(technician=technician) | Q(installation_record_id__in=assigned_installations)
        ).select_related(
            'installation_record', 
            'template', 
            'technician', 
            'technician__user'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Automatically assign the technician on create"""
        if hasattr(self.request.user, 'technician_profile'):
            serializer.save(technician=self.request.user.technician_profile)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def update_item(self, request, pk=None):
        """
        Custom action to update a single checklist item.
        Expects: item_id, completed (bool), notes (optional), photos (optional)
        """
        entry = self.get_object()
        item_id = request.data.get('item_id')
        completed = request.data.get('completed', False)
        notes = request.data.get('notes', '')
        photos = request.data.get('photos', [])

        if not item_id:
            return Response(
                {'error': 'item_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update completed_items
        if item_id not in entry.completed_items:
            entry.completed_items[item_id] = {}

        entry.completed_items[item_id].update({
            'completed': completed,
            'completed_at': timezone.now().isoformat() if completed else None,
            'notes': notes,
            'photos': photos,
            'completed_by': str(request.user.id) if request.user.is_authenticated else None,
        })

        # Recalculate completion status
        entry.update_completion_status()
        entry.save()

        serializer = self.get_serializer(entry)
        return Response({
            'message': f'Checklist item {item_id} updated successfully.',
            'data': serializer.data
        })
