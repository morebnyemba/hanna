from rest_framework import serializers
from .models import Warranty, WarrantyClaim, Manufacturer, WarrantyRule, SLAThreshold, SLAStatus
from products_and_services.models import SerializedItem

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'

class WarrantySerializer(serializers.ModelSerializer):
    applied_rule_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Warranty
        fields = '__all__'
    
    def get_applied_rule_name(self, obj):
        """
        Get the name of the warranty rule that was applied (if any).
        Note: For optimal performance when serializing multiple warranties,
        consider prefetching warranty rules in the viewset.
        """
        # Check if rules have been prefetched to avoid N+1 queries
        product = obj.serialized_item.product
        
        # Try to use prefetched data if available
        if hasattr(product, '_prefetched_warranty_rules'):
            # Rules already prefetched, use them
            for rule in product._prefetched_warranty_rules:
                if rule.is_active:
                    return rule.name
        
        # Fallback to service method (will cause additional query)
        from .services import WarrantyRuleService
        rule = WarrantyRuleService.find_applicable_rule(product)
        return rule.name if rule else None

class WarrantyClaimCreateSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(write_only=True)

    class Meta:
        model = WarrantyClaim
        fields = ['serial_number', 'description_of_fault']

    def create(self, validated_data):
        serial_number = validated_data.pop('serial_number')
        try:
            serialized_item = SerializedItem.objects.get(serial_number=serial_number)
            warranty = serialized_item.warranty
        except SerializedItem.DoesNotExist:
            raise serializers.ValidationError("No serialized item found with this serial number.")
        except Warranty.DoesNotExist:
            raise serializers.ValidationError("No warranty found for this serialized item.")

        claim = WarrantyClaim.objects.create(warranty=warranty, **validated_data)
        return claim

class WarrantyClaimListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing warranty claims, including related product info.
    """
    product_name = serializers.CharField(source='warranty.serialized_item.product.name', read_only=True)
    product_serial_number = serializers.CharField(source='warranty.serialized_item.serial_number', read_only=True)
    customer_name = serializers.CharField(source='warranty.customer.get_full_name', read_only=True, default='N/A')

    class Meta:
        model = WarrantyClaim
        fields = [
            'claim_id',
            'product_name',
            'product_serial_number',
            'customer_name',
            'status',
            'created_at',
        ]


class WarrantyRuleSerializer(serializers.ModelSerializer):
    """Serializer for WarrantyRule CRUD operations"""
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
    """Serializer for SLAThreshold CRUD operations"""
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
    """Serializer for SLAStatus read operations"""
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