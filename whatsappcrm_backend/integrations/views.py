"""
Views for Zoho OAuth integration.
"""
import logging
import secrets
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings

from .models import ZohoCredential, OAuthState
from .utils import ZohoClient

logger = logging.getLogger(__name__)

# OAuth redirect URI configuration
# This can be overridden in settings.py by setting ZOHO_OAUTH_REDIRECT_URI
DEFAULT_REDIRECT_PATH = '/oauth/callback'


def get_redirect_uri(request: HttpRequest) -> str:
    """
    Get the OAuth redirect URI for the current request.
    
    Args:
        request: The HTTP request object
        
    Returns:
        str: The full redirect URI
    """
    # Check if a custom redirect URI is configured in settings
    if hasattr(settings, 'ZOHO_OAUTH_REDIRECT_URI'):
        return settings.ZOHO_OAUTH_REDIRECT_URI
    
    # Otherwise, build it dynamically from the request
    return request.build_absolute_uri(DEFAULT_REDIRECT_PATH)


@staff_member_required
@require_http_methods(["GET"])
def zoho_oauth_initiate(request: HttpRequest) -> HttpResponse:
    """
    Initiate the Zoho OAuth flow.
    
    This view generates the authorization URL with a state parameter
    for CSRF protection and redirects the user to Zoho's authorization page.
    
    GET /oauth/zoho/initiate/
    """
    try:
        credentials = ZohoCredential.get_instance()
        if not credentials or not credentials.client_id:
            return render(request, 'integrations/oauth_error.html', {
                'error': 'Zoho credentials not configured',
                'message': 'Please configure Zoho Client ID and Client Secret in the admin panel first.'
            }, status=400)
        
        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in database
        OAuthState.objects.create(
            state=state,
            user_id=request.user.id if request.user.is_authenticated else None
        )
        
        # Cleanup expired states
        OAuthState.cleanup_expired()
        
        # Build the redirect URI
        redirect_uri = get_redirect_uri(request)
        
        # Build Zoho authorization URL
        scope = credentials.scope or "ZohoInventory.items.READ"
        auth_url = (
            f"https://accounts.zoho.com/oauth/v2/auth"
            f"?scope={scope}"
            f"&client_id={credentials.client_id}"
            f"&response_type=code"
            f"&access_type=offline"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
        )
        
        return render(request, 'integrations/oauth_initiate.html', {
            'auth_url': auth_url,
            'redirect_uri': redirect_uri,
            'scope': scope
        })
        
    except Exception as e:
        logger.error(f"Error initiating Zoho OAuth: {str(e)}")
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Failed to initiate OAuth flow',
            'message': str(e)
        }, status=500)


@csrf_exempt  # OAuth callbacks use state parameter for CSRF protection
@require_http_methods(["GET"])
def zoho_oauth_callback(request: HttpRequest) -> HttpResponse:
    """
    Handle the OAuth callback from Zoho.
    
    This endpoint receives the authorization code from Zoho after user authorization,
    validates the state parameter, exchanges the code for tokens using ZohoClient,
    and stores them.
    
    GET /oauth/callback?code=xxx&state=xxx
    
    Query Parameters:
        code: Authorization code from Zoho
        state: State parameter for CSRF validation
        error: Error code if authorization failed
        error_description: Human-readable error description
        
    Note:
        @csrf_exempt is used here because OAuth 2.0 callbacks use the state parameter
        for CSRF protection instead of Django's CSRF token mechanism.
    """
    # Check for errors from Zoho
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', 'Unknown error')
        logger.error(f"Zoho OAuth error: {error} - {error_description}")
        return render(request, 'integrations/oauth_error.html', {
            'error': error,
            'message': error_description,
            'redirect_uri': get_redirect_uri(request)
        }, status=400)
    
    # Get code and state from query parameters
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code:
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Missing authorization code',
            'message': 'The authorization code was not provided by Zoho.',
            'redirect_uri': get_redirect_uri(request)
        }, status=400)
    
    if not state:
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Missing state parameter',
            'message': 'The state parameter is required for security validation.',
            'redirect_uri': get_redirect_uri(request)
        }, status=400)
    
    # Verify state parameter for CSRF protection using database
    try:
        oauth_state = OAuthState.objects.get(state=state)
        
        if not oauth_state.is_valid():
            logger.warning(f"Invalid or expired OAuth state token: {state}")
            return render(request, 'integrations/oauth_error.html', {
                'error': 'Invalid state parameter',
                'message': 'The state parameter is invalid or has expired. Please try again.',
                'redirect_uri': get_redirect_uri(request)
            }, status=400)
        
        # Mark state as used (one-time use)
        oauth_state.mark_as_used()
        
    except OAuthState.DoesNotExist:
        logger.warning(f"OAuth state token not found: {state}")
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Invalid state parameter',
            'message': 'The state parameter was not found. Please try again.',
            'redirect_uri': get_redirect_uri(request)
        }, status=400)
    
    try:
        # Get credentials
        credentials = ZohoCredential.get_instance()
        if not credentials:
            return render(request, 'integrations/oauth_error.html', {
                'error': 'Configuration error',
                'message': 'Zoho credentials not found in database.',
                'redirect_uri': get_redirect_uri(request)
            }, status=500)
        
        # Build redirect URI (must match the one used in authorization request)
        redirect_uri = get_redirect_uri(request)
        
        # Exchange authorization code for tokens using ZohoClient utility
        token_data = ZohoClient.exchange_code_for_tokens(code, redirect_uri)
        
        # Refresh credentials from database (they were updated by exchange_code_for_tokens)
        credentials.refresh_from_db()
        
        logger.info("Successfully obtained and stored Zoho OAuth tokens via callback")
        
        # Return success page with token information (masked)
        return render(request, 'integrations/oauth_success.html', {
            'access_token_preview': credentials.access_token[:20] + '...' if credentials.access_token else None,
            'refresh_token_preview': credentials.refresh_token[:20] + '...' if credentials.refresh_token else None,
            'expires_in': token_data.get('expires_in', 3600),
            'expires_at': credentials.expires_in,
            'scope': credentials.scope
        })
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Token exchange failed',
            'message': str(e),
            'redirect_uri': get_redirect_uri(request)
        }, status=500)
