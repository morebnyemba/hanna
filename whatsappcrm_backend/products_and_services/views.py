from rest_framework import viewsets, permissions
from .models import Product, ProductCategory, SerializedItem
from .serializers import ProductSerializer, ProductCategorySerializer, SerializedItemSerializer

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