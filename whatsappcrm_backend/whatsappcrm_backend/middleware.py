# whatsappcrm_backend/whatsappcrm_backend/middleware.py

import logging
import time

from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.db import close_old_connections, connection
from django.conf import settings

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_key):
    """
    Asynchronously gets a user from a JWT token.
    """
    try:
        # This will validate the token's signature and expiration
        UntypedToken(token_key)
    except (InvalidToken, TokenError):
        return AnonymousUser()

    from rest_framework_simplejwt.settings import api_settings
    try:
        token = UntypedToken(token_key)
        user_id = token.get(api_settings.USER_ID_CLAIM)
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for Django Channels that authenticates users using a JWT token
    passed in the query string.
    """
    async def __call__(self, scope, receive, send):
        close_old_connections()

        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            # If no token is provided, default to an anonymous user.
            # The consumer will handle the rejection.
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)


# --- Query Performance Monitoring Middleware ---

query_logger = logging.getLogger('django.db.performance')


class QueryPerformanceMiddleware:
    """
    Middleware that logs slow database queries for performance monitoring.
    Configurable via SLOW_QUERY_THRESHOLD_MS environment variable (default: 200ms).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_query_threshold_ms = float(
            getattr(settings, 'SLOW_QUERY_THRESHOLD_MS', 200)
        )

    def __call__(self, request):
        start_time = time.monotonic()
        response = self.get_response(request)
        total_time = (time.monotonic() - start_time) * 1000  # Convert to ms

        if settings.DEBUG:
            queries = connection.queries
            total_queries = len(queries)

            if total_queries > 0:
                slow_queries = []
                total_db_time = 0.0

                for query in queries:
                    query_time_ms = float(query.get('time', 0)) * 1000
                    total_db_time += query_time_ms

                    if query_time_ms >= self.slow_query_threshold_ms:
                        slow_queries.append({
                            'sql': query['sql'][:500],
                            'time_ms': round(query_time_ms, 2),
                        })

                if slow_queries:
                    query_logger.warning(
                        "Slow queries detected on %s %s: %d slow query(ies), "
                        "total DB time: %.2fms, request time: %.2fms",
                        request.method,
                        request.path,
                        len(slow_queries),
                        total_db_time,
                        total_time,
                        extra={'slow_queries': slow_queries},
                    )

                # Log high query count requests (N+1 detection)
                query_count_threshold = int(
                    getattr(settings, 'QUERY_COUNT_THRESHOLD', 50)
                )
                if total_queries >= query_count_threshold:
                    query_logger.warning(
                        "High query count on %s %s: %d queries, "
                        "total DB time: %.2fms",
                        request.method,
                        request.path,
                        total_queries,
                        total_db_time,
                    )

        return response