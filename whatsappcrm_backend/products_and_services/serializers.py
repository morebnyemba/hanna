from rest_framework import serializers
from .models import Product, ProductCategory, SerializedItem, Cart, CartItem, ItemLocationHistory, ProductImage, SolarPackage, SolarPackageProduct
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images with full URL for easy display.
    """
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

class SerializedItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True,
        required=False
    )

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


# ============================================================================
# Retailer Portal Serializers
# ============================================================================

class RetailerItemCheckoutSerializer(serializers.Serializer):
    """
    Serializer for retailer item checkout (sending to customer).
    """
    serial_number = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Serial number or barcode of the item to checkout"
    )
    customer_name = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Name of the customer receiving the item"
    )
    customer_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Customer phone number"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional notes about this checkout"
    )


class RetailerItemCheckinSerializer(serializers.Serializer):
    """
    Serializer for retailer item check-in (receiving from warehouse or return).
    """
    serial_number = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Serial number or barcode of the item to check-in"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional notes about this check-in"
    )


class RetailerAddSerialNumberSerializer(serializers.Serializer):
    """
    Serializer for retailer adding serial numbers to products.
    """
    product_id = serializers.IntegerField(
        required=True,
        help_text="ID of the product"
    )
    serial_number = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Serial number to add"
    )
    barcode = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Barcode for the item (optional)"
    )

    def validate_serial_number(self, value):
        """Ensure serial number is unique."""
        if SerializedItem.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError("An item with this serial number already exists.")
        return value

    def validate_barcode(self, value):
        """Ensure barcode is unique if provided."""
        if value and SerializedItem.objects.filter(barcode=value).exists():
            raise serializers.ValidationError("An item with this barcode already exists.")
        return value

    def validate_product_id(self, value):
        """Ensure product exists."""
        try:
            Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product with this ID does not exist.")
        return value


class RetailerInventoryItemSerializer(serializers.ModelSerializer):
    """
    Serializer for retailer inventory items with product details.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_location_display = serializers.CharField(source='get_current_location_display', read_only=True)

    class Meta:
        model = SerializedItem
        fields = [
            'id', 'serial_number', 'barcode', 'product', 'product_name', 'product_sku',
            'status', 'status_display', 'current_location', 'current_location_display',
            'location_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RetailerDashboardStatsSerializer(serializers.Serializer):
    """
    Serializer for retailer dashboard statistics.
    """
    total_items = serializers.IntegerField()
    items_in_stock = serializers.IntegerField()
    items_sold = serializers.IntegerField()
    items_in_transit = serializers.IntegerField()
    recent_checkouts = RetailerInventoryItemSerializer(many=True, read_only=True)
    recent_checkins = RetailerInventoryItemSerializer(many=True, read_only=True)


# ============================================================================
# Order-Based Dispatch Serializers
# ============================================================================

class OrderItemDispatchSerializer(serializers.Serializer):
    """
    Serializer for order item dispatch status.
    """
    id = serializers.IntegerField()
    product_id = serializers.IntegerField(source='product.id')
    product_name = serializers.CharField(source='product.name')
    product_sku = serializers.CharField(source='product.sku')
    quantity = serializers.IntegerField()
    units_assigned = serializers.IntegerField()
    is_fully_assigned = serializers.BooleanField()
    remaining = serializers.SerializerMethodField()
    
    def get_remaining(self, obj):
        return obj.quantity - obj.units_assigned


class OrderDispatchSerializer(serializers.Serializer):
    """
    Serializer for order dispatch response (order verification).
    """
    order_id = serializers.UUIDField()
    order_number = serializers.CharField()
    customer_name = serializers.SerializerMethodField()
    payment_status = serializers.CharField()
    stage = serializers.CharField()
    items = OrderItemDispatchSerializer(many=True, source='items.all')
    is_eligible_for_dispatch = serializers.SerializerMethodField()
    dispatch_message = serializers.SerializerMethodField()
    
    def get_customer_name(self, obj):
        """Get customer name from related customer profile."""
        if obj.customer:
            return obj.customer.get_full_name() or str(obj.customer)
        return None
    
    def get_is_eligible_for_dispatch(self, obj):
        """Check if order is eligible for dispatch."""
        # Order must be closed_won and paid/partially_paid
        return (
            obj.stage == 'closed_won' and 
            obj.payment_status in ['paid', 'partially_paid']
        )
    
    def get_dispatch_message(self, obj):
        """Get dispatch eligibility message."""
        if obj.stage != 'closed_won':
            return f"Order is not ready for dispatch. Current stage: {obj.get_stage_display()}"
        if obj.payment_status not in ['paid', 'partially_paid']:
            return f"Order payment not confirmed. Status: {obj.get_payment_status_display()}"
        # Check if all items are fully assigned
        all_assigned = all(item.is_fully_assigned for item in obj.items.all())
        if all_assigned:
            return "All items for this order have been dispatched."
        return "Order is ready for dispatch."


class OrderItemScanSerializer(serializers.Serializer):
    """
    Serializer for scanning an item for an order.
    """
    order_number = serializers.CharField(
        required=True,
        help_text="The order/invoice number"
    )
    serial_number = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Serial number or barcode of the item being dispatched"
    )
    order_item_id = serializers.IntegerField(
        required=False,
        help_text="Optional: Specific OrderItem ID to assign to (auto-matched if not provided)"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Additional notes about this dispatch"
    )


class DispatchedItemSerializer(serializers.Serializer):
    """
    Serializer for dispatched item response.
    """
    item_id = serializers.IntegerField()
    serial_number = serializers.CharField()
    barcode = serializers.CharField(allow_null=True)
    product_name = serializers.CharField()
    order_item_id = serializers.IntegerField()
    units_assigned = serializers.IntegerField()
    quantity_ordered = serializers.IntegerField()
    is_fully_assigned = serializers.BooleanField()
    dispatch_timestamp = serializers.DateTimeField()


# ============================================================================
# Meta Catalog Sync Serializers
# ============================================================================

class MetaCatalogVisibilitySerializer(serializers.Serializer):
    """
    Serializer for setting product visibility in Meta Catalog.
    """
    visibility = serializers.ChoiceField(
        choices=['published', 'hidden'],
        required=True,
        help_text="Product visibility: 'published' (active) or 'hidden' (inactive)"
    )


class MetaCatalogBatchUpdateSerializer(serializers.Serializer):
    """
    Serializer for batch updating products in Meta Catalog.
    """
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of product IDs to update"
    )
    visibility = serializers.ChoiceField(
        choices=['published', 'hidden'],
        required=False,
        help_text="Product visibility: 'published' (active) or 'hidden' (inactive)"
    )
    
    def validate_product_ids(self, value):
        """Validate that all product IDs exist."""
        if not value:
            raise serializers.ValidationError("At least one product ID is required.")
        
        existing_ids = set(Product.objects.filter(id__in=value).values_list('id', flat=True))
        missing_ids = set(value) - existing_ids
        
        if missing_ids:
            raise serializers.ValidationError(
                f"The following product IDs do not exist: {list(missing_ids)}"
            )
        return value


class MetaCatalogProductStatusSerializer(serializers.Serializer):
    """
    Serializer for Meta Catalog product status response.
    """
    id = serializers.CharField(help_text="Meta Catalog product ID")
    retailer_id = serializers.CharField(help_text="Product SKU")
    name = serializers.CharField()
    price = serializers.CharField(allow_null=True, required=False)
    currency = serializers.CharField(allow_null=True, required=False)
    availability = serializers.CharField(allow_null=True, required=False)
    visibility = serializers.CharField(allow_null=True, required=False)
    image_url = serializers.URLField(allow_null=True, required=False)
    url = serializers.URLField(allow_null=True, required=False)
    description = serializers.CharField(allow_null=True, required=False)
    brand = serializers.CharField(allow_null=True, required=False)


class MetaCatalogSyncResultSerializer(serializers.Serializer):
    """
    Serializer for sync operation results.
    """
    success = serializers.BooleanField()
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    sku = serializers.CharField(allow_null=True)
    catalog_id = serializers.CharField(allow_null=True)
    message = serializers.CharField()
    error = serializers.CharField(allow_null=True, required=False)


class SolarPackageProductSerializer(serializers.ModelSerializer):
    """
    Serializer for products included in a solar package.
    """
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = SolarPackageProduct
        fields = ['id', 'product', 'quantity']


class SolarPackageSerializer(serializers.ModelSerializer):
    """
    Serializer for solar packages with included products.
    """
    package_products = SolarPackageProductSerializer(many=True, read_only=True)
    total_products = serializers.SerializerMethodField()
    
    class Meta:
        model = SolarPackage
        fields = [
            'id', 'name', 'system_size', 'description', 
            'price', 'currency', 'is_active', 
            'package_products', 'total_products',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_products(self, obj):
        """Calculate total number of products in the package"""
        return sum(pp.quantity for pp in obj.package_products.all())
