from rest_framework import serializers
from .models import Product, ProductCategory, SerializedItem, Cart, CartItem, ItemLocationHistory
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

class SerializedItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = SerializedItem
        fields = '__all__'

class BarcodeScanSerializer(serializers.Serializer):
    """
    Serializer for barcode scan requests.
    """
    barcode = serializers.CharField(max_length=255, required=True, help_text="The scanned barcode value")
    scan_type = serializers.ChoiceField(
        choices=['product', 'serialized_item'],
        default='product',
        help_text="Type of item to scan for: product or serialized_item"
    )

class BarcodeResponseSerializer(serializers.Serializer):
    """
    Serializer for barcode scan responses.
    """
    found = serializers.BooleanField()
    item_type = serializers.CharField(allow_null=True)
    data = serializers.DictField(allow_null=True)
    message = serializers.CharField()


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for cart items including product details and subtotal.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for shopping cart including all items and totals.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'session_key', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'session_key', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """
    Serializer for adding items to cart.
    """
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(default=1, min_value=1)


# ============================================================================
# Item Location Tracking Serializers
# ============================================================================

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for location history."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ItemLocationHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for item location history with full details.
    """
    from_holder_details = UserBasicSerializer(source='from_holder', read_only=True)
    to_holder_details = UserBasicSerializer(source='to_holder', read_only=True)
    transferred_by_details = UserBasicSerializer(source='transferred_by', read_only=True)
    
    from_location_display = serializers.CharField(source='get_from_location_display', read_only=True)
    to_location_display = serializers.CharField(source='get_to_location_display', read_only=True)
    transfer_reason_display = serializers.CharField(source='get_transfer_reason_display', read_only=True)
    
    # Related object details
    related_order_number = serializers.CharField(source='related_order.order_number', read_only=True, allow_null=True)
    related_warranty_claim_id = serializers.CharField(source='related_warranty_claim.claim_id', read_only=True, allow_null=True)
    related_job_card_number = serializers.CharField(source='related_job_card.job_card_number', read_only=True, allow_null=True)
    
    class Meta:
        model = ItemLocationHistory
        fields = [
            'id',
            'serialized_item',
            'from_location',
            'from_location_display',
            'to_location',
            'to_location_display',
            'from_holder',
            'from_holder_details',
            'to_holder',
            'to_holder_details',
            'transfer_reason',
            'transfer_reason_display',
            'notes',
            'related_order',
            'related_order_number',
            'related_warranty_claim',
            'related_warranty_claim_id',
            'related_job_card',
            'related_job_card_number',
            'transferred_by',
            'transferred_by_details',
            'timestamp',
        ]
        read_only_fields = ['id', 'timestamp']


class SerializedItemDetailSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for SerializedItem with location tracking.
    """
    product_details = ProductSerializer(source='product', read_only=True)
    current_holder_details = UserBasicSerializer(source='current_holder', read_only=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_location_display = serializers.CharField(source='get_current_location_display', read_only=True)
    
    # Recent location history
    recent_history = serializers.SerializerMethodField()
    
    class Meta:
        model = SerializedItem
        fields = [
            'id',
            'product',
            'product_details',
            'serial_number',
            'barcode',
            'status',
            'status_display',
            'current_location',
            'current_location_display',
            'current_holder',
            'current_holder_details',
            'location_notes',
            'created_at',
            'updated_at',
            'recent_history',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_recent_history(self, obj):
        """Get last 5 location changes."""
        history = obj.location_history.all()[:5]
        return ItemLocationHistorySerializer(history, many=True).data


class ItemTransferSerializer(serializers.Serializer):
    """
    Serializer for transferring items to new locations.
    """
    to_location = serializers.ChoiceField(
        choices=SerializedItem.Location.choices,
        required=True,
        help_text="Destination location"
    )
    to_holder_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="User ID of the new holder"
    )
    reason = serializers.ChoiceField(
        choices=ItemLocationHistory.TransferReason.choices,
        required=True,
        help_text="Reason for the transfer"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional notes about the transfer"
    )
    update_status = serializers.ChoiceField(
        choices=SerializedItem.Status.choices,
        required=False,
        allow_null=True,
        help_text="Optionally update item status"
    )
    related_order_id = serializers.UUIDField(required=False, allow_null=True)
    related_warranty_claim_id = serializers.UUIDField(required=False, allow_null=True)
    related_job_card_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_to_holder_id(self, value):
        """Validate that the holder user exists."""
        if value is not None:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this ID does not exist")
        return value


class ItemLocationStatsSerializer(serializers.Serializer):
    """
    Serializer for item location statistics.
    """
    by_location = serializers.DictField(child=serializers.IntegerField())
    by_status = serializers.DictField(child=serializers.IntegerField())
    total_items = serializers.IntegerField()


class ItemsNeedingAttentionSerializer(serializers.Serializer):
    """
    Serializer for items that need attention.
    """
    awaiting_collection = SerializedItemDetailSerializer(many=True, read_only=True)
    awaiting_parts = SerializedItemDetailSerializer(many=True, read_only=True)
    outsourced = SerializedItemDetailSerializer(many=True, read_only=True)
    in_transit = SerializedItemDetailSerializer(many=True, read_only=True)
