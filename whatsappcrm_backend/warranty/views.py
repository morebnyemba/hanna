from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, viewsets
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Warranty, WarrantyClaim
from customer_data.models import JobCard, CustomerProfile
from customer_data.serializers import JobCardSerializer, JobCardDetailSerializer
from products_and_services.models import Product
from products_and_services.serializers import ProductSerializer
from .permissions import IsManufacturer
from .serializers import WarrantyClaimListSerializer, WarrantyClaimCreateSerializer, ManufacturerSerializer

class AdminWarrantyClaimListView(generics.ListAPIView):
    """
    Provides a paginated list of all warranty claims for admin users.
    """
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return WarrantyClaim.objects.all().select_related('warranty__serialized_item__product', 'warranty__customer').order_by('-created_at')

class AdminWarrantyClaimCreateView(generics.CreateAPIView):
    serializer_class = WarrantyClaimCreateSerializer
    permission_classes = [IsAdminUser]

class ManufacturerDashboardStatsAPIView(APIView):
    permission_classes = [IsManufacturer]

    def get(self, request, *args, **kwargs):
        manufacturer = request.user.manufacturer_profile

        total_orders = 0  # Replace with actual logic
        pending_orders = 0  # Replace with actual logic
        completed_orders = 0  # Replace with actual logic
        warranty_claims = WarrantyClaim.objects.filter(warranty__serialized_item__product__manufacturer=manufacturer).count()

        stats = {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'warranty_claims': warranty_claims,
        }

        return Response(stats)

class ManufacturerJobCardListView(generics.ListAPIView):
    serializer_class = JobCardSerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return JobCard.objects.filter(serialized_item__product__manufacturer=self.request.user.manufacturer_profile)

class ManufacturerJobCardDetailView(generics.RetrieveAPIView):
    serializer_class = JobCardDetailSerializer
    permission_classes = [IsManufacturer]
    lookup_field = 'job_card_number'

    def get_queryset(self):
        return JobCard.objects.filter(serialized_item__product__manufacturer=self.request.user.manufacturer_profile)

class ManufacturerWarrantyClaimListView(generics.ListAPIView):
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return WarrantyClaim.objects.filter(warranty__serialized_item__product__manufacturer=self.request.user.manufacturer_profile)

class TechnicianDashboardStatsAPIView(APIView):
    pass

class ManufacturerProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return Product.objects.filter(manufacturer=self.request.user.manufacturer_profile)

class ManufacturerProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return Product.objects.filter(manufacturer=self.request.user.manufacturer_profile)

    def perform_create(self, serializer):
        serializer.save(manufacturer=self.request.user.manufacturer_profile)

class ManufacturerWarrantyClaimDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [IsManufacturer]
    lookup_field = 'claim_id'

    def get_queryset(self):
        return WarrantyClaim.objects.filter(warranty__serialized_item__product__manufacturer=self.request.user.manufacturer_profile)

class ManufacturerWarrantyViewSet(viewsets.ModelViewSet):
    serializer_class = WarrantySerializer
    permission_classes = [IsManufacturer]

    def get_queryset(self):
        return Warranty.objects.filter(manufacturer=self.request.user.manufacturer_profile)

    def perform_create(self, serializer):
        serializer.save(manufacturer=self.request.user.manufacturer_profile)

class ManufacturerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ManufacturerSerializer
    permission_classes = [IsManufacturer]

    def get_object(self):
        return self.request.user.manufacturer_profile
