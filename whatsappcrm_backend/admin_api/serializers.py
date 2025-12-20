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
from warranty.models import Manufacturer, Technician, Warranty, WarrantyClaim
from stats.models import DailyStat
from products_and_services.models import Cart, CartItem
from customer_data.models import InstallationRequest


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
