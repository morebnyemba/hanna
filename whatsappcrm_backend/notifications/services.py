import logging
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from .models import Notification
from .models import NotificationTemplate # Import the new model
from .tasks import dispatch_notification_task
from conversations.models import Contact
from flows.models import Flow
from .utils import render_template_string # Import the new render utility

logger = logging.getLogger(__name__)
User = get_user_model()

def queue_notifications_to_users(
    message_body: Optional[str] = None,
    template_name: Optional[str] = None,
    template_context: Optional[dict] = None,
    user_ids: Optional[List[int]] = None,
    group_names: Optional[List[str]] = None,
    related_contact: Optional[Contact] = None,
    related_flow: Optional[Flow] = None,
    channel: str = 'whatsapp'
):
    """
    Finds users by ID or group and creates a Notification record for each.
    The message body can be provided directly or rendered from a NotificationTemplate.
    """
    final_message_body = ""
    if template_name:
        try:
            template = NotificationTemplate.objects.get(name=template_name)
            # Build the context for rendering
            render_context = template_context or {}
            if related_contact:
                render_context['contact'] = related_contact
                if hasattr(related_contact, 'customer_profile'):
                    render_context['customer_profile'] = related_contact.customer_profile
            if related_flow:
                render_context['flow'] = related_flow
            
            final_message_body = render_template_string(template.message_body, render_context)
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template '{template_name}' not found. Cannot queue notification.")
            return
    elif message_body:
        final_message_body = message_body

    if not final_message_body or not final_message_body.strip():
        logger.warning("queue_notifications_to_users called but resulted in an empty message body. Skipping.")
        return

    if not user_ids and not group_names:
        logger.warning("queue_notifications_to_users called without user_ids or group_names. No target users.")
        return

    query = Q()
    if user_ids:
        query |= Q(id__in=user_ids)
    if group_names:
        query |= Q(groups__name__in=group_names)

    all_potential_users = User.objects.filter(query, is_active=True).distinct()

    notifications_to_create = [
        Notification(recipient=user, channel=channel, status='pending', content=final_message_body, related_contact=related_contact, related_flow=related_flow)
        for user in all_potential_users
    ]

    created_notifications = Notification.objects.bulk_create(notifications_to_create)
    logger.info(f"Bulk created {len(created_notifications)} notifications for {len(all_potential_users)} potential admin users.")

    for notification in created_notifications:
        transaction.on_commit(lambda n=notification: dispatch_notification_task.delay(n.id))
        logger.info(f"Notifications: Queued Notification ID {notification.id} for user '{notification.recipient.username}'.")