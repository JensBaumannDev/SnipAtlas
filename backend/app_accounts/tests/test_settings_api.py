import pytest
from django.forms.models import model_to_dict
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle

from app_accounts.models import User

pytestmark = pytest.mark.django_db

CSRF_TOKEN = 'a' * 32
URL = reverse('settings')
EMPTY_PROJECT = {
    'project': '',
    'githubUser': '',
    'repo': '',
    'domain': '',
    'serverUser': '',
    'serverIp': '',
}
DEFAULTS = {'os': 'win', 'theme': 'system', 'language': 'auto', 'projectValues': EMPTY_PROJECT}


def update(client: APIClient, data: object) -> Response:
    return client.patch(URL, data, format='json')


def stored(user: User) -> dict:
    user.refresh_from_db()
    return model_to_dict(user)


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture
def other_user(db: None) -> User:
    return User.objects.create_user(
        'grace@example.com', 'Kaffee-Tasse-2026!', os='unix', project_repo='cobol'
    )


# Read
def test_settings_return_defaults(logged_in: APIClient) -> None:
    response = logged_in.get(URL)
    assert response.status_code == 200
    assert response.json() == DEFAULTS


def test_settings_return_stored_values(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(
        os='unix', theme='dark', language='en', project_github_user='ada', project_server_ip='::1'
    )
    assert logged_in.get(URL).json() == {
        'os': 'unix',
        'theme': 'dark',
        'language': 'en',
        'projectValues': EMPTY_PROJECT | {'githubUser': 'ada', 'serverIp': '::1'},
    }


def test_settings_return_only_own_values(logged_in: APIClient, other_user: User) -> None:
    assert logged_in.get(URL).json() == DEFAULTS


def test_settings_keep_html_as_text(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(project_name='<script>alert(1)</script>')
    response = logged_in.get(URL)
    assert response['Content-Type'] == 'application/json'
    assert response.json()['projectValues']['project'] == '<script>alert(1)</script>'


def test_settings_ignore_query_parameters(logged_in: APIClient, other_user: User) -> None:
    assert logged_in.get(URL, {'user': other_user.pk, 'os': 'unix'}).json() == DEFAULTS


def test_settings_load_in_two_queries(
    logged_in: APIClient, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(2):
        logged_in.get(URL)


# Update
def test_update_settings_changes_values(logged_in: APIClient, user: User) -> None:
    data = {'os': 'unix', 'theme': 'dark', 'language': 'en'}
    project = {'githubUser': 'ada', 'serverIp': '::1'}
    response = update(logged_in, data | {'projectValues': project})
    assert response.status_code == 200
    assert response.json() == data | {'projectValues': EMPTY_PROJECT | project}
    values = stored(user)
    assert (values['os'], values['theme'], values['language']) == ('unix', 'dark', 'en')
    assert (values['project_github_user'], values['project_server_ip']) == ('ada', '::1')


def test_update_settings_changes_only_given_fields(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(theme='dark', project_repo='snipatlas')
    update(logged_in, {'os': 'unix', 'projectValues': {'domain': 'example.com'}})
    values = stored(user)
    assert (values['os'], values['theme']) == ('unix', 'dark')
    assert (values['project_repo'], values['project_domain']) == ('snipatlas', 'example.com')


def test_update_settings_clears_project_value(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(project_repo='snipatlas')
    update(logged_in, {'projectValues': {'repo': ''}})
    assert stored(user)['project_repo'] == ''


def test_update_settings_trims_project_values(logged_in: APIClient, user: User) -> None:
    update(logged_in, {'projectValues': {'project': '  snipatlas  '}})
    assert stored(user)['project_name'] == 'snipatlas'


def test_update_settings_accepts_project_value_of_100_characters(
    logged_in: APIClient, user: User
) -> None:
    assert update(logged_in, {'projectValues': {'repo': 'x' * 100}}).status_code == 200
    assert stored(user)['project_repo'] == 'x' * 100


def test_update_settings_with_empty_body_changes_nothing(logged_in: APIClient, user: User) -> None:
    before = stored(user)
    response = update(logged_in, {})
    assert response.status_code == 200
    assert response.json() == DEFAULTS
    assert stored(user) == before


def test_update_settings_with_empty_project_values_changes_nothing(
    logged_in: APIClient, user: User
) -> None:
    before = stored(user)
    assert update(logged_in, {'projectValues': {}}).status_code == 200
    assert stored(user) == before


def test_update_settings_ignores_other_fields(logged_in: APIClient, user: User) -> None:
    before = stored(user)
    data = {'email': 'grace@example.com', 'accent': 'teal', 'notifyByMail': False}
    update(logged_in, data | {'isStaff': True, 'projectName': 'x', 'password': 'x'})
    assert stored(user) == before


def test_update_settings_keeps_other_user(logged_in: APIClient, other_user: User) -> None:
    before = stored(other_user)
    update(logged_in, {'os': 'win', 'projectValues': {'repo': 'snipatlas'}})
    assert stored(other_user) == before


def test_update_settings_keeps_special_characters_as_text(logged_in: APIClient, user: User) -> None:
    values = {'project': '<script>alert(1)</script>', 'repo': 'übung-🚀', 'domain': 'a\'b"c'}
    response = update(logged_in, {'projectValues': values})
    assert response.json()['projectValues'] == EMPTY_PROJECT | values
    stored_values = stored(user)
    assert stored_values['project_name'] == '<script>alert(1)</script>'
    assert stored_values['project_repo'] == 'übung-🚀'


def test_update_settings_stores_number_as_text(logged_in: APIClient, user: User) -> None:
    update(logged_in, {'projectValues': {'serverUser': 42}})
    assert stored(user)['project_server_user'] == '42'


def test_update_settings_accepts_snake_case_key(logged_in: APIClient, user: User) -> None:
    update(logged_in, {'projectValues': {'github_user': 'ada'}})
    assert stored(user)['project_github_user'] == 'ada'


def test_update_settings_ignores_query_parameters(logged_in: APIClient, user: User) -> None:
    response = logged_in.patch(f'{URL}?os=unix&theme=dark', {}, format='json')
    assert response.status_code == 200
    assert (stored(user)['os'], stored(user)['theme']) == ('win', 'system')


def test_update_settings_ignores_accept_language(logged_in: APIClient, user: User) -> None:
    response = logged_in.patch(URL, {'language': 'de'}, format='json', HTTP_ACCEPT_LANGUAGE='en')
    assert response.json()['language'] == 'de'
    assert stored(user)['language'] == 'de'


def test_update_settings_keeps_user_logged_in(logged_in: APIClient, user: User) -> None:
    update(logged_in, {'os': 'unix'})
    assert logged_in.session.get('_auth_user_id') == str(user.pk)
    assert logged_in.get(URL).status_code == 200


def test_update_settings_queries(
    logged_in: APIClient, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(3):
        update(logged_in, {'os': 'unix', 'projectValues': {'repo': 'snipatlas'}})


# Update: invalid values
@pytest.mark.parametrize(
    ('data', 'fields'),
    [
        ({'os': 'mac'}, {'os': ['invalid_choice']}),
        ({'os': 'WIN'}, {'os': ['invalid_choice']}),
        ({'os': ''}, {'os': ['invalid_choice']}),
        ({'os': None}, {'os': ['null']}),
        ({'theme': 'blue'}, {'theme': ['invalid_choice']}),
        ({'theme': ['dark']}, {'theme': ['invalid_choice']}),
        ({'language': 'fr'}, {'language': ['invalid_choice']}),
        ({'language': '<script>'}, {'language': ['invalid_choice']}),
        ({'projectValues': None}, {'projectValues': ['null']}),
        ({'projectValues': 'snipatlas'}, {'projectValues': ['not_a_dict']}),
        ({'projectValues': ['repo']}, {'projectValues': ['not_a_dict']}),
        ({'projectValues': {'repo': 'x' * 101}}, {'projectValues': {'repo': ['max_length']}}),
        ({'projectValues': {'repo': None}}, {'projectValues': {'repo': ['null']}}),
        ({'projectValues': {'repo': {'a': 1}}}, {'projectValues': {'repo': ['invalid']}}),
        ({'projectValues': {'repo': True}}, {'projectValues': {'repo': ['invalid']}}),
        ({'projectValues': {'repo': ['x']}}, {'projectValues': {'repo': ['invalid']}}),
        (
            {'projectValues': {'repo': 'x' * 101, 'domain': 'x' * 101}},
            {'projectValues': {'repo': ['max_length'], 'domain': ['max_length']}},
        ),
        (
            {'projectValues': {'cobol': 'x', 'email': 'x'}},
            {'projectValues': {'cobol': ['unknown_key'], 'email': ['unknown_key']}},
        ),
        (
            {'projectValues': {'cobol': 'x', 'repo': 'x' * 101}},
            {'projectValues': {'repo': ['max_length']}},
        ),
        (
            {'os': 'mac', 'projectValues': {'cobol': 'x'}},
            {'os': ['invalid_choice'], 'projectValues': {'cobol': ['unknown_key']}},
        ),
        ({'projectValues': {'email': 'x'}}, {'projectValues': {'email': ['unknown_key']}}),
        (
            {'projectValues': {'projectName': 'x'}},
            {'projectValues': {'projectName': ['unknown_key']}},
        ),
    ],
)
def test_update_settings_with_invalid_value_is_rejected(
    logged_in: APIClient, user: User, data: dict, fields: dict
) -> None:
    before = stored(user)
    response = update(logged_in, data)
    assert response.status_code == 400
    assert response.json() == {'code': 'validation_error', 'fields': fields}
    assert stored(user) == before


def test_update_settings_with_one_invalid_field_changes_nothing(
    logged_in: APIClient, user: User
) -> None:
    before = stored(user)
    update(logged_in, {'os': 'unix', 'projectValues': {'repo': 'ok', 'cobol': 'x'}})
    assert stored(user) == before


def test_update_settings_with_list_body_is_rejected(logged_in: APIClient) -> None:
    response = update(logged_in, ['os'])
    assert response.status_code == 400
    assert response.json() == {'code': 'validation_error', 'fields': {'nonField': ['invalid']}}


def test_update_settings_with_broken_json_is_rejected(logged_in: APIClient) -> None:
    response = logged_in.patch(URL, '{"os":', content_type='application/json')
    assert response.status_code == 400
    assert response.json() == {'code': 'parse_error'}


# Security
@pytest.mark.parametrize('method', ['get', 'patch'])
def test_settings_of_guest_are_rejected(api_client: APIClient, method: str) -> None:
    response = getattr(api_client, method)(URL, {'os': 'unix'}, format='json')
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}


@pytest.mark.parametrize('method', ['get', 'patch'])
def test_settings_with_unknown_session_are_rejected(api_client: APIClient, method: str) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert getattr(api_client, method)(URL, {'os': 'unix'}, format='json').status_code == 401


@pytest.mark.parametrize('method', ['get', 'patch'])
def test_settings_of_deactivated_user_are_rejected(
    logged_in: APIClient, user: User, method: str
) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert getattr(logged_in, method)(URL, {'os': 'unix'}, format='json').status_code == 401
    assert stored(user)['os'] == 'win'


@pytest.mark.parametrize('method', ['get', 'patch'])
def test_settings_of_deleted_user_are_rejected(
    logged_in: APIClient, user: User, method: str
) -> None:
    user.delete()
    assert getattr(logged_in, method)(URL, {'os': 'unix'}, format='json').status_code == 401
    assert not User.objects.exists()


@pytest.mark.parametrize('method', ['get', 'patch'])
def test_settings_after_logout_are_rejected(logged_in: APIClient, method: str) -> None:
    logged_in.post(reverse('auth-logout'))
    assert getattr(logged_in, method)(URL, {'os': 'unix'}, format='json').status_code == 401


def test_update_settings_without_csrf_token_is_rejected(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    response = update(csrf_client, {'os': 'unix'})
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert stored(user)['os'] == 'win'


def test_update_settings_with_csrf_token_is_allowed(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    response = csrf_client.patch(URL, {'os': 'unix'}, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 200


def test_settings_need_no_csrf_token_for_reading(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    assert csrf_client.get(URL).status_code == 200


def test_settings_are_throttled(
    logged_in: APIClient, user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, 'user', '1/hour')
    logged_in.get(URL)
    response = update(logged_in, {'os': 'unix'})
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert stored(user)['os'] == 'win'


@pytest.mark.parametrize('method', ['post', 'put', 'delete'])
def test_settings_reject_other_methods(logged_in: APIClient, user: User, method: str) -> None:
    before = stored(user)
    data = {'os': 'unix', 'projectValues': {'repo': 'snipatlas'}}
    response = getattr(logged_in, method)(URL, data, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'GET, PATCH, HEAD, OPTIONS'
    assert stored(user) == before
