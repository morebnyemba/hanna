# whatsappcrm_backend/analytics/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Sum, Avg, ExpressionWrapper, F, DurationField
from django.db.models.functions import TruncDate
import re
from collections import Counter
from django.utils.dateparse import parse_date

from customer_data.models import CustomerProfile, Order, JobCard, InstallationRequest, LeadStatus, OrderItem, SiteAssessmentRequest, SolarCleaningRequest, Payment
from conversations.models import Contact
from warranty.models import WarrantyClaim, Technician, Warranty, Manufacturer
from flows.models import ContactFlowState, Flow
from products_and_services.models import Product
from email_integration.models import EmailAttachment

def get_date_range(request):
    """
    Helper function to parse start and end dates from request query params.
    If no dates are provided, returns None, None to signify a 'lifetime' range.
    """
    end_date_str = request.query_params.get('end_date')
    start_date_str = request.query_params.get('start_date')

    if start_date_str and end_date_str:
        start_date = parse_date(start_date_str)
        end_date = parse_date(end_date_str)
        return start_date, end_date
    
    return None, None

class AdminAnalyticsView(APIView):
    """
    Provides comprehensive analytics for the main admin dashboard.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        start_date, end_date = get_date_range(request)
        
        if start_date and end_date:
            date_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
            email_date_filter = Q(saved_at__date__gte=start_date, saved_at__date__lte=end_date)
            started_at_date_filter = Q(started_at__date__gte=start_date, started_at__date__lte=end_date)
        else:
            date_filter = Q()
            email_date_filter = Q()
            started_at_date_filter = Q()

        # --- Customer Analytics ---
        customer_growth = CustomerProfile.objects.filter(date_filter).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('contact_id')).order_by('date')
        
        total_leads = CustomerProfile.objects.filter(date_filter).count()
        won_leads = CustomerProfile.objects.filter(date_filter, lead_status=LeadStatus.WON).count()
        lead_conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

        # --- Sales Analytics ---
        orders = Order.objects.filter(date_filter, stage=Order.Stage.CLOSED_WON)
        revenue_over_time = orders.annotate(date=TruncDate('created_at')).values('date').annotate(total=Sum('amount')).order_by('date')
        total_orders = orders.count()
        total_revenue = orders.aggregate(total=Sum('amount'))['total'] or 0
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0

        top_selling_products = OrderItem.objects.filter(order__in=orders).values('product__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]
        
        # --- Job Card Analytics ---
        job_cards = JobCard.objects.filter(date_filter)
        total_job_cards = job_cards.count()
        job_cards_by_status = job_cards.values('status').annotate(count=Count('status'))

        resolved_job_cards = job_cards.filter(status__in=[JobCard.Status.RESOLVED, JobCard.Status.CLOSED])
        
        average_resolution_time_agg = resolved_job_cards.aggregate(
            avg_time=Avg(ExpressionWrapper(F('updated_at') - F('created_at'), output_field=DurationField()))
        )
        average_resolution_time_days = average_resolution_time_agg['avg_time'].days if average_resolution_time_agg['avg_time'] else 0

        # --- Email Analytics ---
        emails = EmailAttachment.objects.filter(email_date_filter)
        total_incoming_emails = emails.count()
        processed_emails = emails.filter(processed=True).count()
        unprocessed_emails = total_incoming_emails - processed_emails

        # --- AI & Automation Analytics ---
        total_ai_users = ContactFlowState.objects.filter(started_at_date_filter).values('contact').distinct().count()
        
        most_active_flows_query = Flow.objects.all()
        if start_date and end_date:
            most_active_flows_query = most_active_flows_query.filter(contactflowstate__started_at__date__gte=start_date, contactflowstate__started_at__date__lte=end_date)
        
        most_active_flows = most_active_flows_query.annotate(engagement=Count('contactflowstate')).order_by('-engagement')[:5]

        # --- Installation Request Analytics ---
        installation_requests = InstallationRequest.objects.filter(date_filter)
        total_installation_requests = installation_requests.count()
        installation_requests_by_status = installation_requests.values('status').annotate(count=Count('status'))
        installation_requests_by_status_pie = [{'name': item['status'], 'value': item['count']} for item in installation_requests_by_status]

        # --- Technician Analytics ---
        installations_per_technician = InstallationRequest.objects.filter(date_filter, technicians__isnull=False).values('technicians__user__username').annotate(count=Count('id')).order_by('-count')

        # --- Manufacturer Analytics ---
        warranties_per_manufacturer = Warranty.objects.filter(date_filter, manufacturer__isnull=False).values('manufacturer__name').annotate(count=Count('id')).order_by('-count')
        warranty_claims_per_manufacturer = WarrantyClaim.objects.filter(date_filter, warranty__manufacturer__isnull=False).values('warranty__manufacturer__name').annotate(count=Count('id')).order_by('-count')

        job_cards_by_status_pie = [{'name': item['status'], 'value': item['count']} for item in job_cards_by_status]

        # --- Site Assessment Request Analytics ---
        site_assessment_requests = SiteAssessmentRequest.objects.filter(date_filter)
        total_site_assessment_requests = site_assessment_requests.count()
        site_assessment_requests_by_status = site_assessment_requests.values('status').annotate(count=Count('status'))
        site_assessment_requests_by_status_pie = [{'name': item['status'], 'value': item['count']} for item in site_assessment_requests_by_status]

        # --- Solar Cleaning Request Analytics ---
        solar_cleaning_requests = SolarCleaningRequest.objects.filter(date_filter)
        total_solar_cleaning_requests = solar_cleaning_requests.count()
        solar_cleaning_requests_by_status = solar_cleaning_requests.values('status').annotate(count=Count('status'))
        solar_cleaning_requests_by_status_pie = [{'name': item['status'], 'value': item['count']} for item in solar_cleaning_requests_by_status]

        # --- Payment Analytics ---
        payments = Payment.objects.filter(date_filter)
        total_payments = payments.count()
        payments_by_status = payments.values('status').annotate(count=Count('status'))
        payments_by_status_pie = [{'name': item['status'], 'value': item['count']} for item in payments_by_status]
        total_revenue_from_payments = payments.filter(status='successful').aggregate(total=Sum('amount'))['total'] or 0

        data = {
            'customer_analytics': {
                'growth_over_time': list(customer_growth),
                'lead_conversion_rate': f"{lead_conversion_rate:.2f}%",
                'total_customers_in_period': total_leads,
            },
            'sales_analytics': {
                'revenue_over_time': list(revenue_over_time),
                'total_orders': total_orders,
                'average_order_value': f"{average_order_value:.2f}",
                'top_selling_products': list(top_selling_products),
            },
            'job_card_analytics': {
                'total_job_cards': total_job_cards,
                'job_cards_by_status': list(job_cards_by_status),
                'job_cards_by_status_pie': job_cards_by_status_pie,
                'average_resolution_time_days': f"{average_resolution_time_days:.2f}",
            },
            'email_analytics': {
                'total_incoming_emails': total_incoming_emails,
                'processed_emails': processed_emails,
                'unprocessed_emails': unprocessed_emails,
            },
            'installation_request_analytics': {
                'total_installation_requests': total_installation_requests,
                'installation_requests_by_status': list(installation_requests_by_status),
                'installation_requests_by_status_pie': installation_requests_by_status_pie,
            },
            'site_assessment_request_analytics': {
                'total_site_assessment_requests': total_site_assessment_requests,
                'site_assessment_requests_by_status': list(site_assessment_requests_by_status),
                'site_assessment_requests_by_status_pie': site_assessment_requests_by_status_pie,
            },
            'solar_cleaning_request_analytics': {
                'total_solar_cleaning_requests': total_solar_cleaning_requests,
                'solar_cleaning_requests_by_status': list(solar_cleaning_requests_by_status),
                'solar_cleaning_requests_by_status_pie': solar_cleaning_requests_by_status_pie,
            },
            'payment_analytics': {
                'total_payments': total_payments,
                'payments_by_status': list(payments_by_status),
                'payments_by_status_pie': payments_by_status_pie,
                'total_revenue_from_payments': f"{total_revenue_from_payments:.2f}",
            },
            'technician_analytics': {
                'installations_per_technician': list(installations_per_technician),
            },
            'manufacturer_analytics': {
                'warranties_per_manufacturer': list(warranties_per_manufacturer),
                'warranty_claims_per_manufacturer': list(warranty_claims_per_manufacturer),
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
