# whatsappcrm_backend/meta_integration/apps.py

from django.apps import AppConfig

class MetaIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meta_integration'
    verbose_name = "Meta Integration"

    def ready(self):
        # Import signals to ensure they are connected
        import meta_integration.signals
