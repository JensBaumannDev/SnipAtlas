import pytest
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from app_accounts.models import CompletedStep, Favorite, User
from app_content.models import BlueprintStep, Entry
from app_feedback.models import Suggestion

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
CSRF_TOKEN = 'a' * 32
URL = reverse('auth-delete-account')
ME_URL = reverse('auth-me')


def delete(client: APIClient, **changes: object) -> Response:
    data = {'password': PASSWORD} | changes
    return client.post(URL, data, format='json')


def field_errors(response: Response) -> dict:
    assert response.status_code == 400
    assert response.json()['code'] == 'validation_error'
    return response.json()['fields']


def exists(user: User) -> bool:
    return User.objects.filter(pk=user.pk).exists()


def login(client: APIClient, password: str = PASSWORD) -> Response:
    data = {'email': 'ada@example.com', 'password': password}
    return client.post(reverse('auth-login'), data, format='json')


def add_user_data(user: User, entry: Entry, step: BlueprintStep) -> None:
    Favorite.objects.create(user=user, entry=entry)
    CompletedStep.objects.create(user=user, step=step)
    Suggestion.objects.create(
        kind='bug', user=user, bug_type='typo', location='Start', problem='Tippfehler.'
    )


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture
def other(db: None) -> User:
    return User.objects.create_user('grace@example.com', PASSWORD)


# Delete
def test_delete_account_returns_no_content(logged_in: APIClient, user: User) -> None:
    response = delete(logged_in)
    assert response.status_code == 204
    assert response.content == b''
    assert not exists(user)


def test_delete_account_deletes_all_user_data(
    logged_in: APIClient, user: User, entry: Entry, venv_step: BlueprintStep
) -> None:
    add_user_data(user, entry, venv_step)
    delete(logged_in)
    assert not Favorite.objects.exists()
    assert not CompletedStep.objects.exists()
    assert not Suggestion.objects.exists()


def test_delete_account_keeps_data_of_others(
    logged_in: APIClient,
    user: User,
    other: User,
    entry: Entry,
    venv_step: BlueprintStep,
    entry_suggestion: Suggestion,
) -> None:
    add_user_data(user, entry, venv_step)
    add_user_data(other, entry, venv_step)
    delete(logged_in)
    assert exists(other)
    assert list(Favorite.objects.values_list('user', flat=True)) == [other.pk]
    assert list(CompletedStep.objects.values_list('user', flat=True)) == [other.pk]
    assert set(Suggestion.objects.values_list('pk', flat=True)) == {
        entry_suggestion.pk,
        Suggestion.objects.get(user=other).pk,
    }


def test_delete_account_keeps_content(
    logged_in: APIClient, user: User, entry: Entry, venv_step: BlueprintStep
) -> None:
    add_user_data(user, entry, venv_step)
    delete(logged_in)
    assert Entry.objects.filter(pk=entry.pk).exists()
    assert BlueprintStep.objects.filter(pk=venv_step.pk).exists()


def test_delete_account_logs_out_this_device(logged_in: APIClient) -> None:
    response = delete(logged_in)
    assert response.cookies['sessionid'].value == ''
    assert logged_in.get(ME_URL).status_code == 401


def test_delete_account_logs_out_other_devices(logged_in: APIClient, user: User) -> None:
    other_device = APIClient()
    other_device.force_login(user)
    delete(logged_in)
    assert other_device.get(ME_URL).status_code == 401


def test_login_fails_after_delete(logged_in: APIClient) -> None:
    delete(logged_in)
    assert login(logged_in).json() == {'code': 'invalid_credentials'}


def test_email_can_register_again_after_delete(logged_in: APIClient) -> None:
    delete(logged_in)
    data = {'email': 'ada@example.com', 'password': PASSWORD}
    assert logged_in.post(reverse('auth-register'), data, format='json').status_code == 201


def test_delete_account_ignores_other_fields(logged_in: APIClient, user: User, other: User) -> None:
    response = delete(logged_in, email='grace@example.com', id=other.pk, user=other.pk)
    assert response.status_code == 204
    assert not exists(user)
    assert exists(other)


def test_delete_account_of_staff_user_is_allowed(api_client: APIClient, staff_user: User) -> None:
    api_client.force_login(staff_user)
    assert delete(api_client).status_code == 204
    assert not exists(staff_user)


# Wrong password
@pytest.mark.parametrize('password', ['Falsches-Passwort-1', PASSWORD.lower(), f'{PASSWORD} '])
def test_delete_account_with_wrong_password_is_rejected(
    logged_in: APIClient, user: User, password: str
) -> None:
    response = delete(logged_in, password=password)
    assert response.status_code == 400
    assert response.json() == {'code': 'wrong_password'}
    assert exists(user)


def test_wrong_password_keeps_user_data(
    logged_in: APIClient, user: User, entry: Entry, venv_step: BlueprintStep
) -> None:
    add_user_data(user, entry, venv_step)
    delete(logged_in, password='Falsches-Passwort-1')
    assert Favorite.objects.filter(user=user).exists()
    assert CompletedStep.objects.filter(user=user).exists()
    assert Suggestion.objects.filter(user=user).exists()


def test_wrong_password_keeps_user_logged_in(logged_in: APIClient) -> None:
    delete(logged_in, password='Falsches-Passwort-1')
    assert logged_in.get(ME_URL).status_code == 200


def test_delete_account_of_user_without_password_is_rejected(
    api_client: APIClient, db: None
) -> None:
    user = User.objects.create_user('nopass@example.com')
    api_client.force_login(user)
    assert delete(api_client).json() == {'code': 'wrong_password'}
    assert exists(user)


# Invalid fields
@pytest.mark.parametrize(
    ('password', 'fields'),
    [('', {'password': ['blank']}), (None, {'password': ['null']})],
)
def test_delete_account_with_empty_password_is_rejected(
    logged_in: APIClient, user: User, password: str | None, fields: dict
) -> None:
    assert field_errors(delete(logged_in, password=password)) == fields
    assert exists(user)


def test_delete_account_without_fields_is_rejected(logged_in: APIClient, user: User) -> None:
    response = logged_in.post(URL, {}, format='json')
    assert field_errors(response) == {'password': ['required']}
    assert exists(user)


def test_delete_account_with_list_body_is_rejected(logged_in: APIClient, user: User) -> None:
    response = logged_in.post(URL, ['password'], format='json')
    assert field_errors(response) == {'nonField': ['invalid']}
    assert exists(user)


# Security
def test_delete_account_of_guest_is_rejected(api_client: APIClient, user: User) -> None:
    response = delete(api_client)
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}
    assert exists(user)


def test_delete_account_with_unknown_session_is_rejected(api_client: APIClient, user: User) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert delete(api_client).status_code == 401
    assert exists(user)


def test_delete_account_of_deactivated_user_is_rejected(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert delete(logged_in).status_code == 401
    assert exists(user)


def test_delete_account_after_logout_is_rejected(logged_in: APIClient, user: User) -> None:
    logged_in.post(reverse('auth-logout'))
    assert delete(logged_in).status_code == 401
    assert exists(user)


def test_delete_account_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    response = delete(csrf_client)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert exists(user)


def test_delete_account_with_csrf_token_is_allowed(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    data = {'password': PASSWORD}
    response = csrf_client.post(URL, data, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 204
    assert not exists(user)


def test_delete_account_is_throttled_after_five_attempts(logged_in: APIClient, user: User) -> None:
    for _ in range(5):
        delete(logged_in, password='Falsches-Passwort-1')
    response = delete(logged_in)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert exists(user)


def test_delete_account_shares_limit_with_login(logged_in: APIClient, user: User) -> None:
    for _ in range(5):
        login(logged_in, 'Falsches-Passwort-1')
    assert delete(logged_in).status_code == 429
    assert exists(user)


@pytest.mark.parametrize('method', ['get', 'put', 'patch', 'delete'])
def test_delete_account_rejects_other_methods(
    logged_in: APIClient, user: User, method: str
) -> None:
    response = getattr(logged_in, method)(URL, {'password': PASSWORD}, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'POST, OPTIONS'
    assert exists(user)
