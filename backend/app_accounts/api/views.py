from django.contrib.auth import login
from rest_framework import generics
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from config.permissions import CsrfProtected
from config.throttling import AuthRateThrottle

from .serializers import RegisterSerializer

AUTH_THROTTLES = (AnonRateThrottle, UserRateThrottle, AuthRateThrottle)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (CsrfProtected,)
    throttle_classes = AUTH_THROTTLES

    def perform_create(self, serializer: RegisterSerializer) -> None:
        login(self.request, serializer.save())
