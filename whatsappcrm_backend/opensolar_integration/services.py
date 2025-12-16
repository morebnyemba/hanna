# whatsappcrm_backend/opensolar_integration/services.py

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from .models import OpenSolarProject, OpenSolarSyncLog
from .api_client import OpenSolarAPIClient
from customer_data.models import InstallationRequest

logger = logging.getLogger(__name__)


class ProjectSyncService:
    """
    Service for syncing installation requests to OpenSolar projects.
    """
    
    def __init__(self):
        self.api_client = OpenSolarAPIClient()
    
    def sync_installation_request(
        self,
        installation_request: InstallationRequest,
        force: bool = False
    ) -> OpenSolarProject:
        """
        Sync installation request to OpenSolar.
        
        Args:
            installation_request: InstallationRequest to sync
            force: Force resync even if already synced
            
        Returns:
            OpenSolarProject instance
        """
        # Get or create OpenSolarProject
        project, created = OpenSolarProject.objects.get_or_create(
            installation_request=installation_request
        )
        
        # Skip if already synced and not forcing
        if not created and project.sync_status == 'synced' and not force:
            logger.info(f"Project {project.id} already synced, skipping")
            return project
        
        # Start sync
        sync_log = OpenSolarSyncLog.objects.create(
            project=project,
            sync_type='create_project' if not project.opensolar_project_id else 'update_project',
            status='started'
        )
        
        start_time = timezone.now()
        
        try:
            # Prepare project data
            project_data = self._prepare_project_data(installation_request)
            
            # Create or update in OpenSolar
            if project.opensolar_project_id:
                response = self.api_client.update_project(
                    project.opensolar_project_id,
                    project_data
                )
            else:
                # First create/get contact
                contact_id = self._sync_contact(installation_request)
                project_data['contact_id'] = contact_id
                
                response = self.api_client.create_project(project_data)
                project.opensolar_project_id = response['id']
                project.opensolar_contact_id = contact_id
            
            # Update project with OpenSolar data
            project.project_name = response.get('name', '')
            project.project_status = response.get('status', '')
            project.system_size_kw = response.get('system_size_kw')
            project.sync_status = 'synced'
            project.last_synced_at = timezone.now()
            project.sync_error_message = ''
            project.sync_retry_count = 0
            project.save()
            
            # Update sync log
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            sync_log.status = 'success'
            sync_log.completed_at = end_time
            sync_log.duration_ms = duration_ms
            sync_log.request_data = project_data
            sync_log.response_data = response
            sync_log.save()
            
            logger.info(f"Successfully synced project {project.id} to OpenSolar")
            
            return project
            
        except Exception as e:
            logger.error(f"Failed to sync project {project.id}: {str(e)}")
            
            # Update project
            project.sync_status = 'sync_failed'
            project.sync_error_message = str(e)
            project.sync_retry_count += 1
            project.save()
            
            # Update sync log
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            raise
    
    def _prepare_project_data(
        self,
        installation_request: InstallationRequest
    ) -> Dict[str, Any]:
        """
        Prepare project data for OpenSolar API.
        """
        customer = installation_request.customer
        
        return {
            'name': f"{customer.first_name} {customer.last_name} - Solar Installation",
            'type': 'residential',  # or 'commercial'
            'status': 'lead',  # Initial status
            'address': {
                'street': installation_request.installation_address or '',
                'city': installation_request.suburb or '',
                'state': '',
                'postal_code': '',
                'country': 'ZW',  # Zimbabwe
            },
            'notes': installation_request.notes or '',
            'custom_fields': {
                'hanna_installation_id': str(installation_request.id),
                'hanna_order_number': installation_request.order_number or '',
                'installation_type': installation_request.installation_type,
            }
        }
    
    def _sync_contact(self, installation_request: InstallationRequest) -> str:
        """
        Create or get contact in OpenSolar.
        
        Returns:
            OpenSolar contact ID
        """
        customer = installation_request.customer
        
        # Try to find existing contact by phone
        existing_contact = self.api_client.find_contact_by_phone(customer.phone_number)
        if existing_contact:
            logger.info(f"Found existing OpenSolar contact: {existing_contact['id']}")
            return existing_contact['id']
        
        # Create new contact
        contact_data = {
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email or '',
            'phone': customer.phone_number,
            'custom_fields': {
                'hanna_customer_id': str(customer.id),
                'source': 'whatsapp_crm',
            }
        }
        
        response = self.api_client.create_contact(contact_data)
        logger.info(f"Created new OpenSolar contact: {response['id']}")
        
        return response['id']
    
    def fetch_project_status(self, project: OpenSolarProject) -> Dict[str, Any]:
        """
        Fetch latest project status from OpenSolar.
        """
        if not project.opensolar_project_id:
            raise ValueError("Project not yet synced to OpenSolar")
        
        response = self.api_client.get_project(project.opensolar_project_id)
        
        # Update project with latest data
        project.project_status = response.get('status', '')
        project.system_size_kw = response.get('system_size_kw')
        project.proposal_url = response.get('proposal_url', '')
        project.last_synced_at = timezone.now()
        project.save()
        
        return response
