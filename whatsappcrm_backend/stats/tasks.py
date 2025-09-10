# stats/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from . import services

logger = logging.getLogger(__name__)

def _broadcast_update(update_type, payload):
    """Helper function to send updates to the dashboard group."""
    channel_layer = get_channel_layer()
    if channel_layer:
        logger.debug(f"Broadcasting update: type='{update_type}'")
        async_to_sync(channel_layer.group_send)(
            'dashboard_updates',
            {
                'type': 'dashboard.update',
                'update_type': update_type,
                'payload': payload
            }
        )
    else:
        logger.warning("Cannot broadcast update: Channel layer not found.")

@shared_task(name="stats.update_dashboard_stats")
def update_dashboard_stats():
    """
    A Celery task to calculate and broadcast all key dashboard statistics.
    This is designed to be 'debounced' by calling it with a countdown.
    """
    logger.info("Running scheduled dashboard stats update task.")
    
    _broadcast_update('stats_update', services.get_stats_card_data())
    _broadcast_update('chart_update_conversation_trends', services.get_conversation_trends_chart_data())
    _broadcast_update('chart_update_bot_performance', services.get_bot_performance_chart_data())

@shared_task(name="stats.broadcast_activity_log")
def broadcast_activity_log(payload):
    """Broadcasts a single activity log entry."""
    _broadcast_update('activity_log_add', payload)

@shared_task(name="stats.broadcast_human_intervention_notification")
def broadcast_human_intervention_notification(payload):
    """Broadcasts a notification for human intervention."""
    _broadcast_update('human_intervention_needed', payload)