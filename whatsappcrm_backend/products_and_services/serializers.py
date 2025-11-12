from rest_framework import serializers
from .models import Product, ProductCategory, SerializedItem

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
