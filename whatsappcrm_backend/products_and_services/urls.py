from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.ProductCategoryViewSet, basename='productcategory')
router.register(r'serialized-items', views.SerializedItemViewSet, basename='serializeditem')

app_name = 'products_and_services_api'

urlpatterns = [
    path('', include(router.urls)),
]
