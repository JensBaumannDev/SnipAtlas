import pytest
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db

INDEX_URL = reverse('admin:index')
LOGIN_URL = reverse('admin:login')
STYLESHEET = 'snipatlas/admin.css'
LOGO = 'snipatlas/logo.svg'
FONT = 'snipatlas/fonts/ibm-plex-sans-latin-wght-normal.woff2'
FAVICON = 'snipatlas/favicon.svg'
FAVICON_TAG = f'<link rel="icon" type="image/svg+xml" href="{static(FAVICON)}">'


# Branding
def test_admin_header_shows_snipatlas(staff_client: Client) -> None:
    response = staff_client.get(INDEX_URL)
    assert response.status_code == 200
    assert '<span class="snipatlas-logo" aria-hidden="true"></span>SnipAtlas Admin' in (
        response.content.decode()
    )


def test_admin_title_shows_snipatlas(staff_client: Client) -> None:
    content = staff_client.get(INDEX_URL).content.decode()
    assert '| SnipAtlas Admin</title>' in content
    assert 'Django' not in content


def test_admin_has_snipatlas_favicon(staff_client: Client) -> None:
    assert FAVICON_TAG in staff_client.get(INDEX_URL).content.decode()


def test_admin_login_has_snipatlas_favicon(client: Client) -> None:
    assert FAVICON_TAG in client.get(LOGIN_URL).content.decode()


def test_admin_login_shows_snipatlas_and_theme_toggle(client: Client) -> None:
    content = client.get(LOGIN_URL).content.decode()
    assert 'SnipAtlas Admin' in content
    assert 'theme-toggle' in content


# Stylesheet
def test_admin_loads_snipatlas_stylesheet(staff_client: Client) -> None:
    content = staff_client.get(INDEX_URL).content.decode()
    assert f'<link rel="stylesheet" href="{static(STYLESHEET)}">' in content
    assert content.index(static('admin/css/dark_mode.css')) < content.index(static(STYLESHEET))


def test_admin_login_loads_snipatlas_stylesheet(client: Client) -> None:
    assert static(STYLESHEET) in client.get(LOGIN_URL).content.decode()


@pytest.mark.parametrize('path', [STYLESHEET, LOGO, FONT, FAVICON])
def test_snipatlas_static_file_is_found(path: str) -> None:
    assert finders.find(path) is not None
