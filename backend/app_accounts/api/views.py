from django.contrib.auth import login, logout
from django.db.models import QuerySet
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from app_accounts.models import User
from app_content.models import Entry
from config.permissions import CsrfProtected
from config.throttling import AuthRateThrottle

from .serializers import FavoriteSerializer, LoginSerializer, RegisterSerializer, UserSerializer

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
