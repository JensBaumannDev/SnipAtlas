from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from config.permissions import CsrfProtected
from config.throttling import AuthRateThrottle

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

AUTH_THROTTLES = (AnonRateThrottle, UserRateThrottle, AuthRateThrottle)


class CsrfView(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        get_token(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (CsrfProtected,)
    throttle_classes = AUTH_THROTTLES

    def perform_create(self, serializer: RegisterSerializer) -> None:
        login(self.request, serializer.save())


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (CsrfProtected,)
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(generics.GenericAPIView):
    def post(self, request: Request) -> Response:
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
