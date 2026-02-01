"""
Signal handlers for users app.

Handles user account creation and password reset notifications.
"""

import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from notifications.services import queue_notifications_to_users

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def send_portal_access_notification(sender, instance, created, **kwargs):
    """
    Send portal access notification when a new user account is created
    with a customer profile.
    
    Note: This notification should be sent along with a password reset token
    rather than transmitting passwords. The actual password reset link should
    be sent via a separate secure channel (email with token).
    """
    if created:
        # Check if this user has a customer_profile (indicating portal access)
        if hasattr(instance, 'customer_profile'):
            customer_profile = instance.customer_profile
            customer_contact = customer_profile.contact if hasattr(customer_profile, 'contact') else None
            
            if customer_contact:
                # Note: Do not send actual passwords in notifications
                # Instead, trigger a password reset token generation and send via email
                context = {
                    'customer_name': instance.get_full_name() or instance.username,
                    'username': instance.username,
                    'temp_password': 'Please check your email for a secure password reset link',
                }
                
                transaction.on_commit(
                    lambda: queue_notifications_to_users(
                        template_name='pfungwa_portal_access_granted',
                        contact_ids=[customer_contact.id],
                        related_contact=customer_contact,
                        template_context=context
                    )
                )
                logger.info(f"Queued portal access notification for user {instance.id}.")
                
                # TODO: Integrate with Django's password reset system
                # from django.contrib.auth.tokens import default_token_generator
                # from django.core.mail import send_mail
                # token = default_token_generator.make_token(instance)
                # Send password reset email with token

