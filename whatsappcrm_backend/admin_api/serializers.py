# whatsappcrm_backend/admin_api/serializers.py
"""
Serializers for Admin API
"""

from rest_framework import serializers
from django.contrib.auth.models import User

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
from installation_systems.serializers import (
    CommissioningChecklistTemplateSerializer,
    InstallationChecklistEntrySerializer,
    InstallationChecklistEntryCreateSerializer,
    PayoutConfigurationSerializer,
    InstallerPayoutListSerializer,
    InstallerPayoutDetailSerializer,
)


# User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
        read_only_fields = ['date_joined', 'last_login']


# Notifications
class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.username', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'


# AI Integration
class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = '__all__'


# Email Integration
class SMTPConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMTPConfig
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}


class EmailAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAccount
        fields = '__all__'
        extra_kwargs = {'imap_password': {'write_only': True}}


class EmailAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAttachment
        fields = '__all__'


class ParsedInvoiceSerializer(serializers.ModelSerializer):
    attachment_filename = serializers.CharField(source='attachment.filename', read_only=True)
    
    class Meta:
        model = ParsedInvoice
        fields = '__all__'


class AdminEmailRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminEmailRecipient
        fields = '__all__'


# Users
class RetailerSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    branch_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Retailer
        fields = '__all__'
    
    def get_branch_count(self, obj):
        return obj.branches.count()


class RetailerBranchSerializer(serializers.ModelSerializer):
    retailer_name = serializers.CharField(source='retailer.company_name', read_only=True)
    
    class Meta:
        model = RetailerBranch
        fields = '__all__'


# Warranty
class ManufacturerSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Manufacturer
        fields = '__all__'


class TechnicianSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Technician
        fields = '__all__'


class WarrantySerializer(serializers.ModelSerializer):
    serialized_item_serial = serializers.CharField(source='serialized_item.serial_number', read_only=True)
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = Warranty
        fields = '__all__'


class WarrantyClaimSerializer(serializers.ModelSerializer):
    warranty_item = serializers.CharField(source='warranty.serialized_item.serial_number', read_only=True)
    
    class Meta:
        model = WarrantyClaim
        fields = '__all__'


class WarrantyRuleSerializer(serializers.ModelSerializer):
    """Serializer for WarrantyRule CRUD operations in admin"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    category_name = serializers.CharField(source='product_category.name', read_only=True)
    
    class Meta:
        model = WarrantyRule
        fields = [
            'id',
            'name',
            'product',
            'product_name',
            'product_category',
            'category_name',
            'warranty_duration_days',
            'terms_and_conditions',
            'is_active',
            'priority',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Ensure either product or category is set, not both"""
        product = data.get('product')
        category = data.get('product_category')
        
        if product and category:
            raise serializers.ValidationError(
                "A warranty rule cannot apply to both a specific product and a category. Choose one."
            )
        if not product and not category:
            raise serializers.ValidationError(
                "A warranty rule must apply to either a specific product or a product category."
            )
        
        return data


class SLAThresholdSerializer(serializers.ModelSerializer):
    """Serializer for SLAThreshold CRUD operations in admin"""
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    
    class Meta:
        model = SLAThreshold
        fields = [
            'id',
            'name',
            'request_type',
            'request_type_display',
            'response_time_hours',
            'resolution_time_hours',
            'escalation_rules',
            'notification_threshold_percent',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_notification_threshold_percent(self, value):
        """Ensure notification threshold is between 1 and 100"""
        if value < 1 or value > 100:
            raise serializers.ValidationError("Notification threshold must be between 1 and 100.")
        return value


class SLAStatusSerializer(serializers.ModelSerializer):
    """Serializer for SLAStatus read operations in admin"""
    request_type = serializers.CharField(source='sla_threshold.request_type', read_only=True)
    request_type_display = serializers.CharField(source='sla_threshold.get_request_type_display', read_only=True)
    sla_threshold_name = serializers.CharField(source='sla_threshold.name', read_only=True)
    response_status_display = serializers.CharField(source='get_response_status_display', read_only=True)
    resolution_status_display = serializers.CharField(source='get_resolution_status_display', read_only=True)
    is_breached = serializers.SerializerMethodField()
    
    class Meta:
        model = SLAStatus
        fields = [
            'id',
            'content_type',
            'object_id',
            'sla_threshold',
            'sla_threshold_name',
            'request_type',
            'request_type_display',
            'request_created_at',
            'response_time_deadline',
            'resolution_time_deadline',
            'response_completed_at',
            'resolution_completed_at',
            'response_status',
            'response_status_display',
            'resolution_status',
            'resolution_status_display',
            'is_breached',
            'last_notification_sent',
            'created_at',
            'updated_at'
        ]
        read_only_fields = '__all__'
    
    def get_is_breached(self, obj):
        """Check if either response or resolution is breached"""
        return (
            obj.response_status == SLAStatus.StatusType.BREACHED or 
            obj.resolution_status == SLAStatus.StatusType.BREACHED
        )


# Stats
class DailyStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStat
        fields = '__all__'


# Products
class CartSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = '__all__'
    
    def get_items_count(self, obj):
        return obj.items.count()


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = CartItem
        fields = '__all__'


# InstallationRequest
class InstallationRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    customer_full_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    installation_type_display = serializers.CharField(source='get_installation_type_display', read_only=True)
    technicians = TechnicianSerializer(many=True, read_only=True)
    technician_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        write_only=True, 
        queryset=Technician.objects.all(),
        source='technicians',
        required=False
    )
    
    class Meta:
        model = InstallationRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_customer_full_name(self, obj):
        if obj.customer:
            return f"{obj.customer.first_name or ''} {obj.customer.last_name or ''}".strip() or obj.customer.contact.name
        return None


# SiteAssessmentRequest
class SiteAssessmentRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    customer_full_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assessment_type_display = serializers.CharField(source='get_assessment_type_display', read_only=True)
    
    class Meta:
        model = SiteAssessmentRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'assessment_id']
    
    def get_customer_full_name(self, obj):
        if obj.customer:
            return f"{obj.customer.first_name or ''} {obj.customer.last_name or ''}".strip() or obj.customer.contact.name
        return None


# LoanApplication
class LoanApplicationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    customer_full_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    loan_type_display = serializers.CharField(source='get_loan_type_display', read_only=True)
    
    class Meta:
        model = LoanApplication
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'application_id']
    
    def get_customer_full_name(self, obj):
        if obj.customer:
            return f"{obj.customer.first_name or ''} {obj.customer.last_name or ''}".strip() or obj.customer.contact.name
        return None


# InstallationSystemRecord
class InstallationSystemRecordSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    customer_full_name = serializers.SerializerMethodField()
    order_number = serializers.CharField(source='order.order_number', read_only=True, allow_null=True)
    installation_type_display = serializers.CharField(source='get_installation_type_display', read_only=True)
    system_classification_display = serializers.CharField(source='get_system_classification_display', read_only=True)
    installation_status_display = serializers.CharField(source='get_installation_status_display', read_only=True)
    capacity_unit_display = serializers.CharField(source='get_capacity_unit_display', read_only=True)
    short_id = serializers.SerializerMethodField()
    
    class Meta:
        model = InstallationSystemRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_customer_full_name(self, obj):
        if obj.customer:
            return obj.customer.get_full_name() or obj.customer.contact.name or obj.customer.contact.whatsapp_id
        return None
    
    def get_short_id(self, obj):
        return f"ISR-{str(obj.id)[:8]}"
