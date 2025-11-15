from rest_framework import serializers
from .models import Product, ProductCategory, SerializedItem, Cart, CartItem

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
