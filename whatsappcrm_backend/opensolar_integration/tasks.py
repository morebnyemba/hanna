# whatsappcrm_backend/opensolar_integration/tasks.py

import logging
from celery import shared_task
from django.utils import timezone
from .models import OpenSolarProject
from .services import ProjectSyncService
from customer_data.models import InstallationRequest

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # Retry after 1 minute
)
def sync_installation_to_opensolar(self, installation_request_id):
    """
    Async task to sync installation request to OpenSolar.
    """
    try:
        installation_request = InstallationRequest.objects.get(
            id=installation_request_id
        )
        
        service = ProjectSyncService()
        project = service.sync_installation_request(installation_request)
        
        logger.info(
            f"Successfully synced installation request {installation_request_id} "
            f"to OpenSolar project {project.opensolar_project_id}"
        )
        
        return {
            'status': 'success',
            'installation_request_id': installation_request_id,
            'opensolar_project_id': project.opensolar_project_id
        }
        
    except InstallationRequest.DoesNotExist:
        logger.error(f"Installation request {installation_request_id} not found")
        return {
            'status': 'error',
            'error': 'Installation request not found'
        }
        
    except Exception as e:
        logger.error(
            f"Failed to sync installation request {installation_request_id}: {str(e)}"
        )
        # Retry the task
        raise self.retry(exc=e)


@shared_task
def fetch_opensolar_project_updates():
    """
    Periodic task to fetch updates from OpenSolar for active projects.
    """
    service = ProjectSyncService()
    
    # Get projects that haven't been synced in the last 24 hours
    from datetime import timedelta
    cutoff_time = timezone.now() - timedelta(hours=24)
    
    projects = OpenSolarProject.objects.filter(
        sync_status='synced',
        installation_request__status__in=['pending', 'scheduled', 'in_progress']
    ).filter(
        models.Q(last_synced_at__lt=cutoff_time) | models.Q(last_synced_at__isnull=True)
    )[:50]  # Limit to 50 projects per run
    
    updated_count = 0
    for project in projects:
        try:
            service.fetch_project_status(project)
            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to fetch status for project {project.id}: {str(e)}")
    
    logger.info(f"Updated {updated_count} OpenSolar projects")
    return {'updated_count': updated_count}


@shared_task
def retry_failed_syncs():
    """
    Retry failed sync operations.
    """
    from django.db import models
    
    # Get projects with failed sync that haven't exceeded retry limit
    failed_projects = OpenSolarProject.objects.filter(
        sync_status='sync_failed',
        sync_retry_count__lt=3
    )[:10]  # Limit to 10 retries per run
    
    service = ProjectSyncService()
    retry_count = 0
    
    for project in failed_projects:
        try:
            service.sync_installation_request(
                project.installation_request,
                force=True
            )
            retry_count += 1
            logger.info(f"Successfully retried sync for project {project.id}")
        except Exception as e:
            logger.error(f"Retry failed for project {project.id}: {str(e)}")
    
    logger.info(f"Retried {retry_count} failed syncs")
    return {'retry_count': retry_count}
