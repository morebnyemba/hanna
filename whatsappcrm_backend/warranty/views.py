from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
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
