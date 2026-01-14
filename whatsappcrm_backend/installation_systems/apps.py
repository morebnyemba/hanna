from django.apps import AppConfig


class InstallationSystemsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'installation_systems'
    verbose_name = 'Installation Systems'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import installation_systems.signals  # noqa: F401
