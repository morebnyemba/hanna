"""
Celery tasks for Solar Integration.
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='solar_integration.sync_all_credentials')
def sync_all_credentials_task():
    """
    Periodic task to sync all active solar API credentials.
    Should be scheduled to run every 5-15 minutes.
    """
    from .services import sync_all_solar_credentials
    
    logger.info("Starting solar credential sync task")
    results = sync_all_solar_credentials()
    
    success_count = sum(1 for r in results if r['success'])
    error_count = len(results) - success_count
    
    logger.info(f"Solar sync complete: {success_count} successful, {error_count} failed")
    return results


@shared_task(name='solar_integration.check_alerts')
def check_alerts_task():
    """
    Periodic task to check for alert conditions.
    Should be scheduled to run every 5 minutes.
    """
    from .services import check_and_create_alerts
    
    logger.info("Starting solar alert check task")
    check_and_create_alerts()
    logger.info("Solar alert check complete")


@shared_task(name='solar_integration.sync_single_credential')
def sync_single_credential_task(credential_id: str):
    """
    Task to sync a single credential.
    
    Args:
        credential_id: UUID of the credential to sync
    """
    from .models import SolarAPICredential
    from .services import SolarServiceFactory
    
    try:
        credential = SolarAPICredential.objects.get(pk=credential_id)
        service = SolarServiceFactory.get_service(credential)
        
        if service:
            success, message = service.sync_all()
            logger.info(f"Sync result for {credential.name}: {message}")
            return {'success': success, 'message': message}
        else:
            logger.warning(f"No service implementation for credential {credential.name}")
            return {'success': False, 'message': 'No service implementation'}
            
    except SolarAPICredential.DoesNotExist:
        logger.error(f"Credential {credential_id} not found")
        return {'success': False, 'message': 'Credential not found'}
    except Exception as e:
        logger.error(f"Error syncing credential {credential_id}: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}


@shared_task(name='solar_integration.aggregate_daily_stats')
def aggregate_daily_stats_task():
    """
    Periodic task to aggregate daily statistics from data points.
    Should be scheduled to run once per day, after midnight.
    """
    from datetime import timedelta
    from decimal import Decimal
    from django.db.models import Avg, Max, Min, Sum
    from .models import DailyEnergyStats, InverterDataPoint, SolarInverter
    
    # Process yesterday's data
    yesterday = (timezone.now() - timedelta(days=1)).date()
    
    logger.info(f"Aggregating daily stats for {yesterday}")
    
    inverters = SolarInverter.objects.filter(is_active=True)
    stats_created = 0
    
    for inverter in inverters:
        # Get data points for yesterday
        data_points = InverterDataPoint.objects.filter(
            inverter=inverter,
            timestamp__date=yesterday
        )
        
        if not data_points.exists():
            continue
        
        # Aggregate statistics
        aggregates = data_points.aggregate(
            peak_power=Max('power_w'),
            avg_power=Avg('power_w'),
            max_energy=Max('energy_kwh'),
        )
        
        # Get the last data point for final energy reading
        last_point = data_points.order_by('-timestamp').first()
        
        # Calculate generation hours (time when power > 100W)
        active_points = data_points.filter(power_w__gt=100).count()
        total_points = data_points.count()
        generation_hours = (active_points / total_points * 24) if total_points > 0 else None
        
        # Create or update daily stats
        stats, created = DailyEnergyStats.objects.update_or_create(
            inverter=inverter,
            date=yesterday,
            defaults={
                'energy_generated_kwh': aggregates['max_energy'] or Decimal('0'),
                'peak_power_w': aggregates['peak_power'],
                'generation_hours': generation_hours,
                # These would need more complex calculation from grid_power direction
                'energy_imported_kwh': Decimal('0'),
                'energy_exported_kwh': Decimal('0'),
            }
        )
        
        if created:
            stats_created += 1
    
    logger.info(f"Created {stats_created} daily stats records for {yesterday}")
    return {'date': str(yesterday), 'stats_created': stats_created}


@shared_task(name='solar_integration.send_alert_notifications')
def send_alert_notifications_task():
    """
    Task to send notifications for new alerts.
    """
    from .models import SolarAlert
    from notifications.services import queue_notifications_to_users
    
    # Get alerts that haven't been notified yet
    unnotified_alerts = SolarAlert.objects.filter(
        is_active=True,
        notification_sent=False
    ).select_related('station', 'inverter')
    
    for alert in unnotified_alerts:
        try:
            # Prepare notification context
            context = {
                'alert_title': alert.title,
                'alert_severity': alert.severity,
                'alert_type': alert.get_alert_type_display(),
                'station_name': alert.station.name if alert.station else 'N/A',
                'inverter_serial': alert.inverter.serial_number if alert.inverter else 'N/A',
                'description': alert.description,
                'occurred_at': alert.occurred_at.isoformat(),
            }
            
            # Queue notification to admin group
            queue_notifications_to_users(
                template_name='solar_alert_notification',
                template_context=context,
                group_names=['Technical Admin', 'Solar Monitoring'],
            )
            
            # Mark as notified
            alert.notification_sent = True
            alert.notification_sent_at = timezone.now()
            alert.save(update_fields=['notification_sent', 'notification_sent_at'])
            
            logger.info(f"Sent notification for solar alert {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to send notification for alert {alert.id}: {e}", exc_info=True)


@shared_task(name='solar_integration.cleanup_old_data_points')
def cleanup_old_data_points_task(days_to_keep: int = 90):
    """
    Periodic task to clean up old time-series data points.
    Keeps aggregated daily stats but removes granular data.
    
    Args:
        days_to_keep: Number of days of granular data to keep (default 90)
    """
    from datetime import timedelta
    from .models import InverterDataPoint
    
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    deleted_count, _ = InverterDataPoint.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old data points older than {days_to_keep} days")
    return {'deleted_count': deleted_count}
