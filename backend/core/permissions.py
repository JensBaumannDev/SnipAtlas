from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .authentication import SessionAuthentication


class CsrfProtected(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        SessionAuthentication().enforce_csrf(request)
        return True
