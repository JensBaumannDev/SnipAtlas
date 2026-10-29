import pytest
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
CSRF_TOKEN = 'a' * 32
URL = reverse('auth-email')


def change(client: APIClient, **changes: object) -> Response:
    data = {'email': 'ada.neu@example.com', 'password': PASSWORD} | changes
    return client.post(URL, data, format='json')


def field_errors(response: Response) -> dict:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields']


def stored_email(user: User) -> str:
    user.refresh_from_db()
    return user.email


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture
def other_user(db: None) -> User:
    return User.objects.create_user('grace@example.com', PASSWORD)


# Change
def test_change_email_returns_user(logged_in: APIClient, user: User) -> None:
    response = change(logged_in)
    assert response.status_code == 200
    assert response.json() == {
        'email': 'ada.neu@example.com',
        'since': user.since.isoformat(),
        'notifyByMail': True,
        'accent': 'blue',
    }
    assert stored_email(user) == 'ada.neu@example.com'


def test_change_email_lowercases_and_trims(logged_in: APIClient, user: User) -> None:
    change(logged_in, email='  Ada.Neu@Example.COM ')
    assert stored_email(user) == 'ada.neu@example.com'


def test_change_email_to_own_email_is_allowed(logged_in: APIClient, user: User) -> None:
    assert change(logged_in, email='ADA@example.com').status_code == 200
    assert stored_email(user) == 'ada@example.com'


def test_change_email_keeps_user_logged_in(logged_in: APIClient, user: User) -> None:
    change(logged_in)
    assert logged_in.get(reverse('auth-me')).status_code == 200


def test_change_email_allows_login_with_new_email(api_client: APIClient, user: User) -> None:
    api_client.force_login(user)
    change(api_client)
    api_client.logout()
    login = {'email': 'ada.neu@example.com', 'password': PASSWORD}
    assert api_client.post(reverse('auth-login'), login, format='json').status_code == 200


def test_change_email_ignores_other_fields(logged_in: APIClient, user: User) -> None:
    change(logged_in, isStaff=True, accent='teal', notifyByMail=False)
    user.refresh_from_db()
    assert (user.is_staff, user.accent, user.notify_by_mail) == (False, 'blue', True)


def test_change_email_keeps_other_user(logged_in: APIClient, user: User, other_user: User) -> None:
    change(logged_in)
    assert stored_email(other_user) == 'grace@example.com'


def test_change_email_keeps_password(logged_in: APIClient, user: User) -> None:
    change(logged_in)
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


# Wrong password
@pytest.mark.parametrize('password', ['Falsches-Passwort-1', PASSWORD.lower(), f' {PASSWORD}'])
def test_change_email_with_wrong_password_is_rejected(
    logged_in: APIClient, user: User, password: str
) -> None:
    response = change(logged_in, password=password)
    assert response.status_code == 400
    assert response.json() == {'code': 'wrong_password'}
    assert stored_email(user) == 'ada@example.com'


@pytest.mark.parametrize('email', ['no-mail', 'grace@example.com', ''])
def test_wrong_password_is_reported_before_email_errors(
    logged_in: APIClient, other_user: User, email: str
) -> None:
    response = change(logged_in, email=email, password='Falsches-Passwort-1')
    assert response.json() == {'code': 'wrong_password'}


def test_change_email_of_user_without_password_is_rejected(api_client: APIClient, db: None) -> None:
    user = User.objects.create_user('nopass@example.com')
    api_client.force_login(user)
    assert change(api_client).json() == {'code': 'wrong_password'}


# Invalid fields
@pytest.mark.parametrize(
    ('changes', 'fields'),
    [
        ({'email': ''}, {'email': ['blank']}),
        ({'email': '   '}, {'email': ['blank']}),
        ({'email': None}, {'email': ['null']}),
        ({'email': 'no-mail'}, {'email': ['invalid']}),
        ({'email': ['a@b.de']}, {'email': ['invalid']}),
        ({'email': f'{"a" * 250}@example.com'}, {'email': ['max_length']}),
        ({'email': 'grace@example.com'}, {'email': ['unique']}),
        ({'email': 'GRACE@example.com'}, {'email': ['unique']}),
        ({'password': ''}, {'password': ['blank']}),
        ({'password': None}, {'password': ['null']}),
    ],
)
def test_change_email_with_invalid_field_is_rejected(
    logged_in: APIClient, user: User, other_user: User, changes: dict, fields: dict
) -> None:
    assert field_errors(change(logged_in, **changes)) == fields
    assert stored_email(user) == 'ada@example.com'


def test_change_email_without_fields_is_rejected(logged_in: APIClient) -> None:
    response = logged_in.post(URL, {}, format='json')
    assert field_errors(response) == {'password': ['required'], 'email': ['required']}


def test_change_email_with_list_body_is_rejected(logged_in: APIClient) -> None:
    response = logged_in.post(URL, ['email'], format='json')
    assert field_errors(response) == {'nonField': ['invalid']}


# Security
def test_change_email_of_guest_is_rejected(api_client: APIClient, user: User) -> None:
    response = change(api_client)
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}
    assert stored_email(user) == 'ada@example.com'


def test_change_email_with_unknown_session_is_rejected(api_client: APIClient) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert change(api_client).status_code == 401


def test_change_email_of_deactivated_user_is_rejected(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert change(logged_in).status_code == 401
    assert stored_email(user) == 'ada@example.com'


def test_change_email_after_logout_is_rejected(logged_in: APIClient) -> None:
    logged_in.post(reverse('auth-logout'))
    assert change(logged_in).status_code == 401


def test_change_email_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    response = change(csrf_client)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert stored_email(user) == 'ada@example.com'


def test_change_email_with_csrf_token_is_allowed(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    data = {'email': 'ada.neu@example.com', 'password': PASSWORD}
    response = csrf_client.post(URL, data, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 200


def test_change_email_is_throttled_after_five_attempts(logged_in: APIClient, user: User) -> None:
    for _ in range(5):
        change(logged_in, password='Falsches-Passwort-1')
    response = change(logged_in)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert stored_email(user) == 'ada@example.com'


def test_change_email_shares_limit_with_login(logged_in: APIClient, user: User) -> None:
    login = {'email': 'ada@example.com', 'password': 'Falsches-Passwort-1'}
    for _ in range(5):
        logged_in.post(reverse('auth-login'), login, format='json')
    assert change(logged_in).status_code == 429


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_change_email_rejects_other_methods(logged_in: APIClient, user: User, method: str) -> None:
    response = getattr(logged_in, method)(URL, {'email': 'ada.neu@example.com'}, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert stored_email(user) == 'ada@example.com'
