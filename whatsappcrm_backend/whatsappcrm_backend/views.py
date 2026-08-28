# whatsappcrm_backend/whatsappcrm_backend/views.py
import logging

from django.views.generic import TemplateView, RedirectView
from django.conf import settings

logger = logging.getLogger(__name__)

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

def healthz(request):
    """Liveness/readiness probe for the container healthcheck.

    Deliberately minimal: one trivial query to prove the process can still reach
    the database and serve a request from the ASGI thread pool. It takes no
    locks, touches no application tables and does no external I/O, so it cannot
    itself become the slow request it is meant to detect.

    Unauthenticated by design -- it is only reachable inside the compose network
    (nginx does not proxy it) and discloses nothing beyond up/down.
    """
    from django.db import connection
    from django.http import JsonResponse

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.error("Health check failed: database unreachable.", exc_info=True)
        return JsonResponse({'status': 'error', 'database': 'unreachable'}, status=503)

    return JsonResponse({'status': 'ok'})
