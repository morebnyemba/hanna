# whatsappcrm_backend/whatsappcrm_backend/views.py
from django.views.generic import TemplateView, RedirectView
from django.conf import settings

class LandingPageView(TemplateView):
    template_name = "landing_page.html"

class AdminRedirectView(RedirectView):
    """
    Redirects Django admin requests to the frontend dashboard.
    This centralizes management to the frontend applications.
    """
    permanent = False
    
    def get_redirect_url(self, *args, **kwargs):
        # Redirect to the frontend dashboard
        # Use environment variable for flexibility across environments
        frontend_url = getattr(settings, 'FRONTEND_DASHBOARD_URL', 'https://dashboard.hanna.co.zw')
        return frontend_url