from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Warranty, WarrantyClaim
from customer_data.models import JobCard, CustomerProfile

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
