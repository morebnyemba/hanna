from rest_framework import serializers
from .models import WarrantyClaim

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