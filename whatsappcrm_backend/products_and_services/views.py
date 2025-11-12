from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, ProductCategory, SerializedItem
from .serializers import (
    ProductSerializer, 
    ProductCategorySerializer, 
    SerializedItemSerializer,
    BarcodeScanSerializer,
    BarcodeResponseSerializer
)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class SerializedItemViewSet(viewsets.ModelViewSet):
    queryset = SerializedItem.objects.all()
    serializer_class = SerializedItemSerializer
    permission_classes = [permissions.IsAuthenticated]

class BarcodeScanViewSet(viewsets.ViewSet):
    """
    ViewSet for barcode scanning operations.
    Provides endpoints to scan and lookup products/items by barcode.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='scan')
    def scan_barcode(self, request):
        """
        Scan a barcode and return product or serialized item information.
        
        POST /crm-api/products/barcode/scan/
        Body: {
            "barcode": "123456789",
            "scan_type": "product" or "serialized_item"
        }
        """
        serializer = BarcodeScanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        barcode_value = serializer.validated_data['barcode']
        scan_type = serializer.validated_data.get('scan_type', 'product')

        # Try to find the item by barcode
        if scan_type == 'product':
            try:
                product = Product.objects.get(barcode=barcode_value)
                product_data = ProductSerializer(product).data
                response_data = {
                    'found': True,
                    'item_type': 'product',
                    'data': product_data,
                    'message': f'Product found: {product.name}'
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except Product.DoesNotExist:
                # Also try by SKU as fallback
                try:
                    product = Product.objects.get(sku=barcode_value)
                    product_data = ProductSerializer(product).data
                    response_data = {
                        'found': True,
                        'item_type': 'product',
                        'data': product_data,
                        'message': f'Product found by SKU: {product.name}'
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                except Product.DoesNotExist:
                    pass

        elif scan_type == 'serialized_item':
            try:
                item = SerializedItem.objects.select_related('product').get(barcode=barcode_value)
                item_data = SerializedItemSerializer(item).data
                response_data = {
                    'found': True,
                    'item_type': 'serialized_item',
                    'data': item_data,
                    'message': f'Serialized item found: {item.product.name} (SN: {item.serial_number})'
                }
                return Response(response_data, status=status.HTTP_200_OK)
            except SerializedItem.DoesNotExist:
                # Also try by serial number as fallback
                try:
                    item = SerializedItem.objects.select_related('product').get(serial_number=barcode_value)
                    item_data = SerializedItemSerializer(item).data
                    response_data = {
                        'found': True,
                        'item_type': 'serialized_item',
                        'data': item_data,
                        'message': f'Serialized item found by serial number: {item.product.name}'
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                except SerializedItem.DoesNotExist:
                    pass

        # If nothing found, return not found response
        response_data = {
            'found': False,
            'item_type': None,
            'data': None,
            'message': f'No {scan_type} found with barcode: {barcode_value}'
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='lookup')
    def lookup_barcode(self, request):
        """
        More flexible lookup that searches across both products and serialized items.
        
        POST /crm-api/products/barcode/lookup/
        Body: {
            "barcode": "123456789"
        }
        """
        barcode_value = request.data.get('barcode')
        if not barcode_value:
            return Response(
                {'error': 'Barcode is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []

        # Search products by barcode
        products = Product.objects.filter(barcode=barcode_value)
        for product in products:
            results.append({
                'type': 'product',
                'data': ProductSerializer(product).data
            })

        # Search products by SKU
        products_by_sku = Product.objects.filter(sku=barcode_value)
        for product in products_by_sku:
            # Avoid duplicates
            if not any(r['data']['id'] == product.id and r['type'] == 'product' for r in results):
                results.append({
                    'type': 'product_by_sku',
                    'data': ProductSerializer(product).data
                })

        # Search serialized items by barcode
        items = SerializedItem.objects.select_related('product').filter(barcode=barcode_value)
        for item in items:
            results.append({
                'type': 'serialized_item',
                'data': SerializedItemSerializer(item).data
            })

        # Search serialized items by serial number
        items_by_sn = SerializedItem.objects.select_related('product').filter(serial_number=barcode_value)
        for item in items_by_sn:
            # Avoid duplicates
            if not any(r['data']['id'] == item.id and r['type'] == 'serialized_item' for r in results):
                results.append({
                    'type': 'serialized_item_by_serial',
                    'data': SerializedItemSerializer(item).data
                })

        if results:
            return Response({
                'found': True,
                'count': len(results),
                'results': results,
                'message': f'Found {len(results)} item(s) matching barcode: {barcode_value}'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'found': False,
                'count': 0,
                'results': [],
                'message': f'No items found matching barcode: {barcode_value}'
            }, status=status.HTTP_404_NOT_FOUND)