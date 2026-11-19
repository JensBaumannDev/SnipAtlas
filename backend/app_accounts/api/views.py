"""Views for login, account, favorites, progress and settings."""

from typing import Any

from django.contrib.auth import login, logout, update_session_auth_hash
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from app_accounts.models import Project, User
from app_content.models import Blueprint, BlueprintStep, Entry, RoadmapStep
from core.permissions import CsrfProtected
from core.throttling import AuthRateThrottle, PasswordResetRateThrottle

from .serializers import (
    ActivationResendSerializer,
    ActivationSerializer,
    CurrentPasswordSerializer,
    EmailChangeSerializer,
    EmailConfirmSerializer,
    FavoriteSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    ProjectBlocksSerializer,
    ProjectNoteSerializer,
    ProjectSerializer,
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


class SilentActionView(generics.GenericAPIView):
    """Run an action for guests and always answer without content."""

    permission_classes = (CsrfProtected,)

    def post(self, request: Request) -> Response:
        """Check the body, run the action and answer the same way every time."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(SilentActionView):
    """Register a new user and send the activation link."""

    serializer_class = RegisterSerializer
    throttle_classes = AUTH_THROTTLES


class ActivateView(generics.GenericAPIView):
    """Confirm a new account with the activation link and log the user in."""

    serializer_class = ActivationSerializer
    permission_classes = (CsrfProtected,)
    throttle_classes = AUTH_THROTTLES

    def post(self, request: Request) -> Response:
        """Confirm the email address, log the user in and return their data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data)


class ActivationResendView(SilentActionView):
    """Send a new activation link."""

    serializer_class = ActivationResendSerializer
    throttle_classes = RESET_THROTTLES


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


class EmailConfirmView(SilentActionView):
    """Take over a pending email address with the link sent to it."""

    serializer_class = EmailConfirmSerializer
    throttle_classes = AUTH_THROTTLES


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


class PasswordResetView(SilentActionView):
    """Send a password reset mail."""

    serializer_class = PasswordResetSerializer
    throttle_classes = RESET_THROTTLES


class PasswordResetConfirmView(SilentActionView):
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


# Roadmap project
class ProjectView(generics.GenericAPIView):
    """Read, choose the blocks of, or delete the project of the logged-in user."""

    serializer_class = ProjectSerializer

    def get_object(self) -> Project:
        """Return the project of the logged-in user or raise 404."""
        return get_object_or_404(Project, user=self.request.user)

    def get(self, request: Request) -> Response:
        """Return the project with its progress and notes."""
        return Response(self.get_serializer(self.get_object()).data)

    def put(self, request: Request) -> Response:
        """Create the project or replace its blocks, keeping progress and notes."""
        choice = ProjectBlocksSerializer(data=request.data)
        choice.is_valid(raise_exception=True)
        with transaction.atomic():
            project, created = Project.objects.get_or_create(user=request.user)
            project.set_blocks(choice.validated_data['blocks'])
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(self.get_serializer(project).data, status=code)

    def delete(self, request: Request) -> Response:
        """Delete the project with its progress and notes."""
        Project.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectStepMixin:
    """Mixin for views that work on a roadmap step of the own project."""

    def get_project(self) -> Project:
        """Return the project of the logged-in user or raise 404."""
        return get_object_or_404(Project, user=self.request.user)

    def get_step(self, project: Project, *, in_roadmap: bool) -> RoadmapStep:
        """Return the step from the URL, optionally only if it is in the roadmap."""
        step = get_object_or_404(
            RoadmapStep.objects.select_related('phase'),
            phase__slug=self.kwargs['phase'],
            slug=self.kwargs['step'],
        )
        if in_roadmap and not project.includes(step):
            raise Http404
        return step


class ProjectStepView(ProjectStepMixin, generics.GenericAPIView):
    """Mark a roadmap step of the own project as done or not done."""

    def put(self, request: Request, phase: str, step: str) -> Response:
        """Mark the step as done."""
        project = self.get_project()
        project.completed_steps.get_or_create(step=self.get_step(project, in_roadmap=True))
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, phase: str, step: str) -> Response:
        """Mark the step as not done."""
        project = self.get_project()
        project.completed_steps.filter(step=self.get_step(project, in_roadmap=False)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectNoteView(ProjectStepMixin, generics.GenericAPIView):
    """Write or delete the note on a roadmap step of the own project."""

    serializer_class = ProjectNoteSerializer

    def put(self, request: Request, phase: str, step: str) -> Response:
        """Save the note, replacing an older one."""
        project = self.get_project()
        found = self.get_step(project, in_roadmap=True)
        note = self.get_serializer(data=request.data)
        note.is_valid(raise_exception=True)
        text = note.validated_data['text']
        project.notes.update_or_create(step=found, defaults={'text': text})
        return Response({'text': text})

    def delete(self, request: Request, phase: str, step: str) -> Response:
        """Delete the note."""
        project = self.get_project()
        project.notes.filter(step=self.get_step(project, in_roadmap=False)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
