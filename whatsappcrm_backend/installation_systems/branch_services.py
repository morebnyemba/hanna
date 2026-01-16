# whatsappcrm_backend/installation_systems/branch_services.py
"""
Business logic for branch installer allocation and performance metrics.
"""

from django.db.models import Q, Count, Avg, Sum, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from collections import defaultdict

from .models import InstallationSystemRecord
from .branch_models import InstallerAssignment, InstallerAvailability
from warranty.models import Technician
from customer_data.models import Order, JobCard


class BranchPerformanceMetricsService:
    """Service for calculating branch performance metrics"""
    
    def __init__(self, branch=None, start_date=None, end_date=None):
        self.branch = branch
        self.start_date = start_date or (timezone.now() - timedelta(days=30)).date()
        self.end_date = end_date or timezone.now().date()
    
    def get_installation_metrics(self):
        """Get installation-related metrics"""
        # Base queryset - filter by branch if provided
        installations = InstallationSystemRecord.objects.all()
        
        if self.branch:
            # Get installations assigned to this branch
            branch_assignments = InstallerAssignment.objects.filter(
                branch=self.branch
            ).values_list('installation_record_id', flat=True)
            installations = installations.filter(id__in=branch_assignments)
        
        # Filter by date range
        date_filter = Q(
            installation_date__gte=self.start_date,
            installation_date__lte=self.end_date
        )
        
        # This month's installations
        current_month_start = timezone.now().replace(day=1).date()
        installations_this_month = installations.filter(
            installation_date__gte=current_month_start
        ).count()
        
        # Pending installations
        pending_installations = installations.filter(
            installation_status__in=[
                InstallationSystemRecord.InstallationStatus.PENDING,
                InstallationSystemRecord.InstallationStatus.IN_PROGRESS
            ]
        ).count()
        
        # Completed installations in period
        completed_installations = installations.filter(
            date_filter,
            installation_status__in=[
                InstallationSystemRecord.InstallationStatus.COMMISSIONED,
                InstallationSystemRecord.InstallationStatus.ACTIVE
            ]
        ).count()
        
        # Total installations in period
        total_installations = installations.filter(date_filter).count()
        
        # Completion rate
        completion_rate = (
            (completed_installations / total_installations * 100)
            if total_installations > 0 else 0
        )
        
        # Average completion time (from installation_date to commissioning_date)
        avg_completion_time = installations.filter(
            date_filter,
            installation_date__isnull=False,
            commissioning_date__isnull=False
        ).annotate(
            completion_days=ExpressionWrapper(
                F('commissioning_date') - F('installation_date'),
                output_field=DurationField()
            )
        ).aggregate(
            avg_days=Avg('completion_days')
        )['avg_days']
        
        avg_completion_days = (
            avg_completion_time.days if avg_completion_time else 0
        )
        
        return {
            'installations_this_month': installations_this_month,
            'pending_installations': pending_installations,
            'completed_installations': completed_installations,
            'total_installations': total_installations,
            'completion_rate': round(completion_rate, 2),
            'average_completion_time_days': avg_completion_days,
        }
    
    def get_customer_satisfaction_metrics(self):
        """Get customer satisfaction metrics from assignments"""
        assignments = InstallerAssignment.objects.filter(
            completed_at__date__gte=self.start_date,
            completed_at__date__lte=self.end_date,
            customer_satisfaction_rating__isnull=False
        )
        
        if self.branch:
            assignments = assignments.filter(branch=self.branch)
        
        avg_rating = assignments.aggregate(
            avg=Avg('customer_satisfaction_rating')
        )['avg'] or 0
        
        total_ratings = assignments.count()
        
        # Count complaints (ratings < 3)
        complaints = assignments.filter(
            customer_satisfaction_rating__lt=3
        ).count()
        
        return {
            'average_satisfaction_rating': round(avg_rating, 2),
            'total_ratings': total_ratings,
            'customer_complaints': complaints,
        }
    
    def get_revenue_metrics(self):
        """Get revenue metrics for branch"""
        # This is a simplified version - adjust based on actual revenue tracking
        installations = InstallationSystemRecord.objects.filter(
            installation_date__gte=self.start_date,
            installation_date__lte=self.end_date,
            order__isnull=False
        )
        
        if self.branch:
            branch_assignments = InstallerAssignment.objects.filter(
                branch=self.branch
            ).values_list('installation_record_id', flat=True)
            installations = installations.filter(id__in=branch_assignments)
        
        total_revenue = installations.aggregate(
            total=Sum('order__amount')
        )['total'] or Decimal('0.00')
        
        return {
            'total_revenue': float(total_revenue),
            'installation_count': installations.count(),
            'average_order_value': (
                float(total_revenue / installations.count())
                if installations.count() > 0 else 0
            )
        }
    
    def get_installer_performance(self):
        """Get performance metrics per installer"""
        assignments = InstallerAssignment.objects.filter(
            scheduled_date__gte=self.start_date,
            scheduled_date__lte=self.end_date
        )
        
        if self.branch:
            assignments = assignments.filter(branch=self.branch)
        
        # Group by installer
        installer_stats = assignments.values(
            'installer__id',
            'installer__user__first_name',
            'installer__user__last_name',
            'installer__user__username'
        ).annotate(
            total_assignments=Count('id'),
            completed=Count('id', filter=Q(status=InstallerAssignment.AssignmentStatus.COMPLETED)),
            avg_rating=Avg('customer_satisfaction_rating'),
            avg_duration=Avg(
                ExpressionWrapper(
                    F('actual_end_time') - F('actual_start_time'),
                    output_field=DurationField()
                )
            )
        ).order_by('-completed')
        
        # Format the results
        results = []
        for stat in installer_stats:
            name = (
                f"{stat['installer__user__first_name']} {stat['installer__user__last_name']}"
                if stat['installer__user__first_name']
                else stat['installer__user__username']
            )
            
            avg_duration_hours = None
            if stat['avg_duration']:
                avg_duration_hours = round(stat['avg_duration'].total_seconds() / 3600, 1)
            
            results.append({
                'installer_id': stat['installer__id'],
                'installer_name': name,
                'total_assignments': stat['total_assignments'],
                'completed_assignments': stat['completed'],
                'completion_rate': round(
                    (stat['completed'] / stat['total_assignments'] * 100)
                    if stat['total_assignments'] > 0 else 0,
                    2
                ),
                'average_rating': round(stat['avg_rating'], 2) if stat['avg_rating'] else None,
                'average_duration_hours': avg_duration_hours,
            })
        
        return results
    
    def get_daily_installation_trend(self):
        """Get daily installation count trend"""
        installations = InstallationSystemRecord.objects.filter(
            installation_date__gte=self.start_date,
            installation_date__lte=self.end_date
        )
        
        if self.branch:
            branch_assignments = InstallerAssignment.objects.filter(
                branch=self.branch
            ).values_list('installation_record_id', flat=True)
            installations = installations.filter(id__in=branch_assignments)
        
        trend_data = installations.annotate(
            date=TruncDate('installation_date')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return [
            {
                'date': item['date'].strftime('%Y-%m-%d'),
                'count': item['count']
            }
            for item in trend_data
        ]
    
    def get_kpi_summary(self):
        """Get all KPIs in one call"""
        installation_metrics = self.get_installation_metrics()
        satisfaction_metrics = self.get_customer_satisfaction_metrics()
        revenue_metrics = self.get_revenue_metrics()
        
        return {
            'kpis': {
                'installations_this_month': installation_metrics['installations_this_month'],
                'pending_installations': installation_metrics['pending_installations'],
                'completed_installations': installation_metrics['completed_installations'],
                'customer_complaints': satisfaction_metrics['customer_complaints'],
            },
            'performance': {
                'completion_rate': installation_metrics['completion_rate'],
                'average_completion_time_days': installation_metrics['average_completion_time_days'],
                'average_satisfaction_rating': satisfaction_metrics['average_satisfaction_rating'],
            },
            'revenue': revenue_metrics,
            'period': {
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': self.end_date.strftime('%Y-%m-%d'),
            }
        }


class InstallerSchedulingService:
    """Service for installer scheduling and availability"""
    
    @staticmethod
    def get_installer_schedule(installer_id, start_date, end_date):
        """Get installer schedule for a date range"""
        assignments = InstallerAssignment.objects.filter(
            installer_id=installer_id,
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date
        ).select_related(
            'installation_record',
            'installation_record__customer',
            'installation_record__customer__contact'
        ).order_by('scheduled_date', 'scheduled_start_time')
        
        availability = InstallerAvailability.objects.filter(
            installer_id=installer_id,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date', 'start_time')
        
        # Group by date
        schedule_by_date = defaultdict(lambda: {
            'assignments': [],
            'availability': [],
            'is_available': True,
            'total_scheduled_hours': Decimal('0.0')
        })
        
        for assignment in assignments:
            date_key = assignment.scheduled_date.strftime('%Y-%m-%d')
            schedule_by_date[date_key]['assignments'].append(assignment)
            
            if assignment.estimated_duration_hours:
                schedule_by_date[date_key]['total_scheduled_hours'] += assignment.estimated_duration_hours
        
        for avail in availability:
            date_key = avail.date.strftime('%Y-%m-%d')
            schedule_by_date[date_key]['availability'].append(avail)
            
            if avail.availability_type != InstallerAvailability.AvailabilityType.AVAILABLE:
                schedule_by_date[date_key]['is_available'] = False
        
        return dict(schedule_by_date)
    
    @staticmethod
    def get_available_installers(date, installation_type=None, branch=None):
        """Find available installers for a specific date"""
        # Get all installers
        installers = Technician.objects.filter(
            technician_type=Technician.TechnicianType.INSTALLER
        )
        
        # Filter by specialization if installation type provided
        if installation_type:
            # Map installation types to specializations
            type_map = {
                'solar': 'Solar',
                'starlink': 'Starlink',
                'hybrid': 'Solar',  # Assuming solar installers can do hybrid
            }
            if installation_type in type_map:
                installers = installers.filter(
                    Q(specialization__icontains=type_map[installation_type]) |
                    Q(specialization='')  # Include installers without specialization
                )
        
        available_list = []
        for installer in installers:
            # Check availability records
            unavailable = InstallerAvailability.objects.filter(
                installer=installer,
                date=date,
                availability_type__in=[
                    InstallerAvailability.AvailabilityType.UNAVAILABLE,
                    InstallerAvailability.AvailabilityType.LEAVE,
                    InstallerAvailability.AvailabilityType.SICK,
                ]
            ).exists()
            
            if unavailable:
                continue
            
            # Check existing assignments
            assignments_count = InstallerAssignment.objects.filter(
                installer=installer,
                scheduled_date=date,
                status__in=[
                    InstallerAssignment.AssignmentStatus.PENDING,
                    InstallerAssignment.AssignmentStatus.CONFIRMED,
                    InstallerAssignment.AssignmentStatus.IN_PROGRESS,
                ]
            ).count()
            
            # Calculate current workload
            current_workload = InstallerAssignment.objects.filter(
                installer=installer,
                status__in=[
                    InstallerAssignment.AssignmentStatus.PENDING,
                    InstallerAssignment.AssignmentStatus.CONFIRMED,
                    InstallerAssignment.AssignmentStatus.IN_PROGRESS,
                ]
            ).count()
            
            available_list.append({
                'installer': installer,
                'assignments_count': assignments_count,
                'current_workload': current_workload,
                'is_available': assignments_count < 2,  # Max 2 assignments per day
            })
        
        return available_list
