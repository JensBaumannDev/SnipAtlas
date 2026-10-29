"""Shared permissions for the API."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .authentication import SessionAuthentication


class CsrfProtected(BasePermission):
    """Allow everyone but require a valid CSRF token, also for guests."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check the CSRF token and allow the request if it is valid."""
        SessionAuthentication().enforce_csrf(request)
        return True
