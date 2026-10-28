from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle

from .serializers import RegisterSerializer

AUTH_THROTTLES = (AnonRateThrottle, UserRateThrottle, ScopedRateThrottle)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    throttle_classes = AUTH_THROTTLES
    throttle_scope = 'auth'
