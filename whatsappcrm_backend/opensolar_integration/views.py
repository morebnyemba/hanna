# whatsappcrm_backend/opensolar_integration/views.py

import json
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views import View
from .models import OpenSolarProject, OpenSolarWebhookLog
from .serializers import OpenSolarProjectSerializer, OpenSolarWebhookLogSerializer
from .services import ProjectSyncService
from .webhook_handlers import WebhookProcessor

logger = logging.getLogger(__name__)


class OpenSolarProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing OpenSolar projects.
    """
    queryset = OpenSolarProject.objects.all()
    serializer_class = OpenSolarProjectSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Manually sync a project to OpenSolar.
        """
        project = self.get_object()
        service = ProjectSyncService()
        
        try:
            synced_project = service.sync_installation_request(
                project.installation_request,
                force=True
            )
            serializer = self.get_serializer(synced_project)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to sync project: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Fetch latest status from OpenSolar.
        """
        project = self.get_object()
        service = ProjectSyncService()
        
        try:
            status_data = service.fetch_project_status(project)
            return Response(status_data)
        except Exception as e:
            logger.error(f"Failed to fetch status: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class OpenSolarWebhookView(View):
    """
    Receive webhooks from OpenSolar.
    """
    
    def post(self, request):
        """
        Handle incoming webhook.
        """
        try:
            # Parse payload
            payload = json.loads(request.body)
            headers = dict(request.headers)
            
            # Extract event type
            event_type = payload.get('event_type', 'unknown')
            
            # Process webhook
            processor = WebhookProcessor()
            webhook_log = processor.process_webhook(
                event_type=event_type,
                payload=payload,
                headers=headers
            )
            
            return JsonResponse({
                'status': 'received',
                'webhook_log_id': webhook_log.id
            }, status=200)
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)
