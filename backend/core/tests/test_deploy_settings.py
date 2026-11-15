import importlib
from collections.abc import Callable, Iterator

import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.db import connection
from django.test import Client, override_settings
from django.urls import clear_url_caches

import core.urls
from core import settings as project_settings
from core.security import admin_path

SERVER = {
    'DEBUG': False,
    'SECRET_KEY': 'k3F9pQz7Lm2Xv8Rt5Wy1Bn6Hc4Jd0Gs-Ae7Uf2Ki9Op3Lq8Zx5Cv1Bm6Nh4Tr0',
    'ALLOWED_HOSTS': ['snipatlas.jensbaumann.com'],
    'SESSION_COOKIE_SECURE': True,
    'CSRF_COOKIE_SECURE': True,
    'SECURE_HSTS_SECONDS': 60 * 60 * 24 * 365,
    'MAILERS': {'default': {'BACKEND': 'django.core.mail.backends.smtp.EmailBackend'}},
}


@pytest.fixture
def use_admin_path() -> Iterator[Callable[[str], None]]:
    def use(path: str) -> None:
        settings.ADMIN_PATH = path
        importlib.reload(core.urls)
        clear_url_caches()

    original = settings.ADMIN_PATH
    yield use
    use(original)


# Admin path


@pytest.mark.parametrize('value', ['admin/', 'verwaltung/', 'team-7f3k2/', 'a/'])
def test_admin_path_accepts_one_lowercase_segment(value: str) -> None:
    assert admin_path(value) == value


@pytest.mark.parametrize(
    'value',
    ['', '/', 'admin', '/admin/', 'Admin/', 'ad min/', 'a/b/', '-admin/', 'api/', 'static/'],
)
def test_admin_path_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ImproperlyConfigured):
        admin_path(value)


@pytest.mark.django_db
def test_admin_is_served_at_the_configured_path(
    use_admin_path: Callable[[str], None], client: Client
) -> None:
    use_admin_path('team-7f3k2/')
    assert client.get('/team-7f3k2/login/').status_code == 200
    assert client.get('/admin/login/').status_code == 404


@pytest.mark.django_db
def test_admin_moves_back_to_admin(use_admin_path: Callable[[str], None], client: Client) -> None:
    use_admin_path('team-7f3k2/')
    use_admin_path('admin/')
    assert client.get('/admin/login/').status_code == 200
    assert client.get('/team-7f3k2/login/').status_code == 404


# Shared cache


def test_cache_is_shared_through_the_database() -> None:
    backend = project_settings.CACHES['default']['BACKEND']
    assert backend == 'django.core.cache.backends.db.DatabaseCache'


@pytest.mark.django_db
def test_cache_values_are_stored_in_the_database() -> None:
    with override_settings(CACHES=project_settings.CACHES):
        cache.set('throttle_test', [1, 2, 3])
        table = project_settings.CACHES['default']['LOCATION']
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            assert cursor.fetchone()[0] == 1
        assert cache.get('throttle_test') == [1, 2, 3]


# HTTPS behind the proxy


def test_hsts_covers_subdomains_without_preload() -> None:
    assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
    assert settings.SECURE_HSTS_PRELOAD is False


@pytest.mark.django_db
def test_proxy_https_header_marks_request_secure(client: Client) -> None:
    with override_settings(**SERVER):
        response = client.get(
            '/api/auth/csrf/',
            headers={'X-Forwarded-Proto': 'https'},
            SERVER_NAME=SERVER['ALLOWED_HOSTS'][0],
        )
    assert response['Strict-Transport-Security'] == 'max-age=31536000; includeSubDomains'


@pytest.mark.django_db
def test_plain_http_gets_no_hsts(client: Client) -> None:
    with override_settings(**SERVER):
        response = client.get('/api/auth/csrf/', SERVER_NAME=SERVER['ALLOWED_HOSTS'][0])
    assert 'Strict-Transport-Security' not in response


def test_deploy_check_has_no_warnings_with_server_settings(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with override_settings(**SERVER):
        call_command('check', deploy=True, fail_level='WARNING')
    assert 'no issues' in capsys.readouterr().out


def test_deploy_check_warns_without_hsts() -> None:
    with override_settings(**{**SERVER, 'SECURE_HSTS_SECONDS': 0}):
        with pytest.raises(SystemCheckError, match='W004'):
            call_command('check', deploy=True, fail_level='WARNING')
