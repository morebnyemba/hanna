# whatsappcrm_backend/opensolar_integration/webhook_handlers.py

import logging
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional
from django.utils import timezone
from .models import OpenSolarWebhookLog, OpenSolarProject

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Process incoming webhooks from OpenSolar.
    """
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate webhook signature.
        """
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> OpenSolarWebhookLog:
        """
        Process incoming webhook from OpenSolar.
        """
        # Extract project ID
        project_id = payload.get('project', {}).get('id')
        
        # Create webhook log
        webhook_log = OpenSolarWebhookLog.objects.create(
            event_type=event_type,
            opensolar_project_id=project_id or '',
            payload=payload,
            headers=headers,
            status='processing'
        )
        
        try:
            # Find associated project
            project = None
            if project_id:
                try:
                    project = OpenSolarProject.objects.get(
                        opensolar_project_id=project_id
                    )
                    webhook_log.project = project
                    webhook_log.save()
                except OpenSolarProject.DoesNotExist:
                    logger.warning(f"No project found for OpenSolar ID: {project_id}")
            
            # Process based on event type
            if event_type == 'project.status_changed':
                self._handle_status_change(project, payload)
            elif event_type == 'project.design_complete':
                self._handle_design_complete(project, payload)
            elif event_type == 'project.proposal_sent':
                self._handle_proposal_sent(project, payload)
            elif event_type == 'project.contract_signed':
                self._handle_contract_signed(project, payload)
            elif event_type == 'project.installation_scheduled':
                self._handle_installation_scheduled(project, payload)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
            
            # Mark as processed
            webhook_log.status = 'processed'
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            
            return webhook_log
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            webhook_log.status = 'failed'
            webhook_log.error_message = str(e)
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            raise
    
    def _handle_status_change(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle project status change."""
        if not project:
            return
        
        new_status = payload.get('project', {}).get('status')
        project.project_status = new_status
        project.save()
        
        # Update installation request status
        installation_request = project.installation_request
        status_map = {
            'lead': 'pending',
            'design': 'pending',
            'proposal': 'pending',
            'contract': 'scheduled',
            'installation': 'in_progress',
            'complete': 'completed',
        }
        
        if new_status in status_map:
            installation_request.status = status_map[new_status]
            installation_request.save()
        
        logger.info(f"Updated project status to: {new_status}")
    
    def _handle_design_complete(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle design completion."""
        if not project:
            return
        
        logger.info(f"Design complete for project {project.id}")
        # Additional notification logic can be added here
    
    def _handle_proposal_sent(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle proposal sent."""
        if not project:
            return
        
        proposal_url = payload.get('project', {}).get('proposal_url', '')
        project.proposal_url = proposal_url
        project.proposal_sent_at = timezone.now()
        project.save()
        
        logger.info(f"Proposal sent for project {project.id}")
    
    def _handle_contract_signed(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle contract signed."""
        if not project:
            return
        
        project.contract_signed_at = timezone.now()
        project.save()
        
        # Update installation request
        installation_request = project.installation_request
        installation_request.status = 'scheduled'
        installation_request.save()
        
        logger.info(f"Contract signed for project {project.id}")
    
    def _handle_installation_scheduled(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle installation scheduled."""
        if not project:
            return
        
        install_date = payload.get('project', {}).get('installation_date')
        if install_date:
            project.installation_scheduled_date = datetime.fromisoformat(install_date).date()
            project.save()
        
        logger.info(f"Installation scheduled for project {project.id}")
