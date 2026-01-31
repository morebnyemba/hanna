from rest_framework import serializers
from products_and_services.models import SerializedItem, Product
from products_and_services.serializers import ProductSerializer


class ManufacturerSerializedItemSerializer(serializers.Serializer):
    """
    Serializer for manufacturers to create serialized items.
    Accepts either an existing product_id or product details to auto-create.
    """
    serial_number = serializers.CharField(max_length=255, required=True)
    product_id = serializers.IntegerField(required=False, allow_null=True)
    
    # For creating a new product if product_id not provided
    product_name = serializers.CharField(max_length=255, required=False)
    product_type = serializers.ChoiceField(
        choices=['software', 'service', 'hardware', 'module'],
        required=False
    )
    sku = serializers.CharField(max_length=100, required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Ensure either product_id or product_name is provided"""
        if not data.get('product_id') and not data.get('product_name'):
            raise serializers.ValidationError(
                "Either provide product_id or product_name to create a new product."
            )
        return data
    
    def create(self, validated_data):
        """Create or retrieve product, then create serialized item"""
        serial_number = validated_data['serial_number']
        manufacturer = validated_data['manufacturer']
        product_id = validated_data.get('product_id')
        
        # Check if serial number already exists
        if SerializedItem.objects.filter(serial_number=serial_number).exists():
            raise serializers.ValidationError(f"Serial number '{serial_number}' already exists.")
        
        # Get or create product
        if product_id:
            try:
                product = Product.objects.get(id=product_id, manufacturer=manufacturer)
            except Product.DoesNotExist:
                raise serializers.ValidationError("Product not found or does not belong to this manufacturer.")
        else:
            # Create new product
            product_name = validated_data.get('product_name')
            product_type = validated_data.get('product_type', 'hardware')
            sku = validated_data.get('sku', '')
            price = validated_data.get('price')
            description = validated_data.get('description', '')
            
            product, created = Product.objects.get_or_create(
                name=product_name,
                manufacturer=manufacturer,
                defaults={
                    'product_type': product_type,
                    'sku': sku or '',
                    'price': price,
                    'description': description,
                }
            )
        
        # Create serialized item
        serialized_item = SerializedItem.objects.create(
            product=product,
            serial_number=serial_number
        )
        
        return serialized_item
    
    def to_representation(self, instance):
        """Return the created serialized item with full product details"""
        return {
            'id': instance.id,
            'serial_number': instance.serial_number,
            'product': ProductSerializer(instance.product).data,
            'created_at': instance.created_at,
        }
