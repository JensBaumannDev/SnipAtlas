from rest_framework import authentication, exceptions
from rest_framework.request import Request


class CsrfFailed(exceptions.PermissionDenied):
    default_detail = 'CSRF check failed.'
    default_code = 'csrf_failed'


class SessionAuthentication(authentication.SessionAuthentication):
    def authenticate_header(self, request: Request) -> str:
        return 'Session'

    def enforce_csrf(self, request: Request) -> None:
        try:
            super().enforce_csrf(request)
        except exceptions.PermissionDenied as error:
            raise CsrfFailed from error
