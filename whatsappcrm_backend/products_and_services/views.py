from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, ProductCategory, SerializedItem, Cart, CartItem
from .serializers import (
    ProductSerializer, 
    ProductCategorySerializer, 
    SerializedItemSerializer,
    BarcodeScanSerializer,
    BarcodeResponseSerializer,
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer
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


class CartViewSet(viewsets.ViewSet):
    """
    ViewSet for shopping cart operations.
    Supports both authenticated users and guest sessions.
    """
    permission_classes = [permissions.AllowAny]

    def _get_or_create_cart(self, request):
        """Get or create a cart for the current user or session."""
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            # For guest users, use session key
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart

    def list(self, request):
        """Get the current user's/session's cart."""
        cart = self._get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add')
    def add_to_cart(self, request):
        """
        Add a product to the cart or update quantity if it already exists.
        
        POST /crm-api/products/cart/add/
        Body: {
            "product_id": 1,
            "quantity": 2
        }
        """
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        # Get or create cart
        cart = self._get_or_create_cart(request)

        # Get product
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found or not available'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check stock availability
        if product.stock_quantity < quantity:
            return Response(
                {'error': f'Only {product.stock_quantity} items available in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if product.stock_quantity < new_quantity:
                return Response(
                    {'error': f'Only {product.stock_quantity} items available in stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()

        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': f'Added {quantity}x {product.name} to cart',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='update')
    def update_quantity(self, request):
        """
        Update the quantity of an item in the cart.
        
        POST /crm-api/products/cart/update/
        Body: {
            "cart_item_id": 1,
            "quantity": 3
        }
        """
        cart_item_id = request.data.get('cart_item_id')
        quantity = request.data.get('quantity')

        if not cart_item_id or quantity is None:
            return Response(
                {'error': 'cart_item_id and quantity are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity < 1:
                return Response(
                    {'error': 'Quantity must be at least 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid quantity value'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self._get_or_create_cart(request)

        try:
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check stock availability
        if cart_item.product.stock_quantity < quantity:
            return Response(
                {'error': f'Only {cart_item.product.stock_quantity} items available in stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart updated successfully',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='remove')
    def remove_from_cart(self, request):
        """
        Remove an item from the cart.
        
        POST /crm-api/products/cart/remove/
        Body: {
            "cart_item_id": 1
        }
        """
        cart_item_id = request.data.get('cart_item_id')

        if not cart_item_id:
            return Response(
                {'error': 'cart_item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self._get_or_create_cart(request)

        try:
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
            product_name = cart_item.product.name
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_serializer = CartSerializer(cart)
        return Response({
            'message': f'Removed {product_name} from cart',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='clear')
    def clear_cart(self, request):
        """
        Clear all items from the cart.
        
        POST /crm-api/products/cart/clear/
        """
        cart = self._get_or_create_cart(request)
        cart.items.all().delete()

        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart cleared successfully',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)