# whatsappcrm_backend/admin_api/views.py
"""
Centralized Admin API ViewSets for frontend admin dashboard.
All Django admin functionality accessible via REST API.
"""

from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User

# Import models
from notifications.models import Notification, NotificationTemplate
from ai_integration.models import AIProvider
from email_integration.models import SMTPConfig, EmailAccount, EmailAttachment, ParsedInvoice, AdminEmailRecipient
from users.models import Retailer, RetailerBranch
from warranty.models import Manufacturer, Technician, Warranty, WarrantyClaim
from stats.models import DailyStat
from products_and_services.models import Cart, CartItem
from customer_data.models import InstallationRequest, SiteAssessmentRequest, LoanApplication

# Import serializers
from .serializers import (
    NotificationSerializer, NotificationTemplateSerializer,
    AIProviderSerializer, SMTPConfigSerializer, EmailAccountSerializer,
    EmailAttachmentSerializer, ParsedInvoiceSerializer, AdminEmailRecipientSerializer,
    RetailerSerializer, RetailerBranchSerializer,
    ManufacturerSerializer, TechnicianSerializer, WarrantySerializer, WarrantyClaimSerializer,
    DailyStatSerializer, CartSerializer, CartItemSerializer,
    UserSerializer, InstallationRequestSerializer, SiteAssessmentRequestSerializer, LoanApplicationSerializer
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
    queryset = Warranty.objects.all()
    serializer_class = WarrantySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'manufacturer']
    search_fields = ['serialized_item__serial_number', 'customer__name']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']


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
        
        from warranty.models import Technician
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
