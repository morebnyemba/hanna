# whatsappcrm_backend/notifications/utils.py
import logging
from jinja2 import Environment, Undefined
from django.conf import settings

logger = logging.getLogger(__name__)

class SilentUndefined(Undefined):
    """A Jinja2 Undefined class that fails silently by returning an empty string."""
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ''

# Initialize a Jinja2 environment for rendering templates
jinja_env = Environment(undefined=SilentUndefined)

def render_template_string(template_string: str, context: dict) -> str:
    """
    Renders a Jinja2 template string with a given context.

    Args:
        template_string: The string containing Jinja2 template syntax.
        context: A dictionary of variables to be used in rendering.

    Returns:
        The rendered string.
    """
    if not isinstance(template_string, str):
        return str(template_string)
    try:
        template = jinja_env.from_string(template_string)
        return template.render(context)
    except Exception as e:
        logger.error(f"Jinja2 template rendering failed: {e}. Template: '{template_string}'", exc_info=False)
        # Return the original string on error to aid in debugging
        return template_string


def get_versioned_template_name(template_name: str) -> str:
    """
    Returns the template name with the version suffix appended.
    
    This is used when sending template messages to Meta's WhatsApp API to ensure
    the template name matches the versioned name that was synced to Meta.
    
    Args:
        template_name: The base template name (e.g., 'new_order_notification')
    
    Returns:
        The versioned template name (e.g., 'new_order_notification_v1_02')
    
    Example:
        >>> get_versioned_template_name('new_order_notification')
        'new_order_notification_v1_02'
    """
    version_suffix = getattr(settings, 'META_SYNC_VERSION_SUFFIX', 'v1_02')
    return f"{template_name}_{version_suffix}"