from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.ProductCategoryViewSet, basename='productcategory')
router.register(r'serialized-items', views.SerializedItemViewSet, basename='serializeditem')
router.register(r'barcode', views.BarcodeScanViewSet, basename='barcode')
router.register(r'cart', views.CartViewSet, basename='cart')
# Item tracking endpoints
router.register(r'items', views.ItemTrackingViewSet, basename='item-tracking')

app_name = 'products_and_services_api'

urlpatterns = [
    path('', include(router.urls)),
]
