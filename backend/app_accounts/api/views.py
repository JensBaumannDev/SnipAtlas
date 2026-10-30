"""Views for login, account, favorites, progress and settings."""

from typing import Any

from django.contrib.auth import login, logout, update_session_auth_hash
from django.db.models import QuerySet
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from app_accounts.models import User
from app_content.models import Blueprint, BlueprintStep, Entry
from core.permissions import CsrfProtected
from core.throttling import AuthRateThrottle, PasswordResetRateThrottle

from .serializers import (
    CurrentPasswordSerializer,
    EmailChangeSerializer,
    FavoriteSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    SettingsSerializer,
    UserSerializer,
)

AUTH_THROTTLES = (AnonRateThrottle, UserRateThrottle, AuthRateThrottle)
RESET_THROTTLES = (AnonRateThrottle, UserRateThrottle, PasswordResetRateThrottle)


class CsrfView(generics.GenericAPIView):
    """Set the CSRF cookie."""

    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        """Set the CSRF cookie and answer without content."""
        get_token(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(generics.CreateAPIView):
    """Register a new user and log them in."""

    serializer_class = RegisterSerializer
    permission_classes = (CsrfProtected,)
    throttle_classes = AUTH_THROTTLES

    def perform_create(self, serializer: RegisterSerializer) -> None:
        """Create the user and log them in."""
        login(self.request, serializer.save())


class LoginView(generics.GenericAPIView):
    """Log a user in with email and password."""

    serializer_class = LoginSerializer
    permission_classes = (CsrfProtected,)
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        """Log the user in and return their data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(generics.GenericAPIView):
    """Log the current user out."""

    def post(self, request: Request) -> Response:
        """End the session."""
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """Read and change the data of the logged-in user."""

    serializer_class = UserSerializer
    http_method_names = ('get', 'patch', 'head', 'options')

    def get_permissions(self) -> list[BasePermission]:
        """Allow the session check to report an anonymous state without an error."""
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Return no content when there is no signed-in user."""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return super().retrieve(request, *args, **kwargs)

    def get_object(self) -> User:
        """Return the logged-in user."""
        return self.request.user


# Account
class EmailView(generics.GenericAPIView):
    """Change the email address of the logged-in user."""

    serializer_class = EmailChangeSerializer
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        """Save the new email address and return the user."""
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordView(generics.GenericAPIView):
    """Change the password of the logged-in user."""

    serializer_class = PasswordChangeSerializer
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        """Save the new password and keep the user logged in."""
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        update_session_auth_hash(request, serializer.save())
        return Response(serializer.data)


class DeleteAccountView(generics.GenericAPIView):
    """Delete the account of the logged-in user."""

    serializer_class = CurrentPasswordSerializer
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        """Check the password, log the user out and delete the account."""
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        logout(request)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetView(generics.GenericAPIView):
    """Send a password reset mail."""

    serializer_class = PasswordResetSerializer
    permission_classes = (CsrfProtected,)
    throttle_classes = RESET_THROTTLES

    def post(self, request: Request) -> Response:
        """Send the mail and always answer the same way."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetConfirmView(PasswordResetView):
    """Set a new password from a password reset link."""

    serializer_class = PasswordResetConfirmSerializer
    throttle_classes = AUTH_THROTTLES


# Favorites
class FavoriteListView(generics.ListAPIView):
    """List the favorites of the logged-in user."""

    serializer_class = FavoriteSerializer

    def get_queryset(self) -> QuerySet:
        """Return the favorites of the logged-in user."""
        return self.request.user.favorites.select_related('entry__subtopic__topic')


class FavoriteView(generics.GenericAPIView):
    """Add or remove a single favorite."""

    def get_entry(self) -> Entry:
        """Return the command from the URL or raise 404."""
        return get_object_or_404(Entry, slug=self.kwargs['entry'])

    def put(self, request: Request, entry: str) -> Response:
        """Add the command to the favorites."""
        request.user.favorites.get_or_create(entry=self.get_entry())
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, entry: str) -> Response:
        """Remove the command from the favorites."""
        request.user.favorites.filter(entry=self.get_entry()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Progress
class ProgressListView(generics.GenericAPIView):
    """List the completed blueprint steps of the logged-in user."""

    def get(self, request: Request) -> Response:
        """Return the completed step slugs grouped by blueprint."""
        return Response(request.user.progress())


class ProgressBlueprintView(generics.GenericAPIView):
    """Reset the progress of a single blueprint."""

    def delete(self, request: Request, blueprint: str) -> Response:
        """Remove all completed steps of the blueprint."""
        found = get_object_or_404(Blueprint, slug=blueprint)
        request.user.completed_steps.filter(step__blueprint=found).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProgressStepView(generics.GenericAPIView):
    """Mark a single blueprint step as done or not done."""

    def get_step(self) -> BlueprintStep:
        """Return the step from the URL or raise 404."""
        return get_object_or_404(
            BlueprintStep, blueprint__slug=self.kwargs['blueprint'], slug=self.kwargs['step']
        )

    def put(self, request: Request, blueprint: str, step: str) -> Response:
        """Mark the step as done."""
        request.user.completed_steps.get_or_create(step=self.get_step())
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, blueprint: str, step: str) -> Response:
        """Mark the step as not done."""
        request.user.completed_steps.filter(step=self.get_step()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Settings
class SettingsView(generics.RetrieveUpdateAPIView):
    """Read and change the settings of the logged-in user."""

    serializer_class = SettingsSerializer
    http_method_names = ('get', 'patch', 'head', 'options')

    def get_object(self) -> User:
        """Return the logged-in user."""
        return self.request.user
