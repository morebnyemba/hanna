from django.apps import AppConfig


class OpensolarIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opensolar_integration'
    verbose_name = 'OpenSolar Integration'

    def ready(self):
        """Import signals when app is ready."""
        import opensolar_integration.signals  # noqa
