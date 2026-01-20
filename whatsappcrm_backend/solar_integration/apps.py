from django.apps import AppConfig


class SolarIntegrationConfig(AppConfig):
    name = 'solar_integration'
    verbose_name = 'Solar System Monitoring'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """
        Import signals when the app is ready.
        """
        pass  # Add signal imports here if needed in the future
