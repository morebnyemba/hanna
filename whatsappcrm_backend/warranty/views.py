from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Count, Q

# Create your views here.
from .models import Warranty, WarrantyClaim
from customer_data.models import JobCard

# --- Custom Permissions ---
class IsManufacturerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'manufacturer_profile')

class IsTechnicianUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'technician_profile')

# --- Dashboard Views ---
class ManufacturerDashboardStatsAPIView(APIView):
    """ Provides dashboard statistics for an authenticated manufacturer user. """
    permission_classes = [IsManufacturerUser]

    def get(self, request, format=None):
        manufacturer = request.user.manufacturer_profile
        claims = WarrantyClaim.objects.filter(warranty__manufacturer=manufacturer)
        data = {
            'manufacturer_name': manufacturer.name,
            'total_claims': claims.count(),
            'pending_claims': claims.filter(status=WarrantyClaim.ClaimStatus.PENDING).count(),
            'approved_claims': claims.filter(status=WarrantyClaim.ClaimStatus.APPROVED).count(),
        }
        return Response(data, status=status.HTTP_200_OK)

class TechnicianDashboardStatsAPIView(APIView):
    """ Provides dashboard statistics for an authenticated technician user. """
    permission_classes = [IsTechnicianUser]

    def get(self, request, format=None):
        technician_user = request.user
        # Assumes a field `assigned_technician` on the JobCard model
        job_cards = JobCard.objects.filter(assigned_technician=technician_user)
        data = {
            'technician_name': technician_user.get_full_name() or technician_user.username,
            'total_assigned_jobs': job_cards.count(),
            'open_jobs': job_cards.filter(status=JobCard.Status.OPEN).count(),
            'in_progress_jobs': job_cards.filter(status=JobCard.Status.IN_PROGRESS).count(),
            'completed_today': job_cards.filter(
                status=JobCard.Status.COMPLETED, 
                # resolution_date__date=timezone.now().date() # Assumes a resolution_date field
            ).count(),
        }
        return Response(data, status=status.HTTP_200_OK)
