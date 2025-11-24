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
    AddToCartSerializer,
    # Item tracking serializers
    ItemLocationHistorySerializer,
    SerializedItemDetailSerializer,
    ItemTransferSerializer,
    ItemLocationStatsSerializer,
    ItemsNeedingAttentionSerializer,
)
from .services import ItemTrackingService
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        """
        Allow public read access (list, retrieve) for products.
        Require authentication for write operations (create, update, delete).
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    
    def get_permissions(self):
        """
        Allow public read access (list, retrieve) for categories.
        Require authentication for write operations (create, update, delete).
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

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


# ============================================================================
# Item Location Tracking ViewSets
# ============================================================================

class ItemTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for item location tracking operations.
    Provides endpoints for viewing and managing item locations.
    """
    queryset = SerializedItem.objects.select_related(
        'product', 'current_holder'
    ).prefetch_related('location_history')
    serializer_class = SerializedItemDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'], url_path='location-history')
    def location_history(self, request, pk=None):
        """
        Get complete location history for an item.
        
        GET /crm-api/items/{id}/location-history/
        """
        item = self.get_object()
        history = ItemTrackingService.get_item_location_timeline(item)
        serializer = ItemLocationHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='transfer')
    def transfer(self, request, pk=None):
        """
        Transfer item to new location.
        
        POST /crm-api/items/{id}/transfer/
        Body: {
            "to_location": "technician",
            "to_holder_id": 5,
            "reason": "repair",
            "notes": "Sent for screen replacement",
            "update_status": "in_repair"
        }
        """
        item = self.get_object()
        serializer = ItemTransferSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get validated data
        data = serializer.validated_data
        to_holder = None
        if data.get('to_holder_id'):
            to_holder = User.objects.get(id=data['to_holder_id'])
        
        # Get related objects if provided
        related_order = None
        related_warranty_claim = None
        related_job_card = None
        
        if data.get('related_order_id'):
            from customer_data.models import Order
            related_order = Order.objects.get(id=data['related_order_id'])
        
        if data.get('related_warranty_claim_id'):
            from warranty.models import WarrantyClaim
            related_warranty_claim = WarrantyClaim.objects.get(id=data['related_warranty_claim_id'])
        
        if data.get('related_job_card_id'):
            from customer_data.models import JobCard
            related_job_card = JobCard.objects.get(job_card_number=data['related_job_card_id'])
        
        # Perform transfer
        history = ItemTrackingService.transfer_item(
            item=item,
            to_location=data['to_location'],
            to_holder=to_holder,
            reason=data['reason'],
            notes=data.get('notes', ''),
            related_order=related_order,
            related_warranty_claim=related_warranty_claim,
            related_job_card=related_job_card,
            transferred_by=request.user,
            update_status=data.get('update_status')
        )
        
        return Response(
            ItemLocationHistorySerializer(history).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], url_path='by-location/(?P<location>[^/.]+)')
    def by_location(self, request, location=None):
        """
        Get all items at a specific location.
        
        GET /crm-api/items/by-location/warehouse/
        GET /crm-api/items/by-location/technician/?holder_id=5
        """
        holder_id = request.query_params.get('holder_id')
        holder = User.objects.get(id=holder_id) if holder_id else None
        
        items = ItemTrackingService.get_items_by_location(location, holder)
        
        # Paginate results
        page = self.paginate_queryset(items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='needing-attention')
    def needing_attention(self, request):
        """
        Get items that need attention (awaiting collection, parts, etc.)
        
        GET /crm-api/items/needing-attention/
        """
        items = ItemTrackingService.get_items_needing_attention()
        serializer = ItemsNeedingAttentionSerializer(items)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        Get statistics about item locations and statuses.
        
        GET /crm-api/items/statistics/
        """
        stats = ItemTrackingService.get_item_statistics()
        serializer = ItemLocationStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='mark-sold')
    def mark_sold(self, request, pk=None):
        """
        Mark item as sold and transfer to customer.
        
        POST /crm-api/items/{id}/mark-sold/
        Body: {
            "order_id": "uuid",
            "customer_holder_id": 123,
            "notes": "Delivered to customer"
        }
        """
        item = self.get_object()
        
        from customer_data.models import Order
        order_id = request.data.get('order_id')
        if not order_id:
            return Response(
                {'error': 'order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order = get_object_or_404(Order, id=order_id)
        customer_holder_id = request.data.get('customer_holder_id')
        customer_holder = User.objects.get(id=customer_holder_id) if customer_holder_id else None
        
        history = ItemTrackingService.mark_item_sold(
            item=item,
            order=order,
            customer_holder=customer_holder,
            transferred_by=request.user,
            notes=request.data.get('notes', '')
        )
        
        return Response(
            ItemLocationHistorySerializer(history).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='assign-technician')
    def assign_technician(self, request, pk=None):
        """
        Assign item to a technician for service/repair.
        
        POST /crm-api/items/{id}/assign-technician/
        Body: {
            "technician_id": 5,
            "job_card_number": "JC-001",
            "notes": "Screen replacement needed"
        }
        """
        item = self.get_object()
        
        technician_id = request.data.get('technician_id')
        if not technician_id:
            return Response(
                {'error': 'technician_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        technician = get_object_or_404(User, id=technician_id)
        
        job_card = None
        if request.data.get('job_card_number'):
            from customer_data.models import JobCard
            job_card = JobCard.objects.get(job_card_number=request.data['job_card_number'])
        
        history = ItemTrackingService.assign_to_technician(
            item=item,
            technician=technician,
            job_card=job_card,
            notes=request.data.get('notes', ''),
            transferred_by=request.user
        )
        
        return Response(
            ItemLocationHistorySerializer(history).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='mark-outsourced')
    def mark_outsourced(self, request, pk=None):
        """
        Mark item as outsourced to third-party service provider.
        
        POST /crm-api/items/{id}/mark-outsourced/
        Body: {
            "holder_id": 10,
            "job_card_number": "JC-001",
            "notes": "Sent to XYZ Repairs"
        }
        """
        item = self.get_object()
        
        holder_id = request.data.get('holder_id')
        if not holder_id:
            return Response(
                {'error': 'holder_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        holder = get_object_or_404(User, id=holder_id)
        
        job_card = None
        if request.data.get('job_card_number'):
            from customer_data.models import JobCard
            job_card = JobCard.objects.get(job_card_number=request.data['job_card_number'])
        
        history = ItemTrackingService.mark_item_outsourced(
            item=item,
            holder=holder,
            job_card=job_card,
            notes=request.data.get('notes', ''),
            transferred_by=request.user
        )
        
        return Response(
            ItemLocationHistorySerializer(history).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='return-to-warehouse')
    def return_to_warehouse(self, request, pk=None):
        """
        Return item to warehouse.
        
        POST /crm-api/items/{id}/return-to-warehouse/
        Body: {
            "job_card_number": "JC-001",
            "notes": "Repair completed",
            "mark_as_stock": true
        }
        """
        item = self.get_object()
        
        job_card = None
        if request.data.get('job_card_number'):
            from customer_data.models import JobCard
            job_card = JobCard.objects.get(job_card_number=request.data['job_card_number'])
        
        history = ItemTrackingService.return_to_warehouse(
            item=item,
            job_card=job_card,
            notes=request.data.get('notes', ''),
            transferred_by=request.user,
            mark_as_stock=request.data.get('mark_as_stock', True)
        )
        
        return Response(
            ItemLocationHistorySerializer(history).data,
            status=status.HTTP_200_OK
        )