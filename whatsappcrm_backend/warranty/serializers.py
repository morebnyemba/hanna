from rest_framework import serializers
from .models import Warranty, WarrantyClaim, Manufacturer
from products_and_services.models import SerializedItem

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'

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