# whatsappcrm_backend/installation_systems/branch_views.py
"""
API Views for branch installer allocation and performance metrics.
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
import io

from .branch_models import InstallerAssignment, InstallerAvailability
from .branch_serializers import (
    InstallerAssignmentSerializer,
    InstallerAssignmentCreateSerializer,
    InstallerAvailabilitySerializer,
    InstallerScheduleSerializer,
    AvailableInstallerSerializer,
    InstallerSummarySerializer,
)
from .branch_services import BranchPerformanceMetricsService, InstallerSchedulingService
from .models import InstallationSystemRecord
from warranty.models import Technician
from users.models import RetailerBranch
from users.permissions import IsRetailerOrBranch


class BranchInstallerAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing installer assignments at the branch level.
    Allows branches to assign installers to installations and track progress.
    """
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrBranch]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'installer', 'scheduled_date']
    search_fields = [
        'installation_record__customer__first_name',
        'installation_record__customer__last_name',
        'installation_record__installation_address',
        'installer__user__first_name',
        'installer__user__last_name',
    ]
    ordering_fields = ['scheduled_date', 'created_at', 'status']
    ordering = ['-scheduled_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InstallerAssignmentCreateSerializer
        return InstallerAssignmentSerializer
    
    def get_queryset(self):
        """Filter assignments by branch"""
        user = self.request.user
        
        # Get branch for current user
        branch = None
        if hasattr(user, 'retailer_branch_profile'):
            branch = user.retailer_branch_profile
        elif hasattr(user, 'retailer_profile'):
            # Retailer can see all branches - return empty for now
            # Can be enhanced to show all branch assignments
            return InstallerAssignment.objects.none()
        
        if branch:
            return InstallerAssignment.objects.filter(
                branch=branch
            ).select_related(
                'installer__user',
                'installation_record__customer__contact',
                'assigned_by'
            ).order_by(self.ordering[0])
        
        return InstallerAssignment.objects.none()
    
    def perform_create(self, serializer):
        """Set branch and assigned_by on creation"""
        user = self.request.user
        branch = None
        
        if hasattr(user, 'retailer_branch_profile'):
            branch = user.retailer_branch_profile
        
        serializer.save(
            branch=branch,
            assigned_by=user
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark assignment as started"""
        assignment = self.get_object()
        
        if assignment.status != InstallerAssignment.AssignmentStatus.CONFIRMED:
            return Response(
                {'error': 'Can only start confirmed assignments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignment.status = InstallerAssignment.AssignmentStatus.IN_PROGRESS
        assignment.actual_start_time = timezone.now()
        assignment.save()
        
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark assignment as completed"""
        assignment = self.get_object()
        
        if assignment.status != InstallerAssignment.AssignmentStatus.IN_PROGRESS:
            return Response(
                {'error': 'Can only complete in-progress assignments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional completion data
        completion_notes = request.data.get('completion_notes', '')
        customer_rating = request.data.get('customer_satisfaction_rating')
        customer_feedback = request.data.get('customer_feedback', '')
        
        assignment.status = InstallerAssignment.AssignmentStatus.COMPLETED
        assignment.actual_end_time = timezone.now()
        assignment.completed_at = timezone.now()
        assignment.completion_notes = completion_notes
        assignment.customer_feedback = customer_feedback
        
        if customer_rating:
            assignment.customer_satisfaction_rating = int(customer_rating)
        
        assignment.save()
        
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an assignment"""
        assignment = self.get_object()
        
        if assignment.status == InstallerAssignment.AssignmentStatus.COMPLETED:
            return Response(
                {'error': 'Cannot cancel completed assignments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignment.status = InstallerAssignment.AssignmentStatus.CANCELLED
        assignment.notes = f"{assignment.notes}\n\nCancelled: {request.data.get('reason', 'No reason provided')}"
        assignment.save()
        
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)


class BranchInstallerAvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing installer availability.
    """
    queryset = InstallerAvailability.objects.all()
    serializer_class = InstallerAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrBranch]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['installer', 'date', 'availability_type']
    ordering_fields = ['date', 'start_time']
    ordering = ['-date']
    
    def perform_create(self, serializer):
        """Set created_by on creation"""
        serializer.save(created_by=self.request.user)


class BranchInstallerManagementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and managing installers from branch perspective.
    """
    queryset = Technician.objects.filter(
        technician_type=Technician.TechnicianType.INSTALLER
    )
    serializer_class = InstallerSummarySerializer
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrBranch]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'specialization']
    ordering_fields = ['user__first_name', 'specialization']
    ordering = ['user__first_name']
    
    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Get installer schedule for a date range"""
        installer = self.get_object()
        
        # Parse date range from query params
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if start_date_str:
            start_date = parse_date(start_date_str)
        else:
            start_date = timezone.now().date()
        
        if end_date_str:
            end_date = parse_date(end_date_str)
        else:
            end_date = start_date + timedelta(days=7)
        
        schedule = InstallerSchedulingService.get_installer_schedule(
            installer.id,
            start_date,
            end_date
        )
        
        return Response({
            'installer': InstallerSummarySerializer(installer).data,
            'schedule': schedule,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
        })
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get list of available installers for a specific date"""
        date_str = request.query_params.get('date')
        installation_type = request.query_params.get('installation_type')
        
        if not date_str:
            return Response(
                {'error': 'date parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        date = parse_date(date_str)
        if not date:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get branch for current user
        branch = None
        if hasattr(request.user, 'retailer_branch_profile'):
            branch = request.user.retailer_branch_profile
        
        available = InstallerSchedulingService.get_available_installers(
            date,
            installation_type,
            branch
        )
        
        serializer = AvailableInstallerSerializer(available, many=True)
        return Response(serializer.data)


class BranchPerformanceMetricsViewSet(viewsets.ViewSet):
    """
    ViewSet for branch performance metrics and analytics.
    Provides KPIs, performance data, and export functionality.
    """
    permission_classes = [permissions.IsAuthenticated, IsRetailerOrBranch]
    
    def get_branch(self):
        """Get branch for current user"""
        user = self.request.user
        if hasattr(user, 'retailer_branch_profile'):
            return user.retailer_branch_profile
        return None
    
    def get_date_range(self):
        """Parse date range from query params"""
        start_date_str = self.request.query_params.get('start_date')
        end_date_str = self.request.query_params.get('end_date')
        
        if start_date_str:
            start_date = parse_date(start_date_str)
        else:
            start_date = (timezone.now() - timedelta(days=30)).date()
        
        if end_date_str:
            end_date = parse_date(end_date_str)
        else:
            end_date = timezone.now().date()
        
        return start_date, end_date
    
    def list(self, request):
        """Get overview of all metrics"""
        branch = self.get_branch()
        start_date, end_date = self.get_date_range()
        
        service = BranchPerformanceMetricsService(branch, start_date, end_date)
        metrics = service.get_kpi_summary()
        
        return Response(metrics)
    
    @action(detail=False, methods=['get'])
    def kpis(self, request):
        """Get KPI summary"""
        branch = self.get_branch()
        start_date, end_date = self.get_date_range()
        
        service = BranchPerformanceMetricsService(branch, start_date, end_date)
        
        return Response({
            'installation_metrics': service.get_installation_metrics(),
            'satisfaction_metrics': service.get_customer_satisfaction_metrics(),
            'revenue_metrics': service.get_revenue_metrics(),
        })
    
    @action(detail=False, methods=['get'])
    def installers(self, request):
        """Get installer performance metrics"""
        branch = self.get_branch()
        start_date, end_date = self.get_date_range()
        
        service = BranchPerformanceMetricsService(branch, start_date, end_date)
        performance = service.get_installer_performance()
        
        return Response({
            'installers': performance,
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
            }
        })
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get installation trends"""
        branch = self.get_branch()
        start_date, end_date = self.get_date_range()
        
        service = BranchPerformanceMetricsService(branch, start_date, end_date)
        trend_data = service.get_daily_installation_trend()
        
        return Response({
            'daily_trend': trend_data,
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
            }
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export metrics as CSV"""
        branch = self.get_branch()
        start_date, end_date = self.get_date_range()
        
        service = BranchPerformanceMetricsService(branch, start_date, end_date)
        
        # Get all metrics
        kpi_summary = service.get_kpi_summary()
        installer_performance = service.get_installer_performance()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Branch Performance Metrics Report'])
        writer.writerow([f'Period: {start_date} to {end_date}'])
        writer.writerow([])
        
        # Write KPIs
        writer.writerow(['Key Performance Indicators'])
        writer.writerow(['Metric', 'Value'])
        for key, value in kpi_summary['kpis'].items():
            writer.writerow([key.replace('_', ' ').title(), value])
        writer.writerow([])
        
        # Write performance metrics
        writer.writerow(['Performance Metrics'])
        writer.writerow(['Metric', 'Value'])
        for key, value in kpi_summary['performance'].items():
            writer.writerow([key.replace('_', ' ').title(), value])
        writer.writerow([])
        
        # Write installer performance
        writer.writerow(['Installer Performance'])
        writer.writerow([
            'Installer', 'Total Assignments', 'Completed', 
            'Completion Rate', 'Avg Rating', 'Avg Duration (hrs)'
        ])
        for installer in installer_performance:
            writer.writerow([
                installer['installer_name'],
                installer['total_assignments'],
                installer['completed_assignments'],
                f"{installer['completion_rate']}%",
                installer['average_rating'] or 'N/A',
                installer['average_duration_hours'] or 'N/A',
            ])
        
        # Create response
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="branch_metrics_{start_date}_{end_date}.csv"'
        
        return response
