"""
System-level Celery tasks for health monitoring and alerts.
"""
import logging
from celery import shared_task
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
import redis

logger = logging.getLogger(__name__)

# Store last alert state to avoid duplicate notifications
SYSTEM_STATE_KEY = 'system_health_state'


@shared_task(queue='celery')
def check_system_health():
    """
    Monitor critical system services and send alerts when issues are detected.
    Checks: Database, Redis, Celery workers
    
    Should be run frequently via Celery Beat (e.g., every 5 minutes).
    """
    from notifications.services import queue_notifications_to_users
    
    logger.info("Starting system health check")
    
    services_status = {
        'database': False,
        'redis': False,
        'celery': False,
    }
    
    failed_services = []
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        services_status['database'] = True
        logger.info("Database check: OK")
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        failed_services.append('Database')
    
    # Check Redis connection
    try:
        cache.set('health_check', 'ok', timeout=60)
        if cache.get('health_check') == 'ok':
            services_status['redis'] = True
            logger.info("Redis check: OK")
        else:
            failed_services.append('Redis (Cache)')
    except Exception as e:
        logger.error(f"Redis check failed: {str(e)}")
        failed_services.append('Redis')
    
    # Check Celery workers (by checking if this task can run)
    # If we're executing, at least one worker is running
    services_status['celery'] = True
    logger.info("Celery check: OK (task is running)")
    
    # Get previous system state
    previous_state = cache.get(SYSTEM_STATE_KEY, 'online')
    current_state = 'online' if not failed_services else 'offline'
    
    # Detect state change
    if current_state != previous_state:
        # State changed - send notification
        if current_state == 'offline':
            # System just went offline
            context = {
                'failed_services': ', '.join(failed_services),
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            queue_notifications_to_users(
                template_name='pfungwa_system_offline_alert',
                group_names=["System Admins", "Technical Admin"],
                template_context=context
            )
            logger.warning(f"System offline alert sent. Failed services: {failed_services}")
        
        elif current_state == 'online' and previous_state == 'offline':
            # System just came back online
            context = {
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'recovered_services': 'All critical services',
            }
            
            queue_notifications_to_users(
                template_name='pfungwa_system_back_online',
                group_names=["System Admins", "Technical Admin"],
                template_context=context
            )
            logger.info("System back online notification sent.")
        
        # Update state
        cache.set(SYSTEM_STATE_KEY, current_state, timeout=None)
    
    return {
        'success': True,
        'state': current_state,
        'services': services_status,
        'failed_services': failed_services,
        'state_changed': current_state != previous_state
    }
