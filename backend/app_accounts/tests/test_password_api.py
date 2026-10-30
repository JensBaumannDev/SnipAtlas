import pytest
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
NEW_PASSWORD = 'Tee-Kanne-2027?'
CSRF_TOKEN = 'a' * 32
URL = reverse('auth-password')
ME_URL = reverse('auth-me')


def change(client: APIClient, **changes: object) -> Response:
    data = {'current': PASSWORD, 'next': NEW_PASSWORD} | changes
    return client.post(URL, data, format='json')


def field_errors(response: Response) -> dict:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields']


def has_password(user: User, password: str) -> bool:
    user.refresh_from_db()
    return user.check_password(password)


def login(client: APIClient, password: str) -> Response:
    data = {'email': 'ada@example.com', 'password': password}
    return client.post(reverse('auth-login'), data, format='json')


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


# Change
def test_change_password_returns_user(logged_in: APIClient, user: User) -> None:
    response = change(logged_in)
    assert response.status_code == 200
    assert response.json() == {
        'email': 'ada@example.com',
        'since': user.since.isoformat(),
        'notifyByMail': True,
        'accent': 'blue',
    }
    assert has_password(user, NEW_PASSWORD)


def test_change_password_keeps_spaces(logged_in: APIClient, user: User) -> None:
    change(logged_in, next=f' {NEW_PASSWORD} ')
    assert has_password(user, f' {NEW_PASSWORD} ')


def test_change_password_keeps_this_device_logged_in(logged_in: APIClient) -> None:
    change(logged_in)
    assert logged_in.get(ME_URL).status_code == 200


def test_change_password_logs_out_other_devices(logged_in: APIClient, user: User) -> None:
    other_device = APIClient()
    other_device.force_login(user)
    change(logged_in)
    assert other_device.get(ME_URL).status_code == 204


def test_change_password_rotates_session_key(logged_in: APIClient) -> None:
    before = logged_in.cookies['sessionid'].value
    response = change(logged_in)
    assert response.cookies['sessionid'].value != before


def test_login_works_only_with_new_password(api_client: APIClient, user: User) -> None:
    api_client.force_login(user)
    change(api_client)
    api_client.logout()
    assert login(api_client, PASSWORD).status_code == 400
    assert login(api_client, NEW_PASSWORD).status_code == 200


def test_change_password_to_same_password_is_allowed(logged_in: APIClient, user: User) -> None:
    assert change(logged_in, next=PASSWORD).status_code == 200
    assert has_password(user, PASSWORD)


def test_change_password_ignores_other_fields(logged_in: APIClient, user: User) -> None:
    change(logged_in, email='evil@example.com', isStaff=True, password='x')
    user.refresh_from_db()
    assert (user.email, user.is_staff) == ('ada@example.com', False)
    assert user.check_password(NEW_PASSWORD)


def test_change_password_keeps_other_user(logged_in: APIClient, db: None) -> None:
    other = User.objects.create_user('grace@example.com', PASSWORD)
    change(logged_in)
    assert has_password(other, PASSWORD)


# Wrong password
@pytest.mark.parametrize('current', ['Falsches-Passwort-1', PASSWORD.lower(), f'{PASSWORD} '])
def test_change_password_with_wrong_current_is_rejected(
    logged_in: APIClient, user: User, current: str
) -> None:
    response = change(logged_in, current=current)
    assert response.status_code == 400
    assert response.json() == {'code': 'wrong_password'}
    assert has_password(user, PASSWORD)


@pytest.mark.parametrize('next_password', ['123', '', 'password'])
def test_wrong_current_is_reported_before_password_rules(
    logged_in: APIClient, next_password: str
) -> None:
    response = change(logged_in, current='Falsches-Passwort-1', next=next_password)
    assert response.json() == {'code': 'wrong_password'}


def test_wrong_current_keeps_other_devices_logged_in(logged_in: APIClient, user: User) -> None:
    other_device = APIClient()
    other_device.force_login(user)
    change(logged_in, current='Falsches-Passwort-1')
    assert other_device.get(ME_URL).status_code == 200


def test_change_password_of_user_without_password_is_rejected(
    api_client: APIClient, db: None
) -> None:
    user = User.objects.create_user('nopass@example.com')
    api_client.force_login(user)
    assert change(api_client).json() == {'code': 'wrong_password'}


# Invalid fields
@pytest.mark.parametrize(
    ('next_password', 'code'),
    [
        ('Kurz-1!', 'password_too_short'),
        ('password123', 'password_too_common'),
        ('84736251940', 'password_entirely_numeric'),
        ('ada@example.com', 'password_too_similar'),
    ],
)
def test_change_password_checks_password_rules(
    logged_in: APIClient, user: User, next_password: str, code: str
) -> None:
    assert code in field_errors(change(logged_in, next=next_password))['next']
    assert has_password(user, PASSWORD)


@pytest.mark.parametrize(
    ('changes', 'fields'),
    [
        ({'next': ''}, {'next': ['blank']}),
        ({'next': None}, {'next': ['null']}),
        ({'current': ''}, {'current': ['blank']}),
        ({'current': None}, {'current': ['null']}),
    ],
)
def test_change_password_with_empty_field_is_rejected(
    logged_in: APIClient, user: User, changes: dict, fields: dict
) -> None:
    assert field_errors(change(logged_in, **changes)) == fields
    assert has_password(user, PASSWORD)


def test_change_password_without_fields_is_rejected(logged_in: APIClient) -> None:
    response = logged_in.post(URL, {}, format='json')
    assert field_errors(response) == {'current': ['required'], 'next': ['required']}


def test_change_password_with_list_body_is_rejected(logged_in: APIClient) -> None:
    response = logged_in.post(URL, ['next'], format='json')
    assert field_errors(response) == {'nonField': ['invalid']}


def test_failed_change_keeps_other_devices_logged_in(logged_in: APIClient, user: User) -> None:
    other_device = APIClient()
    other_device.force_login(user)
    change(logged_in, next='123')
    assert other_device.get(ME_URL).status_code == 200


# Security
def test_change_password_of_guest_is_rejected(api_client: APIClient, user: User) -> None:
    response = change(api_client)
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}
    assert has_password(user, PASSWORD)


def test_change_password_with_unknown_session_is_rejected(api_client: APIClient) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert change(api_client).status_code == 401


def test_change_password_of_deactivated_user_is_rejected(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert change(logged_in).status_code == 401
    assert has_password(user, PASSWORD)


def test_change_password_after_logout_is_rejected(logged_in: APIClient) -> None:
    logged_in.post(reverse('auth-logout'))
    assert change(logged_in).status_code == 401


def test_change_password_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    response = change(csrf_client)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert has_password(user, PASSWORD)


def test_change_password_with_csrf_token_is_allowed(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    data = {'current': PASSWORD, 'next': NEW_PASSWORD}
    response = csrf_client.post(URL, data, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 200


def test_change_password_is_throttled_after_five_attempts(logged_in: APIClient, user: User) -> None:
    for _ in range(5):
        change(logged_in, current='Falsches-Passwort-1')
    response = change(logged_in)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert has_password(user, PASSWORD)


def test_change_password_shares_limit_with_login(logged_in: APIClient, user: User) -> None:
    for _ in range(5):
        login(logged_in, 'Falsches-Passwort-1')
    assert change(logged_in).status_code == 429


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_change_password_rejects_other_methods(
    logged_in: APIClient, user: User, method: str
) -> None:
    data = {'current': PASSWORD, 'next': NEW_PASSWORD}
    response = getattr(logged_in, method)(URL, data, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert has_password(user, PASSWORD)
