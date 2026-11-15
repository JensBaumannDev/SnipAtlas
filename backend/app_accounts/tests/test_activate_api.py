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
URL = reverse('auth-activate')


def tamper(token: str) -> str:
    return ('1' if token[0] == '0' else '0') + token[1:]


@pytest.fixture
def new_user() -> User:
    return User.objects.create_user('grace@example.com', PASSWORD, email_confirmed=False)


def uid_of(user: User) -> str:
    return urlsafe_base64_encode(force_bytes(user.pk))


def link_data(user: User, **changes: object) -> dict:
    return {'uid': uid_of(user), 'token': make_link_token(user, ACTIVATION)} | changes


def activate(client: APIClient, data: object) -> Response:
    return client.post(URL, data, format='json')


def logged_in_user_id(client: APIClient) -> str | None:
    return client.session.get('_auth_user_id')


def assert_invalid_link(response: Response) -> None:
    assert response.status_code == 400
    assert response.json() == {'code': 'invalid_link'}


# Success
def test_activate_returns_user(api_client: APIClient, new_user: User) -> None:
    response = activate(api_client, link_data(new_user))
    assert response.status_code == 200
    assert response.json() == {
        'email': 'grace@example.com',
        'since': new_user.since.isoformat(),
        'notifyByMail': True,
        'accent': 'blue',
    }


def test_activate_confirms_email(api_client: APIClient, new_user: User) -> None:
    activate(api_client, link_data(new_user))
    new_user.refresh_from_db()
    assert new_user.email_confirmed
    assert new_user.check_password(PASSWORD)


def test_activate_logs_in(api_client: APIClient, new_user: User) -> None:
    response = activate(api_client, link_data(new_user))
    assert logged_in_user_id(api_client) == str(new_user.pk)
    assert response.cookies['sessionid']['httponly']
    assert api_client.get(reverse('auth-me')).json()['email'] == 'grace@example.com'


def test_activate_sets_new_csrf_cookie(api_client: APIClient, new_user: User) -> None:
    api_client.cookies['csrftoken'] = CSRF_TOKEN
    cookie = activate(api_client, link_data(new_user)).cookies['csrftoken']
    assert cookie.value != CSRF_TOKEN
    assert not cookie['httponly']


def test_activate_while_logged_in_switches_user(
    api_client: APIClient, user: User, new_user: User
) -> None:
    api_client.force_login(user)
    activate(api_client, link_data(new_user))
    assert logged_in_user_id(api_client) == str(new_user.pk)


def test_activate_changes_only_its_user(api_client: APIClient, new_user: User) -> None:
    other = User.objects.create_user('lin@example.com', PASSWORD, email_confirmed=False)
    activate(api_client, link_data(new_user))
    other.refresh_from_db()
    assert not other.email_confirmed


def test_activate_ignores_other_fields(api_client: APIClient, new_user: User) -> None:
    data = link_data(new_user, isStaff=True, email='evil@example.com', password='x')
    activate(api_client, data)
    new_user.refresh_from_db()
    assert (new_user.email, new_user.is_staff) == ('grace@example.com', False)
    assert new_user.check_password(PASSWORD)


# Invalid link
def test_activation_link_works_only_once(api_client: APIClient, new_user: User) -> None:
    data = link_data(new_user)
    activate(api_client, data)
    assert_invalid_link(activate(APIClient(), data))


def test_old_link_fails_after_registering_again(api_client: APIClient, new_user: User) -> None:
    data = link_data(new_user)
    new_user.set_password('Andere-Tasse-2026!')
    new_user.save()
    assert_invalid_link(activate(api_client, data))


def test_expired_link_is_rejected(
    api_client: APIClient, new_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = link_data(new_user)
    later = timezone.now() + timedelta(hours=24, minutes=1)
    monkeypatch.setattr('django.core.signing.time.time', later.timestamp)
    assert_invalid_link(activate(api_client, data))
    new_user.refresh_from_db()
    assert not new_user.email_confirmed


@pytest.mark.parametrize(
    'make_token',
    [
        lambda user: make_link_token(user, EMAIL_CHANGE),
        default_token_generator.make_token,
        lambda user: 'broken',
        lambda user: tamper(make_link_token(user, ACTIVATION)),
    ],
)
def test_wrong_token_is_rejected(api_client: APIClient, new_user: User, make_token: object) -> None:
    response = activate(api_client, link_data(new_user, token=make_token(new_user)))
    assert_invalid_link(response)
    assert logged_in_user_id(api_client) is None


def test_token_of_other_user_is_rejected(api_client: APIClient, new_user: User) -> None:
    other = User.objects.create_user('lin@example.com', PASSWORD, email_confirmed=False)
    data = link_data(new_user, uid=uid_of(other))
    assert_invalid_link(activate(api_client, data))
    other.refresh_from_db()
    assert not other.email_confirmed


@pytest.mark.parametrize('uid', ['broken', '!!!', urlsafe_base64_encode(b'abc'), 'OTk5OTk'])
def test_broken_or_unknown_uid_is_rejected(api_client: APIClient, new_user: User, uid: str) -> None:
    assert_invalid_link(activate(api_client, link_data(new_user, uid=uid)))


def test_deactivated_user_cannot_activate(api_client: APIClient, new_user: User) -> None:
    data = link_data(new_user)
    User.objects.filter(pk=new_user.pk).update(is_active=False)
    assert_invalid_link(activate(api_client, data))
    new_user.refresh_from_db()
    assert not new_user.email_confirmed


def test_confirmed_user_cannot_use_activation_link(api_client: APIClient, user: User) -> None:
    assert_invalid_link(activate(api_client, link_data(user)))


# Invalid fields
@pytest.mark.parametrize('field', ['uid', 'token'])
@pytest.mark.parametrize(('value', 'code'), [('', 'blank'), (None, 'null')])
def test_empty_field_is_rejected(
    api_client: APIClient, new_user: User, field: str, value: object, code: str
) -> None:
    response = activate(api_client, link_data(new_user, **{field: value}))
    assert response.json() == {'code': 'validation_error', 'fields': {field: [code]}}


def test_missing_fields_are_listed_before_link_check(api_client: APIClient) -> None:
    response = activate(api_client, {})
    assert response.json() == {
        'code': 'validation_error',
        'fields': {'uid': ['required'], 'token': ['required']},
    }


@pytest.mark.parametrize('value', [['x'], {'a': 1}])
def test_non_text_token_is_rejected(api_client: APIClient, new_user: User, value: object) -> None:
    response = activate(api_client, link_data(new_user, token=value))
    assert response.json() == {'code': 'validation_error', 'fields': {'token': ['invalid']}}


def test_list_body_is_rejected(api_client: APIClient) -> None:
    response = activate(api_client, ['uid'])
    assert response.json() == {'code': 'validation_error', 'fields': {'nonField': ['invalid']}}


def test_broken_json_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(URL, '{"uid":', content_type='application/json')
    assert response.json() == {'code': 'parse_error'}


# Security
def test_activate_without_csrf_token_is_rejected(csrf_client: APIClient, new_user: User) -> None:
    response = activate(csrf_client, link_data(new_user))
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    new_user.refresh_from_db()
    assert not new_user.email_confirmed


def test_activate_with_csrf_token_is_allowed(csrf_client: APIClient, new_user: User) -> None:
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    response = csrf_client.post(
        URL, link_data(new_user), format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN
    )
    assert response.status_code == 200


def test_activate_with_unknown_session_is_allowed(api_client: APIClient, new_user: User) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert activate(api_client, link_data(new_user)).status_code == 200


def test_activate_is_throttled_with_login(api_client: APIClient, new_user: User) -> None:
    login = {'email': 'grace@example.com', 'password': 'Falsches-Passwort-1'}
    for _ in range(5):
        api_client.post(reverse('auth-login'), login, format='json')
    response = activate(api_client, link_data(new_user))
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    new_user.refresh_from_db()
    assert not new_user.email_confirmed


def test_activate_throttles_per_ip(api_client: APIClient, new_user: User) -> None:
    for _ in range(5):
        activate(api_client, link_data(new_user, token='broken'))
    response = api_client.post(URL, link_data(new_user), format='json', REMOTE_ADDR='10.0.0.2')
    assert response.status_code == 200


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_activate_rejects_other_methods(api_client: APIClient, new_user: User, method: str) -> None:
    response = getattr(api_client, method)(URL, link_data(new_user), format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    new_user.refresh_from_db()
    assert not new_user.email_confirmed
