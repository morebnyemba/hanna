# whatsappcrm_backend/flows/apps.py

from django.apps import AppConfig

class FlowsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flows'
    verbose_name = "Conversational Flows Management"

    def ready(self):
        # This ensures that your custom flow actions are discovered and registered
        # automatically when the Django application starts.
        # Using a registration function instead of direct import to ensure
        # models are available before registration happens.
        from flows.actions import register_flow_actions
        register_flow_actions()
