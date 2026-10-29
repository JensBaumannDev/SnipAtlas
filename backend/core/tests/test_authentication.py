import json

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from app_accounts.models import User
from core.permissions import CsrfProtected

pytestmark = pytest.mark.django_db

CSRF_TOKEN = 'a' * 32


def make_view(permission: type):
    @api_view(['GET', 'POST'])
    @permission_classes([permission])
    def view(request: Request) -> Response:
        return Response({'email': getattr(request.user, 'email', '')})

    return view


def call(
    view, user: User | None = None, method: str = 'get', csrf: str | None = None
) -> tuple[int, dict, dict]:
    headers = {'HTTP_X_CSRFTOKEN': csrf} if csrf else {}
    request = getattr(APIRequestFactory(enforce_csrf_checks=True), method)('/api/x/', **headers)
    request.COOKIES['csrftoken'] = CSRF_TOKEN
    request.user = user or AnonymousUser()
    response = view(request)
    response.render()
    return response.status_code, json.loads(response.content), response.headers


# Session
def test_guest_gets_not_authenticated_with_status_401() -> None:
    status, body, headers = call(make_view(IsAuthenticated))
    assert status == 401
    assert body == {'code': 'not_authenticated'}
    assert headers['WWW-Authenticate'] == 'Session'


def test_logged_in_user_is_authenticated(user: User) -> None:
    status, body, _ = call(make_view(IsAuthenticated), user)
    assert (status, body) == (200, {'email': 'ada@example.com'})


def test_inactive_user_is_treated_as_guest(user: User) -> None:
    user.is_active = False
    status, body, _ = call(make_view(IsAuthenticated), user)
    assert (status, body) == (401, {'code': 'not_authenticated'})


# CSRF for logged-in users
def test_logged_in_write_without_csrf_token_is_rejected(user: User) -> None:
    status, body, _ = call(make_view(IsAuthenticated), user, 'post')
    assert (status, body) == (403, {'code': 'csrf_failed'})


def test_logged_in_write_with_wrong_csrf_token_is_rejected(user: User) -> None:
    status, body, _ = call(make_view(IsAuthenticated), user, 'post', csrf='b' * 32)
    assert (status, body) == (403, {'code': 'csrf_failed'})


def test_logged_in_write_with_csrf_token_is_allowed(user: User) -> None:
    status, _, _ = call(make_view(IsAuthenticated), user, 'post', csrf=CSRF_TOKEN)
    assert status == 200


def test_guest_write_needs_no_csrf_token_by_default() -> None:
    status, _, _ = call(make_view(AllowAny), method='post')
    assert status == 200


# CSRF for guests
def test_csrf_protected_rejects_guest_write_without_token() -> None:
    status, body, _ = call(make_view(CsrfProtected), method='post')
    assert (status, body) == (403, {'code': 'csrf_failed'})


def test_csrf_protected_rejects_guest_write_with_wrong_token() -> None:
    status, body, _ = call(make_view(CsrfProtected), method='post', csrf='b' * 32)
    assert (status, body) == (403, {'code': 'csrf_failed'})


def test_csrf_protected_allows_guest_write_with_token() -> None:
    status, _, _ = call(make_view(CsrfProtected), method='post', csrf=CSRF_TOKEN)
    assert status == 200


def test_csrf_protected_allows_reading_without_token() -> None:
    status, _, _ = call(make_view(CsrfProtected))
    assert status == 200
