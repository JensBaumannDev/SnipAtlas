import json
import logging

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed, Throttled, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    notify_by_mail = serializers.BooleanField()

    def validate(self, attrs: dict) -> dict:
        raise ValidationError('Passwords differ.', code='mismatch')


def make_view(exc: Exception, permission: type = AllowAny):
    @api_view(['GET'])
    @permission_classes([permission])
    def view(request: Request) -> Response:
        raise exc

    return view


def call(view, method: str = 'get') -> tuple[int, dict]:
    request = getattr(APIRequestFactory(), method)('/api/test/')
    response = view(request)
    response.render()
    return response.status_code, json.loads(response.content)


def validation_error(data: dict) -> ValidationError:
    serializer = SignupSerializer(data=data)
    serializer.is_valid()
    return ValidationError(serializer.errors)


# Validation
def test_validation_error_lists_codes_per_field_in_camel_case() -> None:
    exc = validation_error({'email': 'no-mail'})
    status, body = call(make_view(exc))
    assert status == 400
    assert body == {
        'code': 'validation_error',
        'fields': {'email': ['invalid'], 'notifyByMail': ['required']},
    }


def test_validation_error_without_field_is_listed_under_non_field() -> None:
    exc = validation_error({'email': 'a@b.de', 'notify_by_mail': True})
    status, body = call(make_view(exc))
    assert status == 400
    assert body == {'code': 'validation_error', 'fields': {'nonField': ['mismatch']}}


def test_validation_error_with_plain_message_is_listed_under_non_field() -> None:
    status, body = call(make_view(ValidationError('Wrong.', code='invalid')))
    assert status == 400
    assert body == {'code': 'validation_error', 'fields': {'nonField': ['invalid']}}


# Authentication
def test_guest_returns_not_authenticated() -> None:
    status, body = call(make_view(Exception(), permission=IsAuthenticated))
    assert status == 401
    assert body == {'code': 'not_authenticated'}


def test_failed_authentication_returns_authentication_failed() -> None:
    status, body = call(make_view(AuthenticationFailed()))
    assert status == 401
    assert body == {'code': 'authentication_failed'}


# Not found, permission and method
def test_unknown_object_returns_not_found() -> None:
    status, body = call(make_view(Http404()))
    assert status == 404
    assert body == {'code': 'not_found'}


def test_django_permission_denied_returns_permission_denied() -> None:
    status, body = call(make_view(PermissionDenied()))
    assert status == 403
    assert body == {'code': 'permission_denied'}


def test_wrong_method_returns_method_not_allowed() -> None:
    status, body = call(make_view(Exception()), method='post')
    assert status == 405
    assert body == {'code': 'method_not_allowed'}


# Throttling
def test_throttled_returns_retry_after_in_whole_seconds() -> None:
    status, body = call(make_view(Throttled(wait=59.2)))
    assert status == 429
    assert body == {'code': 'throttled', 'retryAfter': 60}


def test_throttled_without_wait_has_no_retry_after() -> None:
    status, body = call(make_view(Throttled()))
    assert status == 429
    assert body == {'code': 'throttled'}


# Server error
def test_unexpected_error_returns_server_error() -> None:
    status, body = call(make_view(RuntimeError('boom')))
    assert status == 500
    assert body == {'code': 'server_error'}


def test_unexpected_error_is_logged_with_traceback(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        call(make_view(RuntimeError('boom')))
    assert caplog.records[-1].exc_info[0] is RuntimeError
