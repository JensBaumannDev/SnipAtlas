import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.settings import api_settings
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle

from core.throttling import AuthRateThrottle


@pytest.fixture
def one_per_hour(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(AnonRateThrottle.THROTTLE_RATES, 'anon', '1/hour')


@pytest.fixture
def behind_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_settings, 'NUM_PROXIES', 1)


def get_groups(client: APIClient, forwarded_for: str | None = None) -> int:
    headers = {'X-Forwarded-For': forwarded_for} if forwarded_for else {}
    return client.get(reverse('group-list'), headers=headers).status_code


def test_num_proxies_defaults_to_zero() -> None:
    assert settings.REST_FRAMEWORK['NUM_PROXIES'] == 0


@pytest.mark.django_db
@pytest.mark.usefixtures('one_per_hour')
def test_forwarded_for_is_ignored_without_proxy(api_client: APIClient) -> None:
    assert get_groups(api_client, '203.0.113.1') == 200
    assert get_groups(api_client, '203.0.113.2') == 429


@pytest.mark.django_db
@pytest.mark.usefixtures('one_per_hour', 'behind_proxy')
def test_forwarded_for_counts_each_visitor_behind_proxy(api_client: APIClient) -> None:
    assert get_groups(api_client, '203.0.113.1') == 200
    assert get_groups(api_client, '203.0.113.2') == 200
    assert get_groups(api_client, '203.0.113.1') == 429


@pytest.mark.django_db
@pytest.mark.usefixtures('one_per_hour', 'behind_proxy')
def test_forwarded_for_uses_address_added_by_proxy(api_client: APIClient) -> None:
    assert get_groups(api_client, '198.51.100.7, 203.0.113.1') == 200
    assert get_groups(api_client, '198.51.100.8, 203.0.113.1') == 429


@pytest.mark.django_db
@pytest.mark.usefixtures('one_per_hour', 'behind_proxy')
def test_missing_forwarded_for_falls_back_to_remote_address(api_client: APIClient) -> None:
    assert get_groups(api_client) == 200
    assert get_groups(api_client) == 429


@pytest.mark.django_db
@pytest.mark.usefixtures('behind_proxy')
def test_auth_throttle_counts_each_visitor_behind_proxy(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(AuthRateThrottle.THROTTLE_RATES, 'auth', '1/minute')
    url = reverse('auth-login')
    body = {'email': 'ada@example.com', 'password': 'wrong'}
    first = api_client.post(url, body, format='json', headers={'X-Forwarded-For': '203.0.113.1'})
    other = api_client.post(url, body, format='json', headers={'X-Forwarded-For': '203.0.113.2'})
    again = api_client.post(url, body, format='json', headers={'X-Forwarded-For': '203.0.113.1'})
    assert first.status_code != 429
    assert other.status_code != 429
    assert again.status_code == 429
