from django.contrib.auth import login, logout, update_session_auth_hash
from django.db.models import QuerySet
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from app_accounts.models import User
from app_content.models import Blueprint, BlueprintStep, Entry
from config.permissions import CsrfProtected
from config.throttling import AuthRateThrottle

from .serializers import (
    CurrentPasswordSerializer,
    EmailChangeSerializer,
    FavoriteSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    RegisterSerializer,
    SettingsSerializer,
    UserSerializer,
)

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


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    http_method_names = ('get', 'patch', 'head', 'options')

    def get_object(self) -> User:
        return self.request.user


# Account
class EmailView(generics.GenericAPIView):
    serializer_class = EmailChangeSerializer
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        update_session_auth_hash(request, serializer.save())
        return Response(serializer.data)


class DeleteAccountView(generics.GenericAPIView):
    serializer_class = CurrentPasswordSerializer
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        logout(request)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Favorites
class FavoriteListView(generics.ListAPIView):
    serializer_class = FavoriteSerializer

    def get_queryset(self) -> QuerySet:
        return self.request.user.favorites.select_related('entry__subtopic__topic')


class FavoriteView(generics.GenericAPIView):
    def get_entry(self) -> Entry:
        return get_object_or_404(Entry, slug=self.kwargs['entry'])

    def put(self, request: Request, entry: str) -> Response:
        request.user.favorites.get_or_create(entry=self.get_entry())
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, entry: str) -> Response:
        request.user.favorites.filter(entry=self.get_entry()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Progress
class ProgressListView(generics.GenericAPIView):
    def get(self, request: Request) -> Response:
        return Response(request.user.progress())


class ProgressBlueprintView(generics.GenericAPIView):
    def delete(self, request: Request, blueprint: str) -> Response:
        found = get_object_or_404(Blueprint, slug=blueprint)
        request.user.completed_steps.filter(step__blueprint=found).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProgressStepView(generics.GenericAPIView):
    def get_step(self) -> BlueprintStep:
        return get_object_or_404(
            BlueprintStep, blueprint__slug=self.kwargs['blueprint'], slug=self.kwargs['step']
        )

    def put(self, request: Request, blueprint: str, step: str) -> Response:
        request.user.completed_steps.get_or_create(step=self.get_step())
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, blueprint: str, step: str) -> Response:
        request.user.completed_steps.filter(step=self.get_step()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Settings
class SettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = SettingsSerializer
    http_method_names = ('get', 'patch', 'head', 'options')

    def get_object(self) -> User:
        return self.request.user
