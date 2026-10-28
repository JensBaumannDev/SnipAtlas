import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from app_accounts.models import User

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
CSRF_TOKEN = 'a' * 32
OTHER_METHODS = ['get', 'put', 'patch', 'delete']


def register(api_client: APIClient, **changes: object) -> HttpResponse:
    data = {'email': 'grace@example.com', 'password': PASSWORD} | changes
    return api_client.post(reverse('auth-register'), data, format='json')


def login(api_client: APIClient, **changes: object) -> HttpResponse:
    data = {'email': 'ada@example.com', 'password': PASSWORD} | changes
    return api_client.post(reverse('auth-login'), data, format='json')


def field_codes(response: HttpResponse, field: str) -> list[str]:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields'][field]


def logged_in_user_id(api_client: APIClient) -> str | None:
    return api_client.session.get('_auth_user_id')


# Register
def test_register_creates_user_and_returns_it(api_client: APIClient) -> None:
    response = register(api_client)
    user = User.objects.get(email='grace@example.com')
    assert response.status_code == 201
    assert response.json() == {
        'email': 'grace@example.com',
        'since': user.since.isoformat(),
        'notifyByMail': True,
        'accent': 'blue',
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
    assert response.json()['email'] == 'grace@example.com'
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


def test_register_logs_in_new_user(api_client: APIClient) -> None:
    register(api_client)
    user = User.objects.get(email='grace@example.com')
    assert logged_in_user_id(api_client) == str(user.pk)


def test_register_sets_http_only_session_cookie(api_client: APIClient) -> None:
    cookie = register(api_client).cookies['sessionid']
    assert cookie['httponly']
    assert cookie['samesite'] == 'Lax'


def test_register_sets_new_readable_csrf_cookie(api_client: APIClient) -> None:
    api_client.cookies['csrftoken'] = CSRF_TOKEN
    cookie = register(api_client).cookies['csrftoken']
    assert cookie.value != CSRF_TOKEN
    assert not cookie['httponly']


def test_register_while_logged_in_switches_to_new_user(api_client: APIClient, user: User) -> None:
    api_client.force_login(user)
    register(api_client)
    assert logged_in_user_id(api_client) != str(user.pk)
    assert User.objects.get(pk=logged_in_user_id(api_client)).email == 'grace@example.com'


def test_failed_register_does_not_log_in(api_client: APIClient) -> None:
    register(api_client, email='no-mail')
    assert logged_in_user_id(api_client) is None


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


def test_register_throttles_per_ip_even_when_logged_in(api_client: APIClient, user: User) -> None:
    for number in range(4):
        register(api_client, email=f'user{number}@example.com')
    api_client.force_login(user)
    register(api_client)
    assert register(api_client, email='lin@example.com').status_code == 429


def test_register_without_csrf_token_is_rejected(csrf_client: APIClient) -> None:
    response = register(csrf_client)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert not User.objects.exists()


def test_register_with_csrf_token_is_allowed(csrf_client: APIClient) -> None:
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    data = {'email': 'grace@example.com', 'password': PASSWORD}
    url = reverse('auth-register')
    response = csrf_client.post(url, data, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 201


@pytest.mark.parametrize('method', OTHER_METHODS)
def test_register_rejects_other_methods(api_client: APIClient, method: str) -> None:
    data = {'email': 'grace@example.com', 'password': PASSWORD}
    response = getattr(api_client, method)(reverse('auth-register'), data, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert not User.objects.exists()


# CSRF
def test_csrf_returns_no_content(api_client: APIClient) -> None:
    response = api_client.get(reverse('auth-csrf'))
    assert response.status_code == 204
    assert response.content == b''


def test_csrf_sets_readable_cookie(api_client: APIClient) -> None:
    cookie = api_client.get(reverse('auth-csrf')).cookies['csrftoken']
    assert len(cookie.value) == 32
    assert not cookie['httponly']
    assert cookie['samesite'] == 'Lax'


def test_csrf_keeps_existing_token(api_client: APIClient) -> None:
    api_client.cookies['csrftoken'] = CSRF_TOKEN
    response = api_client.get(reverse('auth-csrf'))
    assert response.cookies['csrftoken'].value == CSRF_TOKEN


def test_csrf_replaces_broken_token(api_client: APIClient) -> None:
    api_client.cookies['csrftoken'] = '<script>'
    cookie = api_client.get(reverse('auth-csrf')).cookies['csrftoken']
    assert cookie.value != '<script>'
    assert len(cookie.value) == 32


def test_csrf_token_allows_register(csrf_client: APIClient) -> None:
    token = csrf_client.get(reverse('auth-csrf')).cookies['csrftoken'].value
    data = {'email': 'grace@example.com', 'password': PASSWORD}
    url = reverse('auth-register')
    response = csrf_client.post(url, data, format='json', HTTP_X_CSRFTOKEN=token)
    assert response.status_code == 201


def test_csrf_does_not_start_session(api_client: APIClient) -> None:
    response = api_client.get(reverse('auth-csrf'))
    assert 'sessionid' not in response.cookies
    assert logged_in_user_id(api_client) is None


def test_csrf_keeps_user_logged_in(api_client: APIClient, user: User) -> None:
    api_client.force_login(user)
    assert api_client.get(reverse('auth-csrf')).status_code == 204
    assert logged_in_user_id(api_client) == str(user.pk)


def test_csrf_treats_unknown_session_as_guest(api_client: APIClient) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert api_client.get(reverse('auth-csrf')).status_code == 204


def test_csrf_is_throttled_for_guests(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(AnonRateThrottle.THROTTLE_RATES, 'anon', '1/hour')
    api_client.get(reverse('auth-csrf'))
    response = api_client.get(reverse('auth-csrf'))
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'


def test_csrf_is_throttled_for_users(
    api_client: APIClient, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, 'user', '1/hour')
    api_client.force_login(user)
    api_client.get(reverse('auth-csrf'))
    assert api_client.get(reverse('auth-csrf')).status_code == 429


def test_csrf_is_not_limited_like_login(api_client: APIClient) -> None:
    for _ in range(6):
        response = api_client.get(reverse('auth-csrf'))
    assert response.status_code == 204


@pytest.mark.parametrize('method', ['post', 'put', 'patch', 'delete'])
def test_csrf_rejects_other_methods(api_client: APIClient, method: str) -> None:
    response = getattr(api_client, method)(reverse('auth-csrf'))
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'GET, HEAD, OPTIONS'


def test_csrf_needs_no_queries(
    api_client: APIClient, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(0):
        api_client.get(reverse('auth-csrf'))


# Login
def test_login_returns_user(api_client: APIClient, user: User) -> None:
    response = login(api_client)
    assert response.status_code == 200
    assert response.json() == {
        'email': 'ada@example.com',
        'since': user.since.isoformat(),
        'notifyByMail': True,
        'accent': 'blue',
    }


def test_login_returns_stored_settings(api_client: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(accent='teal', notify_by_mail=False)
    data = login(api_client).json()
    assert (data['accent'], data['notifyByMail']) == ('teal', False)


def test_login_logs_in_user(api_client: APIClient, user: User) -> None:
    login(api_client)
    assert logged_in_user_id(api_client) == str(user.pk)


def test_login_sets_http_only_session_cookie(api_client: APIClient, user: User) -> None:
    cookie = login(api_client).cookies['sessionid']
    assert cookie['httponly']
    assert cookie['samesite'] == 'Lax'


def test_login_creates_new_session_key(api_client: APIClient, user: User) -> None:
    session = api_client.session
    session['visited'] = True
    session.save()
    api_client.cookies['sessionid'] = session.session_key
    login(api_client)
    assert api_client.cookies['sessionid'].value != session.session_key


def test_login_sets_new_readable_csrf_cookie(api_client: APIClient, user: User) -> None:
    api_client.cookies['csrftoken'] = CSRF_TOKEN
    cookie = login(api_client).cookies['csrftoken']
    assert cookie.value != CSRF_TOKEN
    assert not cookie['httponly']


def test_login_ignores_case_and_spaces_in_email(api_client: APIClient, user: User) -> None:
    assert login(api_client, email=' ADA@Example.com ').status_code == 200


def test_login_sets_last_login(api_client: APIClient, user: User) -> None:
    login(api_client)
    user.refresh_from_db()
    assert user.last_login is not None


def test_login_works_for_staff(api_client: APIClient, staff_user: User) -> None:
    assert login(api_client, email='staff@example.com').status_code == 200


def test_login_while_logged_in_switches_user(
    api_client: APIClient, user: User, staff_user: User
) -> None:
    api_client.force_login(staff_user)
    login(api_client)
    assert logged_in_user_id(api_client) == str(user.pk)


def test_login_treats_unknown_session_as_guest(api_client: APIClient, user: User) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert login(api_client).status_code == 200


@pytest.mark.parametrize(
    'changes',
    [
        {'password': 'wrong'},
        {'password': f' {PASSWORD} '},
        {'password': PASSWORD.lower()},
        {'email': 'grace@example.com'},
        {'email': 'no-mail'},
        {'email': 'ada@examıple.com'},
        {'email': 'x' * 5000},
        {'email': '<script>@example.com'},
    ],
)
def test_login_with_wrong_data_is_rejected(
    api_client: APIClient, user: User, changes: dict
) -> None:
    response = login(api_client, **changes)
    assert response.status_code == 400
    assert response.json() == {'code': 'invalid_credentials'}
    assert logged_in_user_id(api_client) is None


def test_login_of_inactive_user_is_rejected(api_client: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert login(api_client).json() == {'code': 'invalid_credentials'}


def test_login_of_user_without_password_is_rejected(api_client: APIClient) -> None:
    User.objects.create_user('grace@example.com')
    response = login(api_client, email='grace@example.com', password='!')
    assert response.json() == {'code': 'invalid_credentials'}


def test_login_with_wrong_password_does_not_set_last_login(
    api_client: APIClient, user: User
) -> None:
    login(api_client, password='wrong')
    user.refresh_from_db()
    assert user.last_login is None


def test_failed_login_keeps_current_user_logged_in(
    api_client: APIClient, user: User, staff_user: User
) -> None:
    api_client.force_login(staff_user)
    login(api_client, password='wrong')
    assert logged_in_user_id(api_client) == str(staff_user.pk)


@pytest.mark.parametrize('field', ['email', 'password'])
def test_login_without_field_is_rejected(api_client: APIClient, user: User, field: str) -> None:
    data = {'email': 'ada@example.com', 'password': PASSWORD}
    del data[field]
    response = api_client.post(reverse('auth-login'), data, format='json')
    assert field_codes(response, field) == ['required']


@pytest.mark.parametrize(
    ('value', 'code'), [('', 'blank'), (None, 'null'), (['x'], 'invalid'), ({'a': 1}, 'invalid')]
)
@pytest.mark.parametrize('field', ['email', 'password'])
def test_login_with_empty_or_broken_field_is_rejected(
    api_client: APIClient, user: User, field: str, value: object, code: str
) -> None:
    assert field_codes(login(api_client, **{field: value}), field) == [code]


@pytest.mark.parametrize('field', ['email', 'password'])
def test_login_with_null_character_is_rejected(
    api_client: APIClient, user: User, field: str
) -> None:
    response = login(api_client, **{field: 'ada\x00@example.com'})
    assert field_codes(response, field) == ['null_characters_not_allowed']


def test_login_without_body_lists_both_fields(api_client: APIClient) -> None:
    response = api_client.post(reverse('auth-login'), format='json')
    assert response.json() == {
        'code': 'validation_error',
        'fields': {'email': ['required'], 'password': ['required']},
    }


def test_login_with_broken_json_is_rejected(api_client: APIClient) -> None:
    response = api_client.post(reverse('auth-login'), '{"email":', content_type='application/json')
    assert response.status_code == 400
    assert response.json() == {'code': 'parse_error'}


def test_login_queries(
    api_client: APIClient, user: User, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(9):
        login(api_client)


def test_login_ignores_query_parameters(api_client: APIClient, user: User) -> None:
    url = f'{reverse("auth-login")}?email=grace@example.com&password=x'
    data = {'email': 'ada@example.com', 'password': PASSWORD}
    assert api_client.post(url, data, format='json').status_code == 200


def test_login_with_very_long_password_is_rejected(api_client: APIClient, user: User) -> None:
    response = login(api_client, password='x' * 100_000)
    assert response.json() == {'code': 'invalid_credentials'}


# Login: security
def test_login_is_throttled_after_five_attempts(api_client: APIClient, user: User) -> None:
    for _ in range(5):
        login(api_client, password='wrong')
    response = login(api_client)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert logged_in_user_id(api_client) is None


def test_login_shares_throttling_with_register(api_client: APIClient, user: User) -> None:
    for number in range(3):
        register(api_client, email=f'user{number}@example.com')
    login(api_client)
    login(api_client)
    assert login(api_client).status_code == 429
    assert register(api_client).status_code == 429


def test_login_throttles_per_ip(api_client: APIClient, user: User) -> None:
    for _ in range(5):
        login(api_client, password='wrong')
    data = {'email': 'ada@example.com', 'password': PASSWORD}
    url = reverse('auth-login')
    assert api_client.post(url, data, format='json', REMOTE_ADDR='10.0.0.2').status_code == 200


def test_login_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    response = login(csrf_client)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert logged_in_user_id(csrf_client) is None


def test_login_with_csrf_token_from_endpoint_is_allowed(csrf_client: APIClient, user: User) -> None:
    token = csrf_client.get(reverse('auth-csrf')).cookies['csrftoken'].value
    data = {'email': 'ada@example.com', 'password': PASSWORD}
    url = reverse('auth-login')
    response = csrf_client.post(url, data, format='json', HTTP_X_CSRFTOKEN=token)
    assert response.status_code == 200


@pytest.mark.parametrize('method', OTHER_METHODS)
def test_login_rejects_other_methods(api_client: APIClient, user: User, method: str) -> None:
    data = {'email': 'ada@example.com', 'password': PASSWORD}
    response = getattr(api_client, method)(reverse('auth-login'), data, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert logged_in_user_id(api_client) is None
