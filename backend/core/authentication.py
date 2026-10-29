"""Session authentication for the API."""

from rest_framework import authentication, exceptions
from rest_framework.request import Request


class CsrfFailed(exceptions.PermissionDenied):
    """Error for a missing or wrong CSRF token with its own error code."""

    default_detail = 'CSRF check failed.'
    default_code = 'csrf_failed'


class SessionAuthentication(authentication.SessionAuthentication):
    """Session login that answers 401 and reports CSRF errors clearly."""

    def authenticate_header(self, request: Request) -> str:
        """Return the header value that turns 403 into 401."""
        return 'Session'

    def enforce_csrf(self, request: Request) -> None:
        """Check the CSRF token and raise CsrfFailed if it fails."""
        try:
            super().enforce_csrf(request)
        except exceptions.PermissionDenied as error:
            raise CsrfFailed from error
