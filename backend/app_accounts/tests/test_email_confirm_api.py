from datetime import timedelta

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import User
from app_accounts.tokens import ACTIVATION, EMAIL_CHANGE, make_link_token

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
CSRF_TOKEN = 'a' * 32
URL = reverse('auth-email-confirm')


@pytest.fixture
def pending(user: User) -> User:
    user.pending_email = 'ada.neu@example.com'
    user.save()
    return user


def link_data(user: User, **changes: object) -> dict:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return {'uid': uid, 'token': make_link_token(user, EMAIL_CHANGE)} | changes


def confirm(client: APIClient, data: object) -> Response:
    return client.post(URL, data, format='json')


def stored(user: User) -> tuple[str, str]:
    user.refresh_from_db()
    return user.email, user.pending_email


def assert_invalid_link(response: Response) -> None:
    assert response.status_code == 400
    assert response.json() == {'code': 'invalid_link'}


# Success
def test_confirm_takes_over_pending_email(api_client: APIClient, pending: User) -> None:
    response = confirm(api_client, link_data(pending))
    assert (response.status_code, response.content) == (204, b'')
    assert stored(pending) == ('ada.neu@example.com', '')


def test_confirm_works_without_login(api_client: APIClient, pending: User) -> None:
    confirm(api_client, link_data(pending))
    assert api_client.get(reverse('auth-me')).status_code == 204


def test_confirm_keeps_existing_session(api_client: APIClient, pending: User) -> None:
    data = link_data(pending)
    api_client.force_login(pending)
    confirm(api_client, data)
    assert api_client.get(reverse('auth-me')).json()['email'] == 'ada.neu@example.com'


def test_confirm_keeps_other_devices_logged_in(pending: User) -> None:
    other_device = APIClient()
    other_device.force_login(pending)
    confirm(APIClient(), link_data(pending))
    assert other_device.get(reverse('auth-me')).status_code == 200


def test_login_works_with_new_email_after_confirm(api_client: APIClient, pending: User) -> None:
    confirm(api_client, link_data(pending))
    new = {'email': 'ada.neu@example.com', 'password': PASSWORD}
    old = {'email': 'ada@example.com', 'password': PASSWORD}
    assert api_client.post(reverse('auth-login'), new, format='json').status_code == 200
    assert api_client.post(reverse('auth-login'), old, format='json').status_code == 400


def test_confirm_keeps_password_and_other_data(api_client: APIClient, pending: User) -> None:
    confirm(api_client, link_data(pending))
    pending.refresh_from_db()
    assert pending.check_password(PASSWORD)
    assert (pending.email_confirmed, pending.is_staff, pending.accent) == (True, False, 'blue')


def test_confirm_changes_only_its_user(api_client: APIClient, pending: User) -> None:
    other = User.objects.create_user('grace@example.com', PASSWORD)
    other.pending_email = 'grace.neu@example.com'
    other.save()
    confirm(api_client, link_data(pending))
    assert stored(other) == ('grace@example.com', 'grace.neu@example.com')


def test_confirm_ignores_other_fields(api_client: APIClient, pending: User) -> None:
    confirm(api_client, link_data(pending, email='evil@example.com', pendingEmail='x@y.de'))
    assert stored(pending) == ('ada.neu@example.com', '')


# Invalid link
def test_confirm_link_works_only_once(api_client: APIClient, pending: User) -> None:
    data = link_data(pending)
    confirm(api_client, data)
    assert_invalid_link(confirm(api_client, data))


def test_old_link_fails_after_new_request(api_client: APIClient, pending: User) -> None:
    data = link_data(pending)
    pending.pending_email = 'ada.other@example.com'
    pending.save()
    assert_invalid_link(confirm(api_client, data))
    assert stored(pending) == ('ada@example.com', 'ada.other@example.com')


def test_link_fails_when_address_was_taken_meanwhile(api_client: APIClient, pending: User) -> None:
    data = link_data(pending)
    User.objects.create_user('ADA.NEU@example.com', PASSWORD)
    assert_invalid_link(confirm(api_client, data))
    assert stored(pending) == ('ada@example.com', 'ada.neu@example.com')


def test_link_without_pending_email_fails(api_client: APIClient, user: User) -> None:
    assert_invalid_link(confirm(api_client, link_data(user)))
    assert stored(user) == ('ada@example.com', '')


def test_expired_link_is_rejected(
    api_client: APIClient, pending: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = link_data(pending)
    later = timezone.now() + timedelta(hours=24, minutes=1)
    monkeypatch.setattr('django.core.signing.time.time', later.timestamp)
    assert_invalid_link(confirm(api_client, data))
    assert stored(pending) == ('ada@example.com', 'ada.neu@example.com')


@pytest.mark.parametrize(
    'make_token',
    [
        lambda user: make_link_token(user, ACTIVATION),
        default_token_generator.make_token,
        lambda user: 'broken',
        lambda user: f'0{make_link_token(user, EMAIL_CHANGE)[1:]}',
    ],
)
def test_wrong_token_is_rejected(api_client: APIClient, pending: User, make_token: object) -> None:
    assert_invalid_link(confirm(api_client, link_data(pending, token=make_token(pending))))
    assert stored(pending) == ('ada@example.com', 'ada.neu@example.com')


@pytest.mark.parametrize('uid', ['broken', '!!!', urlsafe_base64_encode(b'abc'), 'OTk5OTk'])
def test_broken_or_unknown_uid_is_rejected(api_client: APIClient, pending: User, uid: str) -> None:
    assert_invalid_link(confirm(api_client, link_data(pending, uid=uid)))


def test_token_of_other_user_is_rejected(api_client: APIClient, pending: User) -> None:
    other = User.objects.create_user('grace@example.com', PASSWORD)
    uid = urlsafe_base64_encode(force_bytes(other.pk))
    assert_invalid_link(confirm(api_client, link_data(pending, uid=uid)))


def test_deactivated_user_cannot_confirm(api_client: APIClient, pending: User) -> None:
    data = link_data(pending)
    User.objects.filter(pk=pending.pk).update(is_active=False)
    assert_invalid_link(confirm(api_client, data))
    assert stored(pending) == ('ada@example.com', 'ada.neu@example.com')


# Invalid fields
@pytest.mark.parametrize('field', ['uid', 'token'])
@pytest.mark.parametrize(('value', 'code'), [('', 'blank'), (None, 'null')])
def test_empty_field_is_rejected(
    api_client: APIClient, pending: User, field: str, value: object, code: str
) -> None:
    response = confirm(api_client, link_data(pending, **{field: value}))
    assert response.json() == {'code': 'validation_error', 'fields': {field: [code]}}


def test_missing_fields_are_listed(api_client: APIClient) -> None:
    assert confirm(api_client, {}).json() == {
        'code': 'validation_error',
        'fields': {'uid': ['required'], 'token': ['required']},
    }


def test_list_body_is_rejected(api_client: APIClient) -> None:
    response = confirm(api_client, ['uid'])
    assert response.json() == {'code': 'validation_error', 'fields': {'nonField': ['invalid']}}


# Security
def test_confirm_without_csrf_token_is_rejected(csrf_client: APIClient, pending: User) -> None:
    response = confirm(csrf_client, link_data(pending))
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert stored(pending) == ('ada@example.com', 'ada.neu@example.com')


def test_confirm_with_csrf_token_is_allowed(csrf_client: APIClient, pending: User) -> None:
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    data = link_data(pending)
    assert (
        csrf_client.post(URL, data, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN).status_code == 204
    )


def test_confirm_with_unknown_session_is_allowed(api_client: APIClient, pending: User) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert confirm(api_client, link_data(pending)).status_code == 204


def test_confirm_is_throttled_with_login(api_client: APIClient, pending: User) -> None:
    login = {'email': 'ada@example.com', 'password': 'Falsches-Passwort-1'}
    for _ in range(5):
        api_client.post(reverse('auth-login'), login, format='json')
    response = confirm(api_client, link_data(pending))
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert stored(pending) == ('ada@example.com', 'ada.neu@example.com')


def test_confirm_throttles_per_ip(api_client: APIClient, pending: User) -> None:
    for _ in range(5):
        confirm(api_client, link_data(pending, token='broken'))
    response = api_client.post(URL, link_data(pending), format='json', REMOTE_ADDR='10.0.0.2')
    assert response.status_code == 204


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_confirm_rejects_other_methods(api_client: APIClient, pending: User, method: str) -> None:
    response = getattr(api_client, method)(URL, link_data(pending), format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert stored(pending) == ('ada@example.com', 'ada.neu@example.com')
