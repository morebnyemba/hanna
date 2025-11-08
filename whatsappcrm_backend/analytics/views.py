# whatsappcrm_backend/analytics/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Sum, Avg
from django.db.models.functions import TruncDate
import re
from collections import Counter
from django.utils.dateparse import parse_date

from customer_data.models import CustomerProfile, Order, JobCard, InstallationRequest, LeadStatus
from conversations.models import Contact
from warranty.models import WarrantyClaim, Technician
from flows.models import ContactFlowState, Flow

def get_date_range(request):
    """
    Helper function to parse start and end dates from request query params.
    Defaults to the last 30 days.
    """
    end_date_str = request.query_params.get('end_date')
    start_date_str = request.query_params.get('start_date')

    if end_date_str:
        end_date = parse_date(end_date_str)
    else:
        end_date = timezone.now().date()

    if start_date_str:
        start_date = parse_date(start_date_str)
    else:
        start_date = end_date - timedelta(days=30)
    
    return start_date, end_date

class AdminAnalyticsView(APIView):
    """
    Provides comprehensive analytics for the main admin dashboard.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        start_date, end_date = get_date_range(request)
        date_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)

        # --- Customer Analytics ---
        customer_growth = CustomerProfile.objects.filter(date_filter).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
        
        total_leads = CustomerProfile.objects.filter(date_filter).count()
        won_leads = CustomerProfile.objects.filter(date_filter, lead_status=LeadStatus.WON).count()
        lead_conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

        # --- Sales Analytics ---
        revenue_over_time = Order.objects.filter(date_filter, stage=Order.Stage.CLOSED_WON).annotate(date=TruncDate('created_at')).values('date').annotate(total=Sum('amount')).order_by('date')
        
        # --- AI & Automation Analytics ---
        total_ai_users = ContactFlowState.objects.filter(started_at__date__gte=start_date, started_at__date__lte=end_date).values('contact').distinct().count()
        most_active_flows = Flow.objects.filter(contact_states__started_at__date__gte=start_date, contact_states__started_at__date__lte=end_date).annotate(engagement=Count('contact_states')).order_by('-engagement')[:5]

        data = {
            'customer_analytics': {
                'growth_over_time': list(customer_growth),
                'lead_conversion_rate': f"{lead_conversion_rate:.2f}%",
                'total_customers_in_period': total_leads,
            },
            'sales_analytics': {
                'revenue_over_time': list(revenue_over_time),
            },
            'automation_analytics': {
                'total_ai_users_in_period': total_ai_users,
                'most_active_flows': [{'name': flow.name, 'engagements': flow.engagement} for flow in most_active_flows],
            }
        }
        return Response(data)

class ManufacturerAnalyticsView(APIView):
    """
    Provides targeted analytics for the manufacturer dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date, end_date = get_date_range(request)
        date_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)

        # --- Warranty & Repair Metrics ---
        total_warranty_repairs = JobCard.objects.filter(
            date_filter,
            is_under_warranty=True,
            status__in=[JobCard.Status.RESOLVED, JobCard.Status.CLOSED]
        ).count()

        items_pending_collection = JobCard.objects.filter(status=JobCard.Status.RESOLVED).count() # This is likely a current state, not historical
        
        items_replaced = WarrantyClaim.objects.filter(date_filter, status=WarrantyClaim.ClaimStatus.REPLACED).count()

        # --- Fault Analysis ---
        overloaded_inverters = JobCard.objects.filter(date_filter, reported_fault__icontains='overload').count()

        # AI Insight: Common Fault Keywords
        all_faults = JobCard.objects.filter(date_filter).exclude(reported_fault__isnull=True).exclude(reported_fault__exact='').values_list('reported_fault', flat=True)
        words = re.findall(r'\b\w+\b', ' '.join(all_faults).lower())
        stopwords = set(['the', 'a', 'an', 'is', 'not', 'and', 'or', 'but', 'to', 'of', 'in', 'for', 'on', 'with', 'it', 'no', 'fault', 'power', 'unit'])
        meaningful_words = [word for word in words if word not in stopwords and not word.isdigit()]
        common_faults = [item[0] for item in Counter(meaningful_words).most_common(5)]

        data = {
            'warranty_metrics': {
                'total_warranty_repairs': total_warranty_repairs,
                'items_pending_collection': items_pending_collection,
                'items_replaced': items_replaced,
            },
            'fault_analytics': {
                'overloaded_inverters': overloaded_inverters,
                'ai_insight_common_faults': common_faults,
            }
        }
        return Response(data)

class TechnicianAnalyticsView(APIView):
    """
    Provides personalized analytics for technicians and installers.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date, end_date = get_date_range(request)
        date_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
        
        technician = request.user.technician_profile

        # --- Job Card (Repair) Metrics ---
        my_job_cards = JobCard.objects.filter(technician=technician)
        my_open_job_cards = my_job_cards.filter(status__in=[JobCard.Status.OPEN, JobCard.Status.IN_PROGRESS]).count()
        
        my_completed_jobs_in_period = my_job_cards.filter(
            date_filter,
            status__in=[JobCard.Status.RESOLVED, JobCard.Status.CLOSED]
        ).count()

        # --- Installation Metrics ---
        my_installations = InstallationRequest.objects.filter(technicians=technician)
        my_total_installations_in_period = my_installations.filter(date_filter, status='completed').count()
        my_pending_installations = my_installations.filter(status__in=['pending', 'scheduled']).count()

        data = {
            'repair_metrics': {
                'my_open_job_cards': my_open_job_cards,
                'my_completed_jobs_in_period': my_completed_jobs_in_period,
            },
            'installation_metrics': {
                'my_total_installations_in_period': my_total_installations_in_period,
                'my_pending_installations': my_pending_installations,
            }
        }
        return Response(data)
