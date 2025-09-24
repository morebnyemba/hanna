from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from customer_data.models import Order, InstallationRequest, SiteAssessmentRequest
from conversations.models import Conversation, Message
from customer_data.models import CustomerProfile

class AnalyticsReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Parse date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        try:
            if start_date:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = timezone.now().date() - timedelta(days=30)
            if end_date:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = timezone.now().date()
        except Exception:
            return Response({'detail': 'Invalid date format.'}, status=400)

        # Example metrics (customize as needed)
        active_conversations_count = Conversation.objects.filter(
            updated_at__gte=timezone.now() - timedelta(hours=4)
        ).count()
        messages_sent = Message.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        new_contacts = CustomerProfile.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        new_orders_today = Order.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        open_orders_value = Order.objects.filter(
            stage='open'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        pending_installations = InstallationRequest.objects.filter(
            status='pending'
        ).count()
        pending_assessments = SiteAssessmentRequest.objects.filter(
            status='pending'
        ).count()

        return Response({
            'active_conversations_count': active_conversations_count,
            'messages_sent': messages_sent,
            'new_contacts': new_contacts,
            'new_orders_today': new_orders_today,
            'open_orders_value': open_orders_value,
            'pending_installations': pending_installations,
            'pending_assessments': pending_assessments,
        })
