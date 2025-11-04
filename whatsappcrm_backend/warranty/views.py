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

class AdminWarrantyClaimCreateView(generics.CreateAPIView):
    serializer_class = WarrantyClaimCreateSerializer
    permission_classes = [IsAdminUser]


User = get_user_model()
# --- Custom Permissions ---
class IsManufacturerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'manufacturer_profile')

class IsTechnicianUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'technician_profile')

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class IsJobCardManufacturerOwner(permissions.BasePermission):
    """
    Permission to check if the user is the manufacturer associated with the job card.
    A JobCard is linked to a manufacturer via its WarrantyClaim.
    """
    def has_object_permission(self, request, view, obj):
        # The user must be a manufacturer
        if not hasattr(request.user, 'manufacturer_profile'):
            return False
        
        manufacturer_profile = request.user.manufacturer_profile
        
        # The job card must have a warranty claim, which has a warranty, which has a manufacturer that matches
        return obj.warranty_claim and obj.warranty_claim.warranty and obj.warranty_claim.warranty.manufacturer == manufacturer_profile

# --- Dashboard Views ---
class ManufacturerDashboardStatsAPIView(APIView):
    """ Provides dashboard statistics for an authenticated manufacturer user. """
    permission_classes = [IsManufacturerUser]

    def get(self, request, format=None):
        manufacturer = request.user.manufacturer_profile

        # Get all warranty claims related to this manufacturer
        manufacturer_claims = WarrantyClaim.objects.filter(warranty__manufacturer=manufacturer)

        # Get all job cards that are linked to this manufacturer's warranty claims
        manufacturer_job_cards = JobCard.objects.filter(warranty_claim__in=manufacturer_claims)

        # Calculate stats
        total_orders = manufacturer_job_cards.count() # This now correctly represents service orders/jobs for the manufacturer
        pending_orders = manufacturer_job_cards.filter(status__in=[JobCard.Status.OPEN, JobCard.Status.IN_PROGRESS]).count()
        completed_orders = manufacturer_job_cards.filter(status=JobCard.Status.CLOSED).count()
        warranty_claims = manufacturer_claims.count()

        data = {
            'manufacturer_name': manufacturer.name,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'warranty_claims': warranty_claims,
        }
        return Response(data, status=status.HTTP_200_OK)

class ManufacturerJobCardListView(generics.ListAPIView):
    """
    Provides a paginated list of job cards associated with the authenticated manufacturer.
    """
    serializer_class = JobCardSerializer
    permission_classes = [IsManufacturerUser]

    def get_queryset(self):
        manufacturer = self.request.user.manufacturer_profile
        # Find all warranty claims associated with this manufacturer
        manufacturer_claims = WarrantyClaim.objects.filter(warranty__manufacturer=manufacturer)
        # Return all job cards linked to those claims
        return JobCard.objects.filter(warranty_claim__in=manufacturer_claims).select_related('customer', 'customer__contact').order_by('-creation_date')

class ManufacturerJobCardDetailView(generics.RetrieveAPIView):
    """
    Provides details for a single job card associated with the authenticated manufacturer.
    """
    queryset = JobCard.objects.all()
    serializer_class = JobCardDetailSerializer
    permission_classes = [IsManufacturerUser]
    lookup_field = 'job_card_number'
    lookup_url_kwarg = 'job_card_number'

class ManufacturerWarrantyClaimListView(generics.ListAPIView):
    """
    Provides a paginated list of warranty claims associated with the authenticated manufacturer.
    """
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [IsManufacturerUser]

    def get_queryset(self):
        manufacturer = self.request.user.manufacturer_profile
        # Return all warranty claims for this manufacturer, ordered by most recent
        return WarrantyClaim.objects.filter(warranty__manufacturer=manufacturer).select_related('warranty__product', 'warranty__customer').order_by('-created_at')


class TechnicianDashboardStatsAPIView(APIView):
    """ Provides dashboard statistics for an authenticated technician user. """
    permission_classes = [IsTechnicianUser]

    def get(self, request, format=None):
        technician_user = request.user
        job_cards = JobCard.objects.filter(assigned_technician=technician_user)
        data = {
            'technician_name': technician_user.get_full_name() or technician_user.username,
            'total_assigned_jobs': job_cards.count(),
            'open_jobs': job_cards.filter(status=JobCard.Status.OPEN).count(),
            'in_progress_jobs': job_cards.filter(status=JobCard.Status.IN_PROGRESS).count(),
            'completed_today': job_cards.filter(status=JobCard.Status.CLOSED, updated_at__date=timezone.now().date()).count(),
        }
        return Response(data, status=status.HTTP_200_OK)

class AdminWarrantyClaimListView(generics.ListAPIView):
    """
    Provides a paginated list of all warranty claims for admin users.
    """
    serializer_class = WarrantyClaimListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return WarrantyClaim.objects.all().select_related('warranty__serialized_item__product', 'warranty__customer').order_by('-created_at')
