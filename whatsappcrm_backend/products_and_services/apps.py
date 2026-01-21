from django.apps import AppConfig


class ProductsAndServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products_and_services'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        This ensures signals are connected when Django starts.
        """
        import products_and_services.signals  # noqa: F401
        import products_and_services.solar_automation  # noqa: F401 - Solar package purchase automation
