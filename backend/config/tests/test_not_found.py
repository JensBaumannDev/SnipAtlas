import pytest
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle

from app_accounts.models import User

CSRF_TOKEN = 'a' * 32

UNKNOWN_PATHS = (
    '/api/',
    '/api/unknown/',
    '/api/glossary/x/',
    '/api/news/x/',
    '/api/entries/a.b/',
    '/api/entries/x/y/',
    '/api/topics/',
)


@pytest.mark.parametrize('path', UNKNOWN_PATHS)
def test_unknown_api_path_returns_json_not_found(api_client: APIClient, path: str) -> None:
    response = api_client.get(path)
    assert response.status_code == 404
    assert response['Content-Type'] == 'application/json'
    assert response.json() == {'code': 'not_found'}


@pytest.mark.parametrize('method', ['post', 'put', 'patch', 'delete', 'options', 'head'])
def test_unknown_api_path_returns_not_found_for_every_method(
    csrf_client: APIClient, method: str
) -> None:
    response = getattr(csrf_client, method)('/api/unknown/')
    assert response.status_code == 404
    if method != 'head':
        assert response.json() == {'code': 'not_found'}


def test_unknown_api_path_without_slash_redirects_to_slash(api_client: APIClient) -> None:
    response = api_client.get('/api/unknown')
    assert response.status_code == 301
    assert response['Location'] == '/api/unknown/'


def test_known_api_path_without_slash_still_redirects(api_client: APIClient) -> None:
    response = api_client.get('/api/groups')
    assert response.status_code == 301
    assert response['Location'] == '/api/groups/'


def test_unknown_api_path_keeps_special_characters_out_of_body(api_client: APIClient) -> None:
    response = api_client.get('/api/%3Cscript%3Ealert(1)%3C/script%3E/')
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}


def test_unknown_api_path_is_throttled(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(AnonRateThrottle.THROTTLE_RATES, 'anon', '1/hour')
    api_client.get('/api/unknown/')
    response = api_client.get('/api/unknown/')
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'


@pytest.mark.django_db
def test_unknown_api_path_with_unknown_session_returns_not_found(api_client: APIClient) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    response = api_client.get('/api/unknown/')
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}


def test_unknown_api_path_needs_csrf_token_when_logged_in(
    csrf_client: APIClient, user: User
) -> None:
    csrf_client.force_login(user)
    response = csrf_client.post('/api/unknown/')
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}


def test_unknown_api_path_with_csrf_token_returns_not_found_when_logged_in(
    csrf_client: APIClient, user: User
) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    response = csrf_client.post('/api/unknown/', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}


def test_path_outside_api_keeps_html_not_found(api_client: APIClient) -> None:
    response = api_client.get('/unknown/')
    assert response.status_code == 404
    assert response['Content-Type'].startswith('text/html')
