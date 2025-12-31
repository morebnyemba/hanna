from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .models import Product, ProductCategory, SerializedItem, Cart, CartItem, ItemLocationHistory
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
    # Retailer portal serializers
    RetailerItemCheckoutSerializer,
    RetailerItemCheckinSerializer,
    RetailerAddSerialNumberSerializer,
    RetailerInventoryItemSerializer,
    RetailerDashboardStatsSerializer,
    # Order dispatch serializers
    OrderDispatchSerializer,
    OrderItemScanSerializer,
    DispatchedItemSerializer,
    # Meta catalog sync serializers
    MetaCatalogVisibilitySerializer,
    MetaCatalogBatchUpdateSerializer,
    MetaCatalogProductStatusSerializer,
    MetaCatalogSyncResultSerializer,
)
from .services import ItemTrackingService
from django.contrib.auth import get_user_model
from users.permissions import IsRetailer, IsRetailerOrAdmin, IsRetailerBranch, IsRetailerBranchOrAdmin
from meta_integration.catalog_service import MetaCatalogService

User = get_user_model()


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        """
        Get products with images. Optionally filter by:
        - category_id: Filter by product category
        - is_active: Filter by active status (default: True for public list)
        """
        queryset = Product.objects.prefetch_related('images').all()
        
        # For public list view, only show active products by default
        if self.action == 'list' and not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # Allow filtering by category
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Allow filtering by is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def get_permissions(self):
        """
        Allow public read access (list, retrieve) for products.
        Require authentication for write operations (create, update, delete).
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='meta-sync')
    def meta_sync(self, request, pk=None):
        """
        Manually trigger sync of a product to Meta Catalog.
        Creates the product if it doesn't exist, updates if it does.
        
        POST /crm-api/products/products/{id}/meta-sync/
        """
        product = self.get_object()
        
        if not product.sku:
            return Response(
                {'error': 'Product does not have a SKU. SKU is required for Meta Catalog sync.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not product.is_active:
            return Response(
                {'error': 'Product is not active. Only active products can be synced to Meta Catalog.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = MetaCatalogService()
            result = service.sync_product_update(product)
            
            # Refresh from DB to get updated catalog_id
            product.refresh_from_db()
            
            return Response({
                'success': True,
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'catalog_id': product.whatsapp_catalog_id,
                'message': 'Product synced to Meta Catalog successfully',
                'meta_response': result
            })
        except ValueError as e:
            return Response({
                'success': False,
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'error': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='meta-visibility')
    def meta_visibility(self, request, pk=None):
        """
        Set the visibility of a product in Meta Catalog.
        
        POST /crm-api/products/products/{id}/meta-visibility/
        Body: {
            "visibility": "published"  // or "hidden"
        }
        """
        product = self.get_object()
        serializer = MetaCatalogVisibilitySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if not product.whatsapp_catalog_id:
            return Response(
                {'error': 'Product has not been synced to Meta Catalog yet. Sync the product first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        visibility = serializer.validated_data['visibility']
        
        try:
            service = MetaCatalogService()
            result = service.set_product_visibility(product, visibility)
            
            return Response({
                'success': True,
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'visibility': visibility,
                'message': f'Product visibility set to "{visibility}" successfully',
                'meta_response': result
            })
        except ValueError as e:
            return Response({
                'success': False,
                'product_id': product.id,
                'product_name': product.name,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'product_id': product.id,
                'product_name': product.name,
                'error': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='meta-status')
    def meta_status(self, request, pk=None):
        """
        Get the current status of a product in Meta Catalog.
        
        GET /crm-api/products/products/{id}/meta-status/
        """
        product = self.get_object()
        
        if not product.whatsapp_catalog_id:
            return Response({
                'synced': False,
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'message': 'Product has not been synced to Meta Catalog yet.',
                'local_sync_info': {
                    'sync_attempts': product.meta_sync_attempts,
                    'last_error': product.meta_sync_last_error,
                    'last_attempt': product.meta_sync_last_attempt,
                    'last_success': product.meta_sync_last_success
                }
            })
        
        try:
            service = MetaCatalogService()
            meta_data = service.get_product_from_catalog(product)
            
            return Response({
                'synced': True,
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'catalog_id': product.whatsapp_catalog_id,
                'meta_catalog_data': meta_data,
                'local_sync_info': {
                    'sync_attempts': product.meta_sync_attempts,
                    'last_error': product.meta_sync_last_error,
                    'last_attempt': product.meta_sync_last_attempt,
                    'last_success': product.meta_sync_last_success
                }
            })
        except ValueError as e:
            return Response({
                'synced': True,
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'catalog_id': product.whatsapp_catalog_id,
                'error': str(e),
                'message': 'Product has a catalog ID but could not fetch status from Meta',
                'local_sync_info': {
                    'sync_attempts': product.meta_sync_attempts,
                    'last_error': product.meta_sync_last_error,
                    'last_attempt': product.meta_sync_last_attempt,
                    'last_success': product.meta_sync_last_success
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=False, methods=['post'], url_path='meta-batch-visibility')
    def meta_batch_visibility(self, request):
        """
        Set visibility for multiple products in Meta Catalog.
        
        POST /crm-api/products/products/meta-batch-visibility/
        Body: {
            "product_ids": [1, 2, 3],
            "visibility": "published"  // or "hidden"
        }
        """
        serializer = MetaCatalogBatchUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_ids = serializer.validated_data['product_ids']
        visibility = serializer.validated_data.get('visibility')
        
        if not visibility:
            return Response(
                {'error': 'visibility field is required for batch visibility update'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        products = Product.objects.filter(id__in=product_ids)
        
        # Build updates list
        updates = []
        skipped = []
        
        for product in products:
            if not product.sku:
                skipped.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'reason': 'No SKU'
                })
                continue
            
            if not product.whatsapp_catalog_id:
                skipped.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'reason': 'Not synced to Meta Catalog'
                })
                continue
            
            updates.append({
                'product': product,
                'data': {'visibility': visibility}
            })
        
        if not updates:
            return Response({
                'success': False,
                'message': 'No products eligible for batch update',
                'skipped': skipped
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = MetaCatalogService()
            result = service.batch_update_products(updates)
            
            return Response({
                'success': True,
                'updated_count': len(updates),
                'visibility': visibility,
                'skipped': skipped,
                'meta_response': result
            })
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e),
                'skipped': skipped
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'skipped': skipped
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='meta-batch-sync')
    def meta_batch_sync(self, request):
        """
        Sync multiple products to Meta Catalog.
        
        POST /crm-api/products/products/meta-batch-sync/
        Body: {
            "product_ids": [1, 2, 3]
        }
        """
        serializer = MetaCatalogBatchUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_ids = serializer.validated_data['product_ids']
        products = Product.objects.filter(id__in=product_ids)
        results = []
        
        service = MetaCatalogService()
        
        for product in products:
            if not product.sku:
                results.append({
                    'success': False,
                    'product_id': product.id,
                    'product_name': product.name,
                    'sku': None,
                    'error': 'No SKU'
                })
                continue
            
            if not product.is_active:
                results.append({
                    'success': False,
                    'product_id': product.id,
                    'product_name': product.name,
                    'sku': product.sku,
                    'error': 'Product is not active'
                })
                continue
            
            try:
                result = service.sync_product_update(product)
                product.refresh_from_db()
                
                results.append({
                    'success': True,
                    'product_id': product.id,
                    'product_name': product.name,
                    'sku': product.sku,
                    'catalog_id': product.whatsapp_catalog_id,
                    'message': 'Synced successfully'
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'product_id': product.id,
                    'product_name': product.name,
                    'sku': product.sku,
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r.get('success'))
        
        return Response({
            'total': len(results),
            'success_count': success_count,
            'failure_count': len(results) - success_count,
            'results': results
        })

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


# Lightweight endpoint to set CSRF cookie for SPA frontends
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ensure_csrf_cookie
def csrf_cookie(request):
    import logging
    logger = logging.getLogger(__name__)
    # Explicitly get the token to ensure the cookie is set in the response
    token = get_token(request)
    logger.info(f"CSRF cookie endpoint called. Token: {token[:10]}...")
    return Response({'detail': 'CSRF cookie set', 'token': token})

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

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout_cart(self, request):
        """
        Create an Order from the current session/user cart and clear the cart.

        POST /crm-api/products/cart/checkout/
        Body:
        {
          "full_name": "John Doe",
          "email": "john@example.com",
          "phone": "+263771234567",
          "address": "123 Main St",
          "city": "Harare",
          "notes": "Leave at gate"
        }

        Returns: { order_number, amount, currency }
        """
        from django.db import transaction
        from decimal import Decimal
        from customer_data.models import Order, OrderItem, CustomerProfile
        from conversations.models import Contact
        import uuid

        cart = self._get_or_create_cart(request)
        cart_items = list(cart.items.select_related('product'))
        if not cart_items:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        full_name = request.data.get('full_name', '').strip()
        email = request.data.get('email', '').strip()
        phone = request.data.get('phone', '').strip()
        address = request.data.get('address', '').strip()
        city = request.data.get('city', '').strip()
        notes = request.data.get('notes', '').strip()

        # Basic validation
        if not full_name or not email or not phone or not address:
            return Response({'error': 'full_name, email, phone, and address are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize phone (remove spaces, ensure it's valid)
        phone_norm = phone.replace(' ', '').strip() if phone else ''
        if not phone_norm:
            return Response({'error': 'Phone number is required and cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Derive currency from first item or default
        currency = cart_items[0].product.currency if cart_items and cart_items[0].product.currency else 'USD'

        # Calculate total
        total_amount = Decimal('0.00')
        for ci in cart_items:
            unit_price = Decimal(str(ci.product.price)) if ci.product.price else Decimal('0.00')
            total_amount += unit_price * ci.quantity

        # Build order notes with delivery details
        delivery_summary = f"Delivery to: {full_name}, {phone_norm}, {address}{', ' + city if city else ''}."
        if notes:
            delivery_summary += f" Notes: {notes}"

        # Create a customer contact/profile (or get existing)
        try:
            contact, _ = Contact.objects.get_or_create(
                whatsapp_id=phone_norm,
                defaults={'name': full_name}
            )
            customer_profile, _ = CustomerProfile.objects.get_or_create(contact=contact)
        except Exception as e:
            return Response({'error': f'Failed to create/update contact: {str(e)[:180]}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Update email and address on profile when provided
        updated_fields = []
        if email and not customer_profile.email:
            customer_profile.email = email
            updated_fields.append('email')
        if address and not customer_profile.address_line_1:
            customer_profile.address_line_1 = address
            updated_fields.append('address_line_1')
        if city and not customer_profile.city:
            customer_profile.city = city
            updated_fields.append('city')
        if full_name and not customer_profile.get_full_name():
            # Try split name
            parts = full_name.split(' ', 1)
            if parts and not customer_profile.first_name:
                customer_profile.first_name = parts[0]
                updated_fields.append('first_name')
            if len(parts) > 1 and not customer_profile.last_name:
                customer_profile.last_name = parts[1]
                updated_fields.append('last_name')
        if updated_fields:
            customer_profile.save(update_fields=updated_fields)

        # Generate unique order number
        order_num = None
        for _ in range(100):
            candidate = f"WA-{uuid.uuid4().hex[:6].upper()}"
            if not Order.objects.filter(order_number=candidate).exists():
                order_num = candidate
                break
        if not order_num:
            order_num = f"WA-{uuid.uuid4().hex[:8].upper()}"

        try:
            with transaction.atomic():
                # Create order with defensive null-safe assigned_agent
                order_data = {
                    'customer': customer_profile,
                    'name': f"Online Order for {full_name}",
                    'order_number': order_num,
                    'stage': Order.Stage.CLOSED_WON,
                    'payment_status': Order.PaymentStatus.PENDING,
                    'source': Order.Source.API,
                    'amount': total_amount,
                    'currency': currency,
                    'notes': delivery_summary,
                }
                # Only add assigned_agent if the profile has one
                if hasattr(customer_profile, 'assigned_agent') and customer_profile.assigned_agent:
                    order_data['assigned_agent'] = customer_profile.assigned_agent
                
                order = Order.objects.create(**order_data)

                order_items_to_create = []
                for ci in cart_items:
                    unit_price = Decimal(str(ci.product.price)) if ci.product.price else Decimal('0.00')
                    order_items_to_create.append(OrderItem(
                        order=order,
                        product=ci.product,
                        quantity=ci.quantity,
                        unit_price=unit_price,
                        total_amount=unit_price * ci.quantity
                    ))
                if order_items_to_create:
                    OrderItem.objects.bulk_create(order_items_to_create)

                # Clear the cart
                cart.items.all().delete()

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[checkout_cart] Exception: {str(e)}\n{tb}")
            return Response({'error': f'Failed to create order: {str(e)[:180]}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': True,
            'order_number': order.order_number,
            'amount': str(order.amount),
            'currency': order.currency
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
    
    @action(detail=True, methods=['post'], url_path='checkout')
    def checkout(self, request, pk=None):
        """
        Checkout an item and mark it as in transit.
        Optionally link to an order for fulfillment tracking.
        
        POST /crm-api/items/{id}/checkout/
        Body: {
            "destination_location": "warehouse|customer|technician|manufacturer|retail|outsourced|disposed",
            "notes": "Optional notes",
            "order_item_id": 123  // Optional: Link to OrderItem for fulfillment
        }
        
        If order_item_id is provided:
        - Validates that product SKU matches the ordered product
        - Links the physical item to the order line item
        - Updates fulfillment tracking (units_assigned counter)
        - Returns validation error if SKU mismatch
        """
        item = self.get_object()
        destination = request.data.get('destination_location')
        if not destination:
            return Response({'error': 'destination_location is required'}, status=status.HTTP_400_BAD_REQUEST)
        if destination not in SerializedItem.Location.values:
            return Response({'error': 'Invalid destination_location'}, status=status.HTTP_400_BAD_REQUEST)
        
        order_item_id = request.data.get('order_item_id')
        
        try:
            history = ItemTrackingService.checkout_item(
                item=item,
                destination_location=destination,
                transferred_by=request.user,
                notes=request.data.get('notes', ''),
                order_item_id=order_item_id
            )
            
            # Include fulfillment info in response if order linked
            response_data = ItemLocationHistorySerializer(history).data
            if order_item_id and item.order_item:
                response_data['fulfillment'] = {
                    'order_number': item.order_item.order.order_number,
                    'product_name': item.order_item.product.name,
                    'units_assigned': item.order_item.units_assigned,
                    'quantity_ordered': item.order_item.quantity,
                    'is_fully_assigned': item.order_item.is_fully_assigned
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='checkin')
    def checkin(self, request, pk=None):
        """
        Check an item into its destination location from in transit.
        
        POST /crm-api/items/{id}/checkin/
        Body: {
            "new_location": "warehouse|customer|technician|manufacturer|retail|outsourced|disposed",
            "notes": "Optional notes"
        }
        """
        item = self.get_object()
        new_location = request.data.get('new_location')
        if not new_location:
            return Response({'error': 'new_location is required'}, status=status.HTTP_400_BAD_REQUEST)
        if new_location not in SerializedItem.Location.values:
            return Response({'error': 'Invalid new_location'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            history = ItemTrackingService.checkin_item(
                item=item,
                new_location=new_location,
                transferred_by=request.user,
                notes=request.data.get('notes', '')
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ItemLocationHistorySerializer(history).data, status=status.HTTP_200_OK)
    
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

# ============================================================================
# Retailer Branch Portal ViewSet (for branch operations)
# ============================================================================

class RetailerBranchPortalViewSet(viewsets.ViewSet):
    """
    ViewSet for retailer BRANCH portal operations.
    Branches (not retailers) perform check-in/checkout and serial number management.
    Retailers can only manage branches, not perform these operations directly.
    """
    permission_classes = [IsRetailerBranchOrAdmin]

    def _get_branch(self, request):
        """Get the retailer branch profile for the current user."""
        if hasattr(request.user, "retailer_branch_profile"):
            return request.user.retailer_branch_profile
        return None

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        """
        Get branch dashboard statistics.
        
        GET /crm-api/products/retailer-branch/dashboard/
        """
        user = request.user
        branch = self._get_branch(request)
        
        # Get items held by this branch (at retail location)
        branch_items = SerializedItem.objects.filter(
            current_holder=user,
            current_location=SerializedItem.Location.RETAIL
        ).select_related("product")
        
        # Count items by status
        items_in_stock = branch_items.filter(status=SerializedItem.Status.IN_STOCK).count()
        items_sold = SerializedItem.objects.filter(
            location_history__transferred_by=user,
            location_history__transfer_reason=ItemLocationHistory.TransferReason.SALE
        ).distinct().count()
        items_in_transit = branch_items.filter(status=SerializedItem.Status.IN_TRANSIT).count()
        
        # Get recent checkout history (last 10)
        recent_checkout_ids = ItemLocationHistory.objects.filter(
            transferred_by=user,
            transfer_reason=ItemLocationHistory.TransferReason.SALE
        ).values_list("serialized_item_id", flat=True).order_by("-timestamp")[:10]
        
        recent_checkouts = SerializedItem.objects.filter(
            id__in=list(recent_checkout_ids)
        ).select_related("product")
        
        # Get recent checkin history (last 10)
        recent_checkin_ids = ItemLocationHistory.objects.filter(
            to_holder=user,
            to_location=SerializedItem.Location.RETAIL
        ).values_list("serialized_item_id", flat=True).order_by("-timestamp")[:10]
        
        recent_checkins = SerializedItem.objects.filter(
            id__in=list(recent_checkin_ids)
        ).select_related("product")
        
        stats = {
            "branch_name": branch.branch_name if branch else None,
            "retailer_name": branch.retailer.company_name if branch else None,
            "total_items": branch_items.count(),
            "items_in_stock": items_in_stock,
            "items_sold": items_sold,
            "items_in_transit": items_in_transit,
            "recent_checkouts": RetailerInventoryItemSerializer(recent_checkouts, many=True).data,
            "recent_checkins": RetailerInventoryItemSerializer(recent_checkins, many=True).data,
        }
        
        return Response(stats)

    @action(detail=False, methods=["get"], url_path="inventory")
    def inventory(self, request):
        """
        Get branch inventory (items at this branch location).
        
        GET /crm-api/products/retailer-branch/inventory/
        """
        user = request.user
        
        # Get items held by this branch
        items = SerializedItem.objects.filter(
            current_holder=user,
            current_location=SerializedItem.Location.RETAIL
        ).select_related("product").order_by("-updated_at")
        
        serializer = RetailerInventoryItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout_item(self, request):
        """
        Checkout an item (send to customer).
        
        POST /crm-api/products/retailer-branch/checkout/
        Body: {
            "serial_number": "SN12345",
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "notes": "Delivered on site"
        }
        """
        serializer = RetailerItemCheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serial_number = serializer.validated_data["serial_number"]
        customer_name = serializer.validated_data["customer_name"]
        customer_phone = serializer.validated_data.get("customer_phone", "")
        notes = serializer.validated_data.get("notes", "")
        
        # Find the item by serial number or barcode
        try:
            item = SerializedItem.objects.select_related("product").get(
                Q(serial_number=serial_number) | Q(barcode=serial_number)
            )
        except SerializedItem.DoesNotExist:
            return Response(
                {"error": f"No item found with serial number or barcode: {serial_number}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except SerializedItem.MultipleObjectsReturned:
            return Response(
                {"error": "Multiple items found. Please use a unique identifier."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if item is at this branch location
        if item.current_holder != request.user or item.current_location != SerializedItem.Location.RETAIL:
            return Response(
                {"error": "This item is not currently in your branch inventory."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Transfer item to customer
        branch = self._get_branch(request)
        checkout_notes = f"Sold to: {customer_name}"
        if customer_phone:
            checkout_notes += f" (Phone: {customer_phone})"
        if branch:
            checkout_notes += f" | Branch: {branch.branch_name}"
        if notes:
            checkout_notes += f". {notes}"
        
        history = ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.CUSTOMER,
            to_holder=None,  # Customer is not a system user
            reason=ItemLocationHistory.TransferReason.SALE,
            notes=checkout_notes,
            transferred_by=request.user,
            update_status=SerializedItem.Status.SOLD
        )
        
        return Response({
            "message": f"Item {item.serial_number} checked out successfully.",
            "item": RetailerInventoryItemSerializer(item).data,
            "history": ItemLocationHistorySerializer(history).data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="checkin")
    def checkin_item(self, request):
        """
        Check-in an item (receive from warehouse or return).
        
        POST /crm-api/products/retailer-branch/checkin/
        Body: {
            "serial_number": "SN12345",
            "notes": "Received from main warehouse"
        }
        """
        serializer = RetailerItemCheckinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serial_number = serializer.validated_data["serial_number"]
        notes = serializer.validated_data.get("notes", "")
        
        # Find the item by serial number or barcode
        try:
            item = SerializedItem.objects.select_related("product").get(
                Q(serial_number=serial_number) | Q(barcode=serial_number)
            )
        except SerializedItem.DoesNotExist:
            return Response(
                {"error": f"No item found with serial number or barcode: {serial_number}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except SerializedItem.MultipleObjectsReturned:
            return Response(
                {"error": "Multiple items found. Please use a unique identifier."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Transfer item to branch location
        branch = self._get_branch(request)
        checkin_notes = f"Checked in by branch"
        if branch:
            checkin_notes += f": {branch.branch_name}"
        if notes:
            checkin_notes += f". {notes}"
        
        history = ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.RETAIL,
            to_holder=request.user,
            reason=ItemLocationHistory.TransferReason.STOCK_RECEIPT,
            notes=checkin_notes.strip(),
            transferred_by=request.user,
            update_status=SerializedItem.Status.IN_STOCK
        )
        
        return Response({
            "message": f"Item {item.serial_number} checked in successfully.",
            "item": RetailerInventoryItemSerializer(item).data,
            "history": ItemLocationHistorySerializer(history).data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="add-serial-number")
    def add_serial_number(self, request):
        """
        Add a new serial number to a product (create a serialized item).
        
        POST /crm-api/products/retailer-branch/add-serial-number/
        Body: {
            "product_id": 123,
            "serial_number": "SN12345",
            "barcode": "123456789"
        }
        """
        serializer = RetailerAddSerialNumberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = serializer.validated_data["product_id"]
        serial_number = serializer.validated_data["serial_number"]
        barcode = serializer.validated_data.get("barcode") or None
        
        # Get the product
        product = get_object_or_404(Product, id=product_id)
        
        # Create the serialized item at branch location
        branch = self._get_branch(request)
        branch_info = f" at branch {branch.branch_name}" if branch else ""
        item = SerializedItem.objects.create(
            product=product,
            serial_number=serial_number,
            barcode=barcode,
            status=SerializedItem.Status.IN_STOCK,
            current_location=SerializedItem.Location.RETAIL,
            current_holder=request.user,
            location_notes=f"Added by branch{branch_info}: {request.user.get_full_name() or request.user.username}"
        )
        
        # Create initial location history
        ItemLocationHistory.objects.create(
            serialized_item=item,
            from_location=None,
            to_location=SerializedItem.Location.RETAIL,
            to_holder=request.user,
            transfer_reason=ItemLocationHistory.TransferReason.STOCK_RECEIPT,
            notes=f"Initial stock entry by branch{branch_info}",
            transferred_by=request.user
        )
        
        return Response({
            "message": f"Serial number {serial_number} added successfully.",
            "item": RetailerInventoryItemSerializer(item).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="scan/(?P<identifier>[^/.]+)")
    def scan_item(self, request, identifier=None):
        """
        Scan an item by serial number or barcode.
        
        GET /crm-api/products/retailer-branch/scan/{identifier}/
        """
        if not identifier:
            return Response(
                {"error": "Identifier (serial number or barcode) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find the item by serial number or barcode
        try:
            item = SerializedItem.objects.select_related("product", "current_holder").get(
                Q(serial_number=identifier) | Q(barcode=identifier)
            )
        except SerializedItem.DoesNotExist:
            # Also try to find by product barcode/SKU
            try:
                product = Product.objects.get(Q(barcode=identifier) | Q(sku=identifier))
                return Response({
                    "found": True,
                    "type": "product",
                    "data": ProductSerializer(product).data,
                    "message": f"Product found: {product.name}. No specific serialized item."
                })
            except Product.DoesNotExist:
                return Response(
                    {"found": False, "message": f"No item found with identifier: {identifier}"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except SerializedItem.MultipleObjectsReturned:
            return Response(
                {"error": "Multiple items found. Please use a unique identifier."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if item is in this branch's inventory
        is_in_inventory = (
            item.current_holder == request.user and 
            item.current_location == SerializedItem.Location.RETAIL
        )
        
        return Response({
            "found": True,
            "type": "serialized_item",
            "is_in_inventory": is_in_inventory,
            "data": SerializedItemDetailSerializer(item).data,
            "message": f"Item found: {item.product.name} (SN: {item.serial_number})"
        })

    @action(detail=False, methods=["get"], url_path="history")
    def transaction_history(self, request):
        """
        Get transaction history for this branch.
        
        GET /crm-api/products/retailer-branch/history/
        """
        user = request.user
        
        # Get all location history where this branch was involved
        history = ItemLocationHistory.objects.filter(
            Q(transferred_by=user) | Q(from_holder=user) | Q(to_holder=user)
        ).select_related(
            "serialized_item", 
            "serialized_item__product",
            "from_holder",
            "to_holder",
            "transferred_by"
        ).order_by("-timestamp")[:50]
        
        serializer = ItemLocationHistorySerializer(history, many=True)
        return Response(serializer.data)

    # ========================================================================
    # Order-Based Dispatch Endpoints
    # ========================================================================

    @action(detail=False, methods=["get"], url_path="order/verify/(?P<order_number>[^/.]+)")
    def verify_order(self, request, order_number=None):
        """
        Verify an order exists and is eligible for dispatch.
        
        GET /crm-api/products/retailer-branch/order/verify/{order_number}/
        
        Returns order details including items to be dispatched and their fulfillment status.
        """
        from customer_data.models import Order
        
        if not order_number:
            return Response(
                {"error": "Order number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find the order
        try:
            order = Order.objects.prefetch_related(
                "items", "items__product"
            ).select_related("customer").get(order_number=order_number)
        except Order.DoesNotExist:
            return Response(
                {"error": f"Order with number '{order_number}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize the order with dispatch info
        serializer = OrderDispatchSerializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="order/dispatch-item")
    def dispatch_item(self, request):
        """
        Dispatch a single item for an order.
        
        POST /crm-api/products/retailer-branch/order/dispatch-item/
        Body: {
            "order_number": "ORD-12345",
            "serial_number": "SN12345",  // Can be serial number or barcode
            "order_item_id": 123,  // Optional - auto-matched if not provided
            "notes": "Packed and ready"
        }
        
        This endpoint:
        1. Validates the order exists and is eligible for dispatch
        2. Finds the serialized item by serial number or barcode
        3. Validates the product matches an order line item (or matches specific order_item_id)
        4. Links the SerializedItem to the OrderItem
        5. Updates fulfillment tracking (units_assigned)
        6. Records the dispatch in ItemLocationHistory
        7. Returns dispatch confirmation with timestamp
        """
        from customer_data.models import Order, OrderItem
        
        serializer = OrderItemScanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        order_number = serializer.validated_data["order_number"]
        serial_number = serializer.validated_data["serial_number"]
        order_item_id = serializer.validated_data.get("order_item_id")
        notes = serializer.validated_data.get("notes", "")
        
        # 1. Find the order
        try:
            order = Order.objects.prefetch_related(
                "items", "items__product"
            ).get(order_number=order_number)
        except Order.DoesNotExist:
            return Response(
                {"error": f"Order with number '{order_number}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 2. Check if order is eligible for dispatch
        if order.stage != "closed_won":
            return Response(
                {"error": f"Order is not ready for dispatch. Current stage: {order.get_stage_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.payment_status not in ["paid", "partially_paid"]:
            return Response(
                {"error": f"Order payment not confirmed. Status: {order.get_payment_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. Find the serialized item
        try:
            item = SerializedItem.objects.select_related("product").get(
                Q(serial_number=serial_number) | Q(barcode=serial_number)
            )
        except SerializedItem.DoesNotExist:
            return Response(
                {"error": f"No item found with serial number or barcode: {serial_number}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except SerializedItem.MultipleObjectsReturned:
            return Response(
                {"error": "Multiple items found. Please use a unique identifier."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 4. Check if item is already assigned to an order
        if item.order_item is not None:
            return Response(
                {"error": f"This item is already assigned to order {item.order_item.order.order_number}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 5. Find the matching order item (or use provided order_item_id)
        if order_item_id:
            try:
                target_order_item = OrderItem.objects.get(id=order_item_id, order=order)
            except OrderItem.DoesNotExist:
                return Response(
                    {"error": f"Order item {order_item_id} not found in this order"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate SKU match
            if item.product.sku != target_order_item.product.sku:
                return Response(
                    {"error": f"Product SKU mismatch! Expected: {target_order_item.product.sku} "
                             f"({target_order_item.product.name}), but scanned: {item.product.sku} "
                             f"({item.product.name})"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Auto-match: find an order item with matching product that is not fully assigned
            matching_items = order.items.filter(
                product=item.product,
                is_fully_assigned=False
            )
            
            if not matching_items.exists():
                # Check if product exists in order but is fully assigned
                all_matching = order.items.filter(product=item.product)
                if all_matching.exists():
                    return Response(
                        {"error": f"All units of {item.product.name} for this order have been dispatched"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {"error": f"Product {item.product.name} (SKU: {item.product.sku}) is not part of this order"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            target_order_item = matching_items.first()
        
        # 6. Check if order item is already fully assigned
        if target_order_item.is_fully_assigned:
            return Response(
                {"error": f"All {target_order_item.quantity} units of {target_order_item.product.name} "
                         f"have already been dispatched for this order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 7. Perform the dispatch - link item to order and update fulfillment
        branch = self._get_branch(request)
        dispatch_notes = f"Dispatched for Order #{order_number}"
        if branch:
            dispatch_notes += f" by branch {branch.branch_name}"
        if notes:
            dispatch_notes += f". {notes}"
        
        # Link item to order item
        item.order_item = target_order_item
        
        # Update fulfillment tracking
        target_order_item.units_assigned += 1
        if target_order_item.units_assigned >= target_order_item.quantity:
            target_order_item.is_fully_assigned = True
        target_order_item.save(update_fields=["units_assigned", "is_fully_assigned"])
        
        # Transfer item (mark as in transit/sold)
        history = ItemTrackingService.transfer_item(
            item=item,
            to_location=SerializedItem.Location.CUSTOMER,
            to_holder=None,  # Customer is not a system user
            reason=ItemLocationHistory.TransferReason.SALE,
            notes=dispatch_notes,
            related_order=order,
            transferred_by=request.user,
            update_status=SerializedItem.Status.SOLD
        )
        
        # Save item with order_item link
        item.save(update_fields=["order_item"])
        
        # 8. Return dispatch confirmation
        return Response({
            "success": True,
            "message": f"Item {item.serial_number} dispatched for order {order_number}",
            "item": {
                "item_id": item.id,
                "serial_number": item.serial_number,
                "barcode": item.barcode,
                "product_name": item.product.name,
                "order_item_id": target_order_item.id,
                "units_assigned": target_order_item.units_assigned,
                "quantity_ordered": target_order_item.quantity,
                "is_fully_assigned": target_order_item.is_fully_assigned,
                "dispatch_timestamp": history.timestamp.isoformat()
            },
            "order_fulfillment": {
                "order_number": order.order_number,
                "items_remaining": sum(
                    1 for oi in order.items.all() 
                    if not oi.is_fully_assigned
                ),
                "total_items": order.items.count(),
                "all_dispatched": all(oi.is_fully_assigned for oi in order.items.all())
            }
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="order/(?P<order_number>[^/.]+)/dispatch-status")
    def order_dispatch_status(self, request, order_number=None):
        """
        Get dispatch status for an order - shows which items have been dispatched.
        
        GET /crm-api/products/retailer-branch/order/{order_number}/dispatch-status/
        """
        from customer_data.models import Order
        
        if not order_number:
            return Response(
                {"error": "Order number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = Order.objects.prefetch_related(
                "items", "items__product", "items__assigned_items"
            ).get(order_number=order_number)
        except Order.DoesNotExist:
            return Response(
                {"error": f"Order with number '{order_number}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build dispatch status for each order item
        items_status = []
        for order_item in order.items.all():
            dispatched_items = []
            for serial_item in order_item.assigned_items.select_related("product"):
                # Get the dispatch history entry for this item
                dispatch_history = serial_item.location_history.filter(
                    related_order=order
                ).order_by("-timestamp").first()
                
                dispatched_items.append({
                    "serial_number": serial_item.serial_number,
                    "barcode": serial_item.barcode,
                    "status": serial_item.status,
                    "status_display": serial_item.get_status_display(),
                    "dispatched_at": dispatch_history.timestamp.isoformat() if dispatch_history else None,
                    "dispatched_by": (
                        dispatch_history.transferred_by.get_full_name() or 
                        dispatch_history.transferred_by.username
                    ) if dispatch_history and dispatch_history.transferred_by else None
                })
            
            items_status.append({
                "order_item_id": order_item.id,
                "product_name": order_item.product.name,
                "product_sku": order_item.product.sku,
                "quantity": order_item.quantity,
                "units_assigned": order_item.units_assigned,
                "is_fully_assigned": order_item.is_fully_assigned,
                "remaining": order_item.quantity - order_item.units_assigned,
                "dispatched_items": dispatched_items
            })
        
        return Response({
            "order_number": order.order_number,
            "order_id": str(order.id),
            "customer_name": (
                order.customer.get_full_name() if order.customer else None
            ),
            "stage": order.stage,
            "stage_display": order.get_stage_display(),
            "payment_status": order.payment_status,
            "payment_status_display": order.get_payment_status_display(),
            "items": items_status,
            "total_items": order.items.count(),
            "items_fully_dispatched": sum(1 for oi in order.items.all() if oi.is_fully_assigned),
            "all_dispatched": all(oi.is_fully_assigned for oi in order.items.all())
        })


# ============================================================================
# Legacy Retailer Portal ViewSet (deprecated - use RetailerBranchPortalViewSet)
# ============================================================================

class RetailerPortalViewSet(viewsets.ViewSet):
    """
    DEPRECATED: This ViewSet is kept for backward compatibility.
    New implementations should use RetailerBranchPortalViewSet.
    
    Retailers should manage branches via /crm-api/users/retailers/me/branches/
    Branches perform check-in/checkout via /crm-api/products/retailer-branch/
    """
    permission_classes = [IsRetailerOrAdmin]

    def _get_retailer(self, request):
        """Get the retailer profile for the current user."""
        if hasattr(request.user, "retailer_profile"):
            return request.user.retailer_profile
        return None

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        """
        Get retailer dashboard statistics.
        NOTE: This is for the parent retailer account - shows aggregate data across all branches.
        """
        retailer = self._get_retailer(request)
        
        if retailer:
            # Get all branch users for this retailer
            branch_users = [b.user for b in retailer.branches.filter(is_active=True)]
            
            # Aggregate stats across all branches
            total_items = SerializedItem.objects.filter(
                current_holder__in=branch_users,
                current_location=SerializedItem.Location.RETAIL
            ).count()
            
            items_sold = SerializedItem.objects.filter(
                location_history__transferred_by__in=branch_users,
                location_history__transfer_reason=ItemLocationHistory.TransferReason.SALE
            ).distinct().count()
            
            return Response({
                "company_name": retailer.company_name,
                "total_branches": retailer.branches.count(),
                "active_branches": retailer.branches.filter(is_active=True).count(),
                "total_items_across_branches": total_items,
                "total_items_sold": items_sold,
                "message": "Use individual branch accounts for check-in/checkout operations."
            })
        
        return Response({
            "error": "You must be a retailer to access this endpoint.",
            "message": "If you are a branch, use /crm-api/products/retailer-branch/dashboard/"
        }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=["get"], url_path="inventory")
    def inventory(self, request):
        """Deprecated - branches should use their own endpoint."""
        return Response({
            "error": "Retailers cannot view inventory directly.",
            "message": "Individual branches should access /crm-api/products/retailer-branch/inventory/"
        }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout_item(self, request):
        """Deprecated - only branches can checkout items."""
        return Response({
            "error": "Retailers cannot checkout items directly.",
            "message": "Individual branches should access /crm-api/products/retailer-branch/checkout/"
        }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=["post"], url_path="checkin")
    def checkin_item(self, request):
        """Deprecated - only branches can checkin items."""
        return Response({
            "error": "Retailers cannot checkin items directly.",
            "message": "Individual branches should access /crm-api/products/retailer-branch/checkin/"
        }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=["post"], url_path="add-serial-number")
    def add_serial_number(self, request):
        """Deprecated - only branches can add serial numbers."""
        return Response({
            "error": "Retailers cannot add serial numbers directly.",
            "message": "Individual branches should access /crm-api/products/retailer-branch/add-serial-number/"
        }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=["get"], url_path="scan/(?P<identifier>[^/.]+)")
    def scan_item(self, request, identifier=None):
        """Deprecated - only branches can scan items."""
        return Response({
            "error": "Retailers cannot scan items directly.",
            "message": "Individual branches should access /crm-api/products/retailer-branch/scan/{identifier}/"
        }, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=["get"], url_path="history")
    def transaction_history(self, request):
        """Deprecated - only branches can view their history."""
        return Response({
            "error": "Retailers cannot view transaction history directly.",
            "message": "Individual branches should access /crm-api/products/retailer-branch/history/"
        }, status=status.HTTP_403_FORBIDDEN)

class ItemLocationHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and managing item location history records.
    Provides paginated list of all check-in/check-out transactions.
    """
    queryset = ItemLocationHistory.objects.select_related(
        'serialized_item',
        'serialized_item__product',
        'from_holder',
        'to_holder'
    ).order_by('-timestamp')
    serializer_class = ItemLocationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Use DRF default pagination from settings
    
    def get_queryset(self):
        """Filter queryset based on optional query parameters."""
        queryset = super().get_queryset()
        
        # Filter by date range if provided
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        # Filter by location if provided
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(to_location=location)
        
        # Filter by transfer reason if provided
        reason = self.request.query_params.get('reason')
        if reason:
            queryset = queryset.filter(transfer_reason=reason)
        
        # Search by serial number or barcode
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(serialized_item__serial_number__icontains=search) |
                Q(serialized_item__barcode__icontains=search) |
                Q(serialized_item__product__name__icontains=search)
            )
        
        return queryset
    
    def perform_destroy(self, instance):
        """Delete an item location history record."""
        instance.delete()

# Zoho Inventory Sync Views

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse


@staff_member_required
def trigger_sync_view(request: HttpRequest) -> HttpResponse:
    """
    Admin view to trigger Zoho Inventory product sync.
    
    This view triggers a Celery task to sync products from Zoho Inventory
    and redirects back to the product list with a success message.
    
    Args:
        request: HttpRequest object
        
    Returns:
        HttpResponse redirecting to admin product list
    """
    from .tasks import task_sync_zoho_products
    
    try:
        # Trigger the Celery task asynchronously
        task = task_sync_zoho_products.delay()
        
        messages.success(
            request,
            f'Zoho product sync has been initiated. Task ID: {task.id}. '
            'Products will be synced in the background. Check logs for progress.'
        )
    except Exception as e:
        messages.error(
            request,
            f'Failed to initiate Zoho sync: {str(e)}'
        )
    
    # Redirect back to the product list in admin
    return redirect('admin:products_and_services_product_changelist')
