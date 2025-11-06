from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Warranty, WarrantyClaim
from customer_data.models import JobCard, CustomerProfile
from customer_data.serializers import JobCardSerializer, JobCardDetailSerializer
from .serializers import WarrantyClaimListSerializer, WarrantyClaimCreateSerializer

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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if not hasattr(user, 'manufacturer_profile'):
            return Response({"error": "User is not a manufacturer"}, status=status.HTTP_403_FORBIDDEN)

        manufacturer = user.manufacturer_profile

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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'manufacturer_profile'):
            return JobCard.objects.filter(serialized_item__product__manufacturer=user.manufacturer_profile)
        return JobCard.objects.none()

class ManufacturerJobCardDetailView(generics.RetrieveAPIView):
    serializer_class = JobCardDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'job_card_number'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'manufacturer_profile'):
            return JobCard.objects.filter(serialized_item__product__manufacturer=user.manufacturer_profile)
        return JobCard.objects.none()

class ManufacturerWarrantyClaimListView(generics.ListAPIView):
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'manufacturer_profile'):
            return WarrantyClaim.objects.filter(warranty__serialized_item__product__manufacturer=user.manufacturer_profile)
        return WarrantyClaim.objects.none()

class TechnicianDashboardStatsAPIView(APIView):
    pass
