# whatsappcrm_backend/admin_api/views.py
"""
Centralized Admin API ViewSets for frontend admin dashboard.
All Django admin functionality accessible via REST API.
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponse
from django.core.cache import cache

# Import models
from notifications.models import Notification, NotificationTemplate
from ai_integration.models import AIProvider
from email_integration.models import SMTPConfig, EmailAccount, EmailAttachment, ParsedInvoice, AdminEmailRecipient
from users.models import Retailer, RetailerBranch
from warranty.models import Manufacturer, Technician, Warranty, WarrantyClaim, WarrantyRule, SLAThreshold, SLAStatus
from stats.models import DailyStat
from products_and_services.models import Cart, CartItem
from customer_data.models import InstallationRequest, SiteAssessmentRequest, LoanApplication
from installation_systems.models import (
    InstallationSystemRecord, 
    CommissioningChecklistTemplate, 
    InstallationChecklistEntry,
    PayoutConfiguration,
    InstallerPayout
)

# Import PDF generators
from warranty.pdf_utils import WarrantyCertificateGenerator, InstallationReportGenerator

# Import serializers
from .serializers import (
    NotificationSerializer, NotificationTemplateSerializer,
    AIProviderSerializer, SMTPConfigSerializer, EmailAccountSerializer,
    EmailAttachmentSerializer, ParsedInvoiceSerializer, AdminEmailRecipientSerializer,
    RetailerSerializer, RetailerBranchSerializer,
    ManufacturerSerializer, TechnicianSerializer, WarrantySerializer, WarrantyClaimSerializer,
    WarrantyRuleSerializer, SLAThresholdSerializer, SLAStatusSerializer,
    DailyStatSerializer, CartSerializer, CartItemSerializer,
    UserSerializer, InstallationRequestSerializer, SiteAssessmentRequestSerializer, LoanApplicationSerializer,
    InstallationSystemRecordSerializer,
    CommissioningChecklistTemplateSerializer,
    InstallationChecklistEntrySerializer,
    InstallationChecklistEntryCreateSerializer,
    PayoutConfigurationSerializer,
    InstallerPayoutListSerializer,
    InstallerPayoutDetailSerializer,
)


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


# User Management
class UserViewSet(viewsets.ModelViewSet):
    """Admin API for User management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined', 'last_login']
    ordering = ['-date_joined']


# Notifications
class NotificationViewSet(viewsets.ModelViewSet):
    """Admin API for Notifications"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'channel', 'recipient']
    search_fields = ['recipient__username', 'recipient__email']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """Admin API for Notification Templates"""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'updated_at']
    ordering = ['name']


# AI Integration
class AIProviderViewSet(viewsets.ModelViewSet):
    """Admin API for AI Providers"""
    queryset = AIProvider.objects.all()
    serializer_class = AIProviderSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['provider', 'is_active']
    ordering_fields = ['provider', 'updated_at']
    ordering = ['provider']


# Email Integration
class SMTPConfigViewSet(viewsets.ModelViewSet):
    """Admin API for SMTP Configurations"""
    queryset = SMTPConfig.objects.all()
    serializer_class = SMTPConfigSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'host', 'username']
    ordering_fields = ['name', 'updated_at']
    ordering = ['name']


class EmailAccountViewSet(viewsets.ModelViewSet):
    """Admin API for Email Accounts"""
    queryset = EmailAccount.objects.all()
    serializer_class = EmailAccountSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'imap_host', 'imap_user']
    ordering_fields = ['name', 'updated_at']
    ordering = ['name']


class EmailAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin API for Email Attachments (read-only)"""
    queryset = EmailAttachment.objects.all()
    serializer_class = EmailAttachmentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['processed']
    search_fields = ['filename', 'sender']
    ordering_fields = ['saved_at', 'email_date']
    ordering = ['-saved_at']


class ParsedInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin API for Parsed Invoices (read-only)"""
    queryset = ParsedInvoice.objects.all()
    serializer_class = ParsedInvoiceSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'attachment__filename']
    ordering_fields = ['invoice_date', 'total_amount']
    ordering = ['-invoice_date']


class AdminEmailRecipientViewSet(viewsets.ModelViewSet):
    """Admin API for Admin Email Recipients"""
    queryset = AdminEmailRecipient.objects.all()
    serializer_class = AdminEmailRecipientSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'email']
    ordering_fields = ['name']
    ordering = ['name']


# Users (Retailers, Branches)
class AdminRetailerViewSet(viewsets.ModelViewSet):
    """Admin API for Retailers"""
    queryset = Retailer.objects.all()
    serializer_class = RetailerSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['company_name', 'contact_phone', 'contact_email']
    ordering_fields = ['company_name', 'created_at']
    ordering = ['company_name']


class AdminRetailerBranchViewSet(viewsets.ModelViewSet):
    """Admin API for Retailer Branches"""
    queryset = RetailerBranch.objects.all()
    serializer_class = RetailerBranchSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'retailer']
    search_fields = ['branch_name', 'branch_code', 'contact_phone']
    ordering_fields = ['branch_name', 'created_at']
    ordering = ['branch_name']


# Warranty Management
class AdminManufacturerViewSet(viewsets.ModelViewSet):
    """Admin API for Manufacturers"""
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_email', 'contact_phone']
    ordering_fields = ['name']
    ordering = ['name']


class AdminTechnicianViewSet(viewsets.ModelViewSet):
    """Admin API for Technicians"""
    queryset = Technician.objects.all()
    serializer_class = TechnicianSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__email', 'specialization', 'contact_phone']
    ordering_fields = ['user__username', 'specialization']
    ordering = ['user__username']


class AdminWarrantyViewSet(viewsets.ModelViewSet):
    """Admin API for Warranties"""
    queryset = Warranty.objects.select_related(
        'serialized_item__product__category',
        'manufacturer',
        'customer__contact'
    ).prefetch_related(
        'serialized_item__product__warranty_rules'
    ).all()
    serializer_class = WarrantySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'manufacturer']
    search_fields = ['serialized_item__serial_number', 'customer__name']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']
    
    @action(detail=True, methods=['get'], url_path='certificate')
    def generate_certificate(self, request, pk=None):
        """
        Generate and download warranty certificate PDF for admin users.
        Endpoint: /crm-api/admin-panel/warranties/{id}/certificate/
        """
        warranty = self.get_object()
        
        # Check cache for existing PDF
        cache_key = f'warranty_certificate_{warranty.id}'
        cached_pdf = cache.get(cache_key)
        
        if cached_pdf:
            response = HttpResponse(cached_pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="warranty_certificate_{warranty.id}.pdf"'
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
            response['Content-Disposition'] = f'attachment; filename="warranty_certificate_{warranty.id}.pdf"'
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate warranty certificate: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminWarrantyClaimViewSet(viewsets.ModelViewSet):
    """Admin API for Warranty Claims"""
    queryset = WarrantyClaim.objects.all()
    serializer_class = WarrantyClaimSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['claim_id', 'warranty__serialized_item__serial_number']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']


class AdminWarrantyRuleViewSet(viewsets.ModelViewSet):
    """Admin API for Warranty Rules"""
    queryset = WarrantyRule.objects.select_related('product', 'product_category').all()
    serializer_class = WarrantyRuleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'product', 'product_category']
    search_fields = ['name', 'product__name', 'product_category__name']
    ordering_fields = ['priority', 'created_at', 'warranty_duration_days']
    ordering = ['-priority', '-created_at']


class AdminSLAThresholdViewSet(viewsets.ModelViewSet):
    """Admin API for SLA Thresholds"""
    queryset = SLAThreshold.objects.all()
    serializer_class = SLAThresholdSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'request_type']
    search_fields = ['name']
    ordering_fields = ['request_type', 'response_time_hours', 'resolution_time_hours']
    ordering = ['request_type', 'name']


class AdminSLAStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin API for SLA Status (read-only)"""
    queryset = SLAStatus.objects.select_related('sla_threshold', 'content_type').all()
    serializer_class = SLAStatusSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['response_status', 'resolution_status', 'sla_threshold__request_type']
    ordering_fields = ['request_created_at', 'response_time_deadline', 'resolution_time_deadline']
    ordering = ['-request_created_at']
    
    @action(detail=False, methods=['get'])
    def compliance_metrics(self, request):
        """Get SLA compliance metrics for dashboard widget"""
        from warranty.services import SLAService
        
        metrics = SLAService.get_sla_compliance_metrics()
        return Response(metrics)


# Stats
class AdminDailyStatViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin API for Daily Stats (read-only)"""
    queryset = DailyStat.objects.all()
    serializer_class = DailyStatSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date']
    ordering = ['-date']


# Products (Cart management)
class AdminCartViewSet(viewsets.ModelViewSet):
    """Admin API for Carts"""
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['contact']
    search_fields = ['contact__name', 'contact__whatsapp_id']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


class AdminCartItemViewSet(viewsets.ModelViewSet):
    """Admin API for Cart Items"""
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['cart']
    ordering_fields = ['added_at']
    ordering = ['-added_at']


# Installation Requests
class AdminInstallationRequestViewSet(viewsets.ModelViewSet):
    """Admin API for Installation Requests"""
    queryset = InstallationRequest.objects.select_related('customer', 'associated_order').prefetch_related('technicians').all()
    serializer_class = InstallationRequestSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'installation_type', 'customer']
    search_fields = ['order_number', 'full_name', 'address', 'contact_phone']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """
        Custom action to mark an installation request as completed.
        """
        installation = self.get_object()
        installation.status = 'completed'
        installation.save()
        serializer = self.get_serializer(installation)
        return Response({
            'message': 'Installation marked as completed successfully.',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def assign_technicians(self, request, pk=None):
        """
        Custom action to assign technicians to an installation request.
        Expects a list of technician IDs in the request body: {"technician_ids": [1, 2, 3]}
        """
        installation = self.get_object()
        technician_ids = request.data.get('technician_ids', [])
        
        if not technician_ids:
            return Response(
                {'error': 'No technician IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        technicians = Technician.objects.filter(id__in=technician_ids)
        installation.technicians.set(technicians)
        
        serializer = self.get_serializer(installation)
        return Response({
            'message': f'Successfully assigned {technicians.count()} technician(s).',
            'data': serializer.data
        })


# Site Assessment Requests
class AdminSiteAssessmentRequestViewSet(viewsets.ModelViewSet):
    """Admin API for Site Assessment Requests"""
    queryset = SiteAssessmentRequest.objects.select_related('customer').all()
    serializer_class = SiteAssessmentRequestSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'assessment_type', 'customer']
    search_fields = ['assessment_id', 'full_name', 'address', 'contact_info']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """
        Custom action to mark a site assessment as assessed.
        """
        assessment = self.get_object()
        assessment.status = 'assessed'
        assessment.save()
        serializer = self.get_serializer(assessment)
        return Response({
            'message': 'Site assessment marked as assessed successfully.',
            'data': serializer.data
        })


# Loan Applications
class AdminLoanApplicationViewSet(viewsets.ModelViewSet):
    """Admin API for Loan Applications"""
    queryset = LoanApplication.objects.select_related('customer').all()
    serializer_class = LoanApplicationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'loan_type', 'customer']
    search_fields = ['application_id', 'full_name', 'national_id', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Custom action to approve a loan application.
        """
        loan = self.get_object()
        loan.status = 'approved'
        loan.save()
        serializer = self.get_serializer(loan)
        return Response({
            'message': 'Loan application approved successfully.',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Custom action to reject a loan application.
        """
        loan = self.get_object()
        loan.status = 'rejected'
        loan.save()
        serializer = self.get_serializer(loan)
        return Response({
            'message': 'Loan application rejected.',
            'data': serializer.data
        })


# Installation System Records
class AdminInstallationSystemRecordViewSet(viewsets.ModelViewSet):
    """Admin API for Installation System Records (SSR)"""
    queryset = InstallationSystemRecord.objects.select_related(
        'customer', 'customer__contact', 'order', 'installation_request'
    ).prefetch_related(
        'technicians', 'installed_components', 'warranties', 'job_cards'
    ).all()
    serializer_class = InstallationSystemRecordSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'installation_type', 'installation_status', 'system_classification',
        'capacity_unit', 'customer', 'order'
    ]
    search_fields = [
        'customer__first_name', 'customer__last_name',
        'customer__contact__whatsapp_id', 'installation_address',
        'remote_monitoring_id'
    ]
    ordering_fields = [
        'created_at', 'updated_at', 'installation_date',
        'commissioning_date', 'installation_status', 'system_size'
    ]
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Custom action to update installation status.
        """
        installation = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(InstallationSystemRecord.InstallationStatus.choices):
            return Response(
                {'error': 'Invalid status value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        installation.installation_status = new_status
        installation.save(update_fields=['installation_status', 'updated_at'])
        
        serializer = self.get_serializer(installation)
        return Response({
            'message': f'Installation status updated to {new_status}.',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def assign_technician(self, request, pk=None):
        """
        Custom action to assign a technician to the installation.
        """
        installation = self.get_object()
        technician_id = request.data.get('technician_id')
        
        if not technician_id:
            return Response(
                {'error': 'technician_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            technician = Technician.objects.get(id=technician_id)
            installation.technicians.add(technician)
            
            serializer = self.get_serializer(installation)
            return Response({
                'message': f'Technician {technician.user.get_full_name()} assigned successfully.',
                'data': serializer.data
            })
        except Technician.DoesNotExist:
            return Response(
                {'error': 'Technician not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get installation statistics.
        """
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
    
    @action(detail=True, methods=['get'], url_path='report')
    def generate_report(self, request, pk=None):
        """
        Generate and download installation report PDF for admin users.
        Endpoint: /crm-api/admin-panel/installation-system-records/{id}/report/
        """
        installation = self.get_object()
        
        # Check cache for existing PDF
        cache_key = f'installation_report_{installation.id}'
        cached_pdf = cache.get(cache_key)
        
        if cached_pdf:
            response = HttpResponse(cached_pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="installation_report_{installation.id}.pdf"'
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
            response['Content-Disposition'] = f'attachment; filename="installation_report_{installation.id}.pdf"'
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate installation report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Commissioning Checklist Templates
class CommissioningChecklistTemplateViewSet(viewsets.ModelViewSet):
    """Admin API for Commissioning Checklist Templates"""
    queryset = CommissioningChecklistTemplate.objects.all()
    serializer_class = CommissioningChecklistTemplateSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['checklist_type', 'installation_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'checklist_type', 'updated_at']
    ordering = ['checklist_type', 'name']

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Custom action to duplicate a checklist template.
        """
        template = self.get_object()
        new_template = CommissioningChecklistTemplate.objects.create(
            name=f"{template.name} (Copy)",
            checklist_type=template.checklist_type,
            installation_type=template.installation_type,
            description=template.description,
            items=template.items,
            is_active=False  # New templates start inactive
        )
        serializer = self.get_serializer(new_template)
        return Response({
            'message': 'Template duplicated successfully.',
            'data': serializer.data
        })


# Installation Checklist Entries
class InstallationChecklistEntryViewSet(viewsets.ModelViewSet):
    """Admin API for Installation Checklist Entries"""
    queryset = InstallationChecklistEntry.objects.select_related(
        'installation_record', 'template', 'technician', 'technician__user'
    ).all()
    serializer_class = InstallationChecklistEntrySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'completion_status', 'template__checklist_type',
        'installation_record', 'technician'
    ]
    search_fields = [
        'installation_record__customer__first_name',
        'installation_record__customer__last_name',
        'template__name',
    ]
    ordering_fields = [
        'created_at', 'updated_at', 'completion_percentage',
        'started_at', 'completed_at'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return InstallationChecklistEntryCreateSerializer
        return InstallationChecklistEntrySerializer

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

    @action(detail=True, methods=['get'])
    def checklist_status(self, request, pk=None):
        """
        Get detailed status of checklist completion.
        """
        entry = self.get_object()
        template_items = entry.template.items

        items_status = []
        for item in template_items:
            item_id = item.get('id')
            completed_data = entry.completed_items.get(item_id, {})
            items_status.append({
                'item_id': item_id,
                'title': item.get('title'),
                'required': item.get('required', False),
                'completed': completed_data.get('completed', False),
                'notes': completed_data.get('notes', ''),
                'photos': completed_data.get('photos', []),
                'completed_at': completed_data.get('completed_at'),
            })

        return Response({
            'entry_id': str(entry.id),
            'completion_status': entry.completion_status,
            'completion_percentage': float(entry.completion_percentage),
            'items': items_status,
        })

    @action(detail=False, methods=['get'])
    def by_installation(self, request):
        """
        Get all checklists for a specific installation.
        Query param: installation_id
        """
        installation_id = request.query_params.get('installation_id')
        if not installation_id:
            return Response(
                {'error': 'installation_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        entries = self.get_queryset().filter(installation_record_id=installation_id)
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)


# Payout Configuration Management
class AdminPayoutConfigurationViewSet(viewsets.ModelViewSet):
    """Admin API for Payout Configuration management"""
    queryset = PayoutConfiguration.objects.all()
    serializer_class = PayoutConfigurationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['installation_type', 'is_active', 'rate_type', 'capacity_unit']
    search_fields = ['name']
    ordering_fields = ['priority', 'name', 'created_at']
    ordering = ['-priority', 'installation_type', 'min_system_size']


# Installer Payout Management
class AdminInstallerPayoutViewSet(viewsets.ModelViewSet):
    """Admin API for Installer Payout management"""
    queryset = InstallerPayout.objects.select_related(
        'technician__user',
        'configuration',
        'approved_by'
    ).prefetch_related('installations').all()
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['technician', 'status', 'approved_by']
    search_fields = ['technician__user__first_name', 'technician__user__last_name', 'payment_reference', 'notes']
    ordering_fields = ['created_at', 'payout_amount', 'approved_at', 'paid_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return InstallerPayoutListSerializer
        return InstallerPayoutDetailSerializer
