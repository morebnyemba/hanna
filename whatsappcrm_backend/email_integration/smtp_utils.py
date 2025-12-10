"""
Utility functions for SMTP email sending with database configuration support.
"""
import logging
from django.core.mail import get_connection
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)


def get_smtp_connection():
    """
    Get an SMTP email backend connection.
    
    Tries to use database SMTP configuration first, falls back to Django settings.
    
    Returns:
        EmailBackend: Configured SMTP backend for sending emails
    
    Note: For high-volume scenarios, consider implementing caching of the active
    configuration to reduce database queries. Cache would need to be invalidated
    when SMTP configuration is changed.
    """
    from .models import SMTPConfig
    
    # Try to get active SMTP config from database
    # TODO: Consider caching this for high-volume email scenarios
    smtp_config = SMTPConfig.objects.get_active_config()
    
    if smtp_config:
        logger.info(f"Using SMTP config from database: {smtp_config.name}")
        return get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=smtp_config.host,
            port=smtp_config.port,
            username=smtp_config.username,
            password=smtp_config.password,
            use_tls=smtp_config.use_tls,
            use_ssl=smtp_config.use_ssl,
            timeout=smtp_config.timeout,
            fail_silently=False,
        )
    else:
        # Fallback to Django settings
        logger.info("Using SMTP config from Django settings")
        return get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            fail_silently=False,
        )


def get_from_email():
    """
    Get the default 'From' email address.
    
    Tries to use database SMTP configuration first, falls back to Django settings.
    
    Returns:
        str: Email address to use as sender
    """
    from .models import SMTPConfig
    
    smtp_config = SMTPConfig.objects.get_active_config()
    
    if smtp_config:
        return smtp_config.from_email
    else:
        return settings.DEFAULT_FROM_EMAIL
