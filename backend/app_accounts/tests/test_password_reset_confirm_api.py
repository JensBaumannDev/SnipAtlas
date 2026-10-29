from datetime import datetime, timedelta

import pytest
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
NEW_PASSWORD = 'Tee-Kanne-2027?'
CSRF_TOKEN = 'a' * 32
URL = reverse('auth-password-reset-confirm')
ME_URL = reverse('auth-me')


def encode(value: object) -> str:
    return urlsafe_base64_encode(force_bytes(value))


def link_data(user: User) -> dict:
    return {'uid': encode(user.pk), 'token': default_token_generator.make_token(user)}


def confirm(client: APIClient, user: User, **changes: object) -> Response:
    data = link_data(user) | {'password': NEW_PASSWORD} | changes
    return client.post(URL, data, format='json')


def field_errors(response: Response) -> dict:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields']


def assert_invalid_link(response: Response) -> None:
    assert response.status_code == 400
    assert response.json() == {'code': 'invalid_link'}


def has_password(user: User, password: str) -> bool:
    user.refresh_from_db()
    return user.check_password(password)


def login(client: APIClient, password: str) -> Response:
    data = {'email': 'ada@example.com', 'password': password}
    return client.post(reverse('auth-login'), data, format='json')


# Confirm
def test_confirm_sets_new_password(api_client: APIClient, user: User) -> None:
    response = confirm(api_client, user)
    assert response.status_code == 204
    assert response.content == b''
    assert has_password(user, NEW_PASSWORD)


def test_confirm_keeps_spaces(api_client: APIClient, user: User) -> None:
    confirm(api_client, user, password=f' {NEW_PASSWORD} ')
    assert has_password(user, f' {NEW_PASSWORD} ')


def test_confirm_does_not_log_in(api_client: APIClient, user: User) -> None:
    confirm(api_client, user)
    assert api_client.get(ME_URL).status_code == 401


def test_confirm_logs_out_all_devices(api_client: APIClient, user: User) -> None:
    device = APIClient()
    device.force_login(user)
    confirm(api_client, user)
    assert device.get(ME_URL).status_code == 401


def test_login_works_only_with_new_password(api_client: APIClient, user: User) -> None:
    confirm(api_client, user)
    assert login(api_client, PASSWORD).status_code == 400
    assert login(api_client, NEW_PASSWORD).status_code == 200


def test_confirm_with_link_from_reset_mail_works(api_client: APIClient, user: User) -> None:
    api_client.post(reverse('auth-password-reset'), {'email': 'ada@example.com'}, format='json')
    query = mail.outbox[0].body.split('?', 1)[1].split()[0]
    uid, token = (part.split('=', 1)[1] for part in query.split('&'))
    assert confirm(api_client, user, uid=uid, token=token).status_code == 204


def test_confirm_ignores_other_fields(api_client: APIClient, user: User) -> None:
    confirm(api_client, user, email='evil@example.com', isStaff=True, isActive=False)
    user.refresh_from_db()
    assert (user.email, user.is_staff, user.is_active) == ('ada@example.com', False, True)


def test_confirm_keeps_other_user(api_client: APIClient, user: User) -> None:
    other = User.objects.create_user('grace@example.com', PASSWORD)
    confirm(api_client, user)
    assert has_password(other, PASSWORD)


# Invalid link
def test_link_works_only_once(api_client: APIClient, user: User) -> None:
    data = link_data(user)
    confirm(api_client, user, **data)
    assert_invalid_link(confirm(api_client, user, **data, password='Noch-ein-Passwort-3'))
    assert has_password(user, NEW_PASSWORD)


def test_expired_link_is_rejected(
    api_client: APIClient, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    past = datetime.now() - timedelta(hours=1, minutes=1)
    monkeypatch.setattr(PasswordResetTokenGenerator, '_now', lambda self: past)
    data = link_data(user)
    monkeypatch.undo()
    assert_invalid_link(confirm(api_client, user, **data))
    assert has_password(user, PASSWORD)


def test_link_within_one_hour_works(
    api_client: APIClient, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    past = datetime.now() - timedelta(minutes=59)
    monkeypatch.setattr(PasswordResetTokenGenerator, '_now', lambda self: past)
    data = link_data(user)
    monkeypatch.undo()
    assert confirm(api_client, user, **data).status_code == 204


def test_link_after_login_is_rejected(api_client: APIClient, user: User) -> None:
    data = link_data(user)
    login(APIClient(), PASSWORD)
    assert_invalid_link(confirm(api_client, user, **data))


def test_link_after_email_change_is_rejected(api_client: APIClient, user: User) -> None:
    data = link_data(user)
    User.objects.filter(pk=user.pk).update(email='ada.neu@example.com')
    assert_invalid_link(confirm(api_client, user, **data))


def test_link_of_other_user_is_rejected(api_client: APIClient, user: User) -> None:
    other = User.objects.create_user('grace@example.com', PASSWORD)
    data = {'uid': encode(other.pk), 'token': link_data(user)['token']}
    assert_invalid_link(confirm(api_client, user, **data))
    assert has_password(other, PASSWORD)
    assert has_password(user, PASSWORD)


def test_link_of_deactivated_user_is_rejected(api_client: APIClient, user: User) -> None:
    data = link_data(user)
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert_invalid_link(confirm(api_client, user, **data))
    assert has_password(user, PASSWORD)


def test_link_of_deleted_user_is_rejected(api_client: APIClient, user: User) -> None:
    data = link_data(user)
    user.delete()
    assert_invalid_link(api_client.post(URL, data | {'password': NEW_PASSWORD}, format='json'))


@pytest.mark.parametrize(
    'uid',
    [
        'x',
        '!!!',
        encode('abc'),
        encode(10**30),
        encode(-1),
        encode('1\x00'),
        urlsafe_base64_encode(b'\xff\xfe'),
    ],
)
def test_broken_uid_is_rejected(api_client: APIClient, user: User, uid: str) -> None:
    assert_invalid_link(confirm(api_client, user, uid=uid))
    assert has_password(user, PASSWORD)


@pytest.mark.parametrize('token', ['x', 'abc-def', 'a' * 1000])
def test_broken_token_is_rejected(api_client: APIClient, user: User, token: str) -> None:
    assert_invalid_link(confirm(api_client, user, token=token))
    assert has_password(user, PASSWORD)


@pytest.mark.parametrize('password', ['123', 'password', 'ada@example.com'])
def test_invalid_link_is_reported_before_password_rules(
    api_client: APIClient, user: User, password: str
) -> None:
    assert_invalid_link(confirm(api_client, user, token='x', password=password))


# Invalid fields
@pytest.mark.parametrize(
    ('password', 'code'),
    [
        ('Kurz-1!', 'password_too_short'),
        ('password123', 'password_too_common'),
        ('84736251940', 'password_entirely_numeric'),
        ('ada@example.com', 'password_too_similar'),
    ],
)
def test_confirm_checks_password_rules(
    api_client: APIClient, user: User, password: str, code: str
) -> None:
    assert code in field_errors(confirm(api_client, user, password=password))['password']
    assert has_password(user, PASSWORD)


def test_failed_password_rules_keep_link_valid(api_client: APIClient, user: User) -> None:
    data = link_data(user)
    confirm(api_client, user, **data, password='123')
    assert confirm(api_client, user, **data).status_code == 204


@pytest.mark.parametrize(
    ('changes', 'fields'),
    [
        ({'password': ''}, {'password': ['blank']}),
        ({'password': None}, {'password': ['null']}),
        ({'uid': ''}, {'uid': ['blank']}),
        ({'token': None}, {'token': ['null']}),
    ],
)
def test_confirm_with_empty_field_is_rejected(
    api_client: APIClient, user: User, changes: dict, fields: dict
) -> None:
    assert field_errors(confirm(api_client, user, **changes)) == fields
    assert has_password(user, PASSWORD)


@pytest.mark.parametrize('field', ['uid', 'token'])
def test_confirm_with_null_character_is_rejected(
    api_client: APIClient, user: User, field: str
) -> None:
    response = confirm(api_client, user, **{field: 'MQ\x00'})
    assert field_errors(response) == {field: ['null_characters_not_allowed']}


def test_confirm_without_fields_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(URL, {}, format='json')
    assert field_errors(response) == {
        'uid': ['required'],
        'token': ['required'],
        'password': ['required'],
    }


def test_confirm_with_list_body_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(URL, ['password'], format='json')
    assert field_errors(response) == {'nonField': ['invalid']}


# Security
def test_confirm_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    response = confirm(csrf_client, user)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert has_password(user, PASSWORD)


def test_confirm_with_csrf_token_is_allowed(csrf_client: APIClient, user: User) -> None:
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    data = link_data(user) | {'password': NEW_PASSWORD}
    response = csrf_client.post(URL, data, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 204


def test_confirm_of_logged_in_user_logs_out(api_client: APIClient, user: User) -> None:
    api_client.force_login(user)
    assert confirm(api_client, user).status_code == 204
    assert api_client.get(ME_URL).status_code == 401


def test_confirm_is_throttled_after_five_attempts(api_client: APIClient, user: User) -> None:
    for _ in range(5):
        confirm(api_client, user, token='x')
    response = confirm(api_client, user)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert has_password(user, PASSWORD)


def test_confirm_shares_limit_with_login(api_client: APIClient, user: User) -> None:
    for _ in range(5):
        login(api_client, 'Falsches-Passwort-1')
    assert confirm(api_client, user).status_code == 429


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_confirm_rejects_other_methods(api_client: APIClient, user: User, method: str) -> None:
    data = link_data(user) | {'password': NEW_PASSWORD}
    response = getattr(api_client, method)(URL, data, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert has_password(user, PASSWORD)
