import pytest
from django.http import HttpResponse
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from app_accounts.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
OTHER_METHODS = ['get', 'put', 'patch', 'delete']


def register(api_client: APIClient, **changes: object) -> HttpResponse:
    data = {'email': 'grace@example.com', 'password': PASSWORD} | changes
    return api_client.post(reverse('auth-register'), data, format='json')


def field_codes(response: HttpResponse, field: str) -> list[str]:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields'][field]


# Register
def test_register_creates_user_and_returns_token(api_client: APIClient) -> None:
    response = register(api_client)
    user = User.objects.get(email='grace@example.com')
    assert response.status_code == 201
    assert response.json() == {
        'token': Token.objects.get(user=user).key,
        'user': {
            'email': 'grace@example.com',
            'since': user.since.isoformat(),
            'notifyByMail': True,
            'accent': 'blue',
        },
    }


def test_register_stores_hashed_password(api_client: APIClient) -> None:
    register(api_client)
    user = User.objects.get(email='grace@example.com')
    assert user.password.startswith('argon2$')
    assert user.check_password(PASSWORD)


def test_register_keeps_spaces_in_password(api_client: APIClient) -> None:
    register(api_client, password=f' {PASSWORD} ')
    assert User.objects.get(email='grace@example.com').check_password(f' {PASSWORD} ')


def test_register_lowercases_and_trims_email(api_client: APIClient) -> None:
    response = register(api_client, email='  Grace@Example.COM ')
    assert response.json()['user']['email'] == 'grace@example.com'
    assert User.objects.filter(email='grace@example.com').exists()


def test_register_ignores_other_fields(api_client: APIClient) -> None:
    extra = {'isStaff': True, 'isSuperuser': True, 'accent': 'teal', 'notifyByMail': False}
    register(api_client, **extra, isActive=False, since='2000-01-01')
    user = User.objects.get(email='grace@example.com')
    assert (user.is_staff, user.is_superuser, user.is_active) == (False, False, True)
    assert (user.accent, user.notify_by_mail) == ('blue', True)
    assert user.date_joined.year != 2000


def test_register_creates_user_without_groups_or_rights(api_client: APIClient) -> None:
    register(api_client, groups=[1], userPermissions=[1])
    user = User.objects.get(email='grace@example.com')
    assert not user.groups.exists()
    assert not user.user_permissions.exists()


def test_register_does_not_start_session(api_client: APIClient) -> None:
    assert 'sessionid' not in register(api_client).cookies


@pytest.mark.parametrize('field', ['email', 'password'])
def test_register_without_field_is_rejected(api_client: APIClient, field: str) -> None:
    data = {'email': 'grace@example.com', 'password': PASSWORD}
    del data[field]
    response = api_client.post(reverse('auth-register'), data, format='json')
    assert field_codes(response, field) == ['required']
    assert not User.objects.exists()


@pytest.mark.parametrize(('value', 'code'), [('', 'blank'), (None, 'null')])
@pytest.mark.parametrize('field', ['email', 'password'])
def test_register_with_empty_field_is_rejected(
    api_client: APIClient, field: str, value: str | None, code: str
) -> None:
    assert field_codes(register(api_client, **{field: value}), field) == [code]


def test_register_with_spaces_as_email_is_rejected(api_client: APIClient) -> None:
    assert field_codes(register(api_client, email='   '), 'email') == ['blank']


@pytest.mark.parametrize(
    'email',
    ['no-mail', 'grace@', '@example.com', '<script>@example.com', ['a@b.de'], {'a': 1}, 42],
)
def test_register_with_invalid_email_is_rejected(api_client: APIClient, email: object) -> None:
    assert field_codes(register(api_client, email=email), 'email') == ['invalid']


def test_register_with_too_long_email_is_rejected(api_client: APIClient) -> None:
    response = register(api_client, email=f'{"a" * 250}@example.com')
    assert 'max_length' in field_codes(response, 'email')


@pytest.mark.parametrize('email', ['ada@example.com', 'ADA@Example.com', ' ada@example.com'])
def test_register_with_taken_email_is_rejected(
    api_client: APIClient, user: User, email: str
) -> None:
    assert field_codes(register(api_client, email=email), 'email') == ['unique']
    assert User.objects.count() == 1


@pytest.mark.parametrize(
    ('password', 'code'),
    [
        ('Kaffee1', 'password_too_short'),
        ('password123', 'password_too_common'),
        ('8264917305', 'password_entirely_numeric'),
        ('grace@example.com', 'password_too_similar'),
    ],
)
def test_register_with_weak_password_is_rejected(
    api_client: APIClient, password: str, code: str
) -> None:
    assert code in field_codes(register(api_client, password=password), 'password')
    assert not User.objects.exists()


def test_register_checks_password_against_invalid_email(api_client: APIClient) -> None:
    response = register(api_client, email=['x'], password='Kaffee1')
    assert field_codes(response, 'password') == ['password_too_short']


@pytest.mark.parametrize('password', [['x'], {'a': 1}])
def test_register_with_non_text_password_is_rejected(
    api_client: APIClient, password: object
) -> None:
    assert field_codes(register(api_client, password=password), 'password') == ['invalid']


def test_register_without_body_lists_both_fields(api_client: APIClient) -> None:
    response = api_client.post(reverse('auth-register'), format='json')
    assert response.json() == {
        'code': 'validation_error',
        'fields': {'email': ['required'], 'password': ['required']},
    }


def test_register_with_broken_json_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(
        reverse('auth-register'), '{"email":', content_type='application/json'
    )
    assert response.status_code == 400
    assert response.json() == {'code': 'parse_error'}


# Register: security
def test_register_is_throttled_after_five_attempts(api_client: APIClient) -> None:
    for number in range(5):
        register(api_client, email=f'user{number}@example.com')
    response = register(api_client)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert not User.objects.filter(email='grace@example.com').exists()


def test_register_counts_failed_attempts_for_throttling(api_client: APIClient) -> None:
    for _ in range(5):
        register(api_client, email='no-mail')
    assert register(api_client).status_code == 429


def test_register_throttles_per_ip(api_client: APIClient) -> None:
    for number in range(5):
        register(api_client, email=f'user{number}@example.com')
    data = {'email': 'grace@example.com', 'password': PASSWORD}
    url = reverse('auth-register')
    response = api_client.post(url, data, format='json', REMOTE_ADDR='10.0.0.2')
    assert response.status_code == 201


def test_register_rejects_invalid_token(api_client: APIClient) -> None:
    api_client.credentials(HTTP_AUTHORIZATION='Token invalid')
    response = register(api_client)
    assert response.status_code == 401
    assert response.json() == {'code': 'authentication_failed'}
    assert not User.objects.exists()


@pytest.mark.parametrize('method', OTHER_METHODS)
def test_register_rejects_other_methods(api_client: APIClient, method: str) -> None:
    data = {'email': 'grace@example.com', 'password': PASSWORD}
    response = getattr(api_client, method)(reverse('auth-register'), data, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert not User.objects.exists()
