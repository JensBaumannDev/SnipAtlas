"""Rate limits for sensitive endpoints, counted per IP address."""

from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class IpRateThrottle(SimpleRateThrottle):
    """Rate limit counted per IP address, also for logged-in users."""

    def get_cache_key(self, request: Request, view: APIView) -> str:
        """Return the cache key built from the scope and the IP address."""
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class AuthRateThrottle(IpRateThrottle):
    """Rate limit for login, registration and account changes."""

    scope = 'auth'


class PasswordResetRateThrottle(IpRateThrottle):
    """Rate limit for requesting a password reset mail."""

    scope = 'password_reset'


class RequestRateThrottle(IpRateThrottle):
    """Rate limit for sending requests."""

    scope = 'requests'
