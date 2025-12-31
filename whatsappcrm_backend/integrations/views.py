"""
Views for Zoho OAuth integration.
"""
import logging
import secrets
import requests
from typing import Optional
from datetime import timedelta

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.conf import settings

from .models import ZohoCredential

logger = logging.getLogger(__name__)


# Store state tokens temporarily (in production, use Redis or database)
_oauth_states = {}


def generate_oauth_state() -> str:
    """
    Generate a secure random state token for CSRF protection.
    
    Returns:
        str: A secure random token
    """
    return secrets.token_urlsafe(32)


def store_oauth_state(state: str, user_id: Optional[int] = None) -> None:
    """
    Store the OAuth state token temporarily.
    In production, this should use Redis or a database table.
    
    Args:
        state: The state token to store
        user_id: Optional user ID associated with the OAuth flow
    """
    _oauth_states[state] = {
        'created_at': timezone.now(),
        'user_id': user_id
    }
    
    # Clean up old states (older than 10 minutes)
    cutoff_time = timezone.now() - timedelta(minutes=10)
    expired_states = [
        s for s, data in _oauth_states.items()
        if data['created_at'] < cutoff_time
    ]
    for expired in expired_states:
        del _oauth_states[expired]


def verify_oauth_state(state: str) -> bool:
    """
    Verify that the OAuth state token is valid.
    
    Args:
        state: The state token to verify
        
    Returns:
        bool: True if valid, False otherwise
    """
    if state not in _oauth_states:
        return False
    
    # Check if state is not too old (max 10 minutes)
    state_data = _oauth_states[state]
    cutoff_time = timezone.now() - timedelta(minutes=10)
    
    if state_data['created_at'] < cutoff_time:
        del _oauth_states[state]
        return False
    
    # Remove state after verification (one-time use)
    del _oauth_states[state]
    return True


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
        state = generate_oauth_state()
        store_oauth_state(state, request.user.id if request.user.is_authenticated else None)
        
        # Build the redirect URI
        redirect_uri = request.build_absolute_uri('/oauth/callback')
        
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


@csrf_exempt
@require_http_methods(["GET"])
def zoho_oauth_callback(request: HttpRequest) -> HttpResponse:
    """
    Handle the OAuth callback from Zoho.
    
    This endpoint receives the authorization code from Zoho after user authorization,
    validates the state parameter, exchanges the code for tokens, and stores them.
    
    GET /oauth/callback?code=xxx&state=xxx
    
    Query Parameters:
        code: Authorization code from Zoho
        state: State parameter for CSRF validation
        error: Error code if authorization failed
        error_description: Human-readable error description
    """
    # Check for errors from Zoho
    error = request.GET.get('error')
    if error:
        error_description = request.GET.get('error_description', 'Unknown error')
        logger.error(f"Zoho OAuth error: {error} - {error_description}")
        return render(request, 'integrations/oauth_error.html', {
            'error': error,
            'message': error_description
        }, status=400)
    
    # Get code and state from query parameters
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code:
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Missing authorization code',
            'message': 'The authorization code was not provided by Zoho.'
        }, status=400)
    
    if not state:
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Missing state parameter',
            'message': 'The state parameter is required for security validation.'
        }, status=400)
    
    # Verify state parameter for CSRF protection
    if not verify_oauth_state(state):
        logger.warning(f"Invalid or expired OAuth state token: {state}")
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Invalid state parameter',
            'message': 'The state parameter is invalid or has expired. Please try again.'
        }, status=400)
    
    try:
        # Get credentials
        credentials = ZohoCredential.get_instance()
        if not credentials:
            return render(request, 'integrations/oauth_error.html', {
                'error': 'Configuration error',
                'message': 'Zoho credentials not found in database.'
            }, status=500)
        
        # Build redirect URI (must match the one used in authorization request)
        redirect_uri = request.build_absolute_uri('/oauth/callback')
        
        # Exchange authorization code for tokens
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        payload = {
            'code': code,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        logger.info("Exchanging authorization code for tokens...")
        response = requests.post(token_url, data=payload, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        
        # Check for errors in token response
        if 'error' in token_data:
            error_msg = token_data.get('error', 'Unknown error')
            logger.error(f"Token exchange error: {error_msg}")
            return render(request, 'integrations/oauth_error.html', {
                'error': 'Token exchange failed',
                'message': error_msg
            }, status=400)
        
        # Validate required fields
        if 'access_token' not in token_data:
            logger.error(f"Access token not in response: {token_data}")
            return render(request, 'integrations/oauth_error.html', {
                'error': 'Invalid token response',
                'message': 'Access token not received from Zoho.'
            }, status=500)
        
        # Update credentials with tokens
        credentials.access_token = token_data['access_token']
        credentials.refresh_token = token_data.get('refresh_token', credentials.refresh_token)
        
        # Calculate token expiration
        expires_in_seconds = token_data.get('expires_in', 3600)
        credentials.expires_in = timezone.now() + timedelta(seconds=expires_in_seconds)
        
        credentials.save()
        
        logger.info("Successfully obtained and stored Zoho OAuth tokens")
        
        # Return success page with token information (masked)
        return render(request, 'integrations/oauth_success.html', {
            'access_token_preview': credentials.access_token[:20] + '...' if credentials.access_token else None,
            'refresh_token_preview': credentials.refresh_token[:20] + '...' if credentials.refresh_token else None,
            'expires_in': expires_in_seconds,
            'expires_at': credentials.expires_in,
            'scope': credentials.scope
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error during token exchange: {str(e)}")
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Network error',
            'message': f'Failed to communicate with Zoho: {str(e)}'
        }, status=500)
    
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback: {str(e)}")
        return render(request, 'integrations/oauth_error.html', {
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)
