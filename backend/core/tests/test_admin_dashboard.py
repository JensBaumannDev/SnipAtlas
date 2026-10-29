import re

import pytest
from django.contrib.auth.models import Permission
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import Client
from django.urls import reverse

from app_accounts.models import User

pytestmark = pytest.mark.django_db

INDEX_URL = reverse('admin:index')
SCRIPT = 'snipatlas/admin-sections.js'
ACTION = 'class="snipatlas-section__action"'
PRIMARY = 'class="snipatlas-section__action snipatlas-section__action--primary"'
SECTION_KEYS = ['structure', 'commands', 'guides', 'errors', 'terms', 'people']


@pytest.fixture
def superuser_client(client: Client) -> Client:
    superuser = User.objects.create_superuser('root@example.com', 'Kaffee-Tasse-2026!')
    client.force_login(superuser)
    return client


def index_html(client: Client, language: str = 'de') -> str:
    return client.get(INDEX_URL, HTTP_ACCEPT_LANGUAGE=language).content.decode()


def section_html(content: str, key: str) -> str:
    match = re.search(
        rf'<details class="snipatlas-section" data-section="{key}">(.*?)</details>', content, re.S
    )
    assert match, key
    return match.group(1)


# Sections
def test_index_shows_one_collapsed_section_per_area(superuser_client: Client) -> None:
    content = index_html(superuser_client)
    assert re.findall(r'<details class="snipatlas-section" data-section="(\w+)">', content) == (
        SECTION_KEYS
    )
    assert '<details class="snipatlas-section" data-section="structure" open' not in content


@pytest.mark.parametrize(
    ('language', 'name'), [('de', 'Befehle &amp; Grundlagen'), ('en', 'Commands &amp; concepts')]
)
def test_section_summary_shows_only_the_name(
    superuser_client: Client, language: str, name: str
) -> None:
    section = section_html(index_html(superuser_client, language), 'commands')
    assert f'<span class="snipatlas-section__name" id="section-commands">{name}</span>' in section
    assert 'snipatlas-section__count' not in section


def test_section_lists_its_models_with_links(superuser_client: Client) -> None:
    section = section_html(index_html(superuser_client), 'commands')
    assert '<table class="snipatlas-section__models" aria-labelledby="section-commands">' in section
    assert f'href="{reverse("admin:app_content_entry_changelist")}">Befehle</a>' in section
    assert f'href="{reverse("admin:app_content_entry_add")}" {PRIMARY}>Hinzufügen</a>' in section
    assert (
        f'href="{reverse("admin:app_content_concept_changelist")}" {ACTION}>Ändern</a>' in section
    )
    assert reverse('admin:app_content_blueprint_changelist') not in section
    assert 'addlink' not in section
    assert 'changelink' not in section


def test_section_shows_view_link_for_read_only_model(client: Client) -> None:
    staff = User.objects.create_user('reader@example.com', 'Kaffee-Tasse-2026!', is_staff=True)
    staff.user_permissions.set(Permission.objects.filter(codename='view_entry'))
    client.force_login(staff)
    section = section_html(index_html(client), 'commands')
    assert f'href="{reverse("admin:app_content_entry_changelist")}" {ACTION}>Ansehen</a>' in section
    assert 'snipatlas-section__action--primary' not in section


def test_staff_sees_only_allowed_sections(staff_client: Client) -> None:
    content = index_html(staff_client)
    assert re.findall(r'data-section="(\w+)"', content) == ['people']


def test_staff_without_rights_sees_no_sections(client: Client) -> None:
    staff = User.objects.create_user('plain@example.com', 'Kaffee-Tasse-2026!', is_staff=True)
    client.force_login(staff)
    content = index_html(client)
    assert 'snipatlas-section' not in content
    assert 'nicht die nötigen Rechte' in content


def test_index_keeps_recent_actions(superuser_client: Client) -> None:
    assert 'id="recent-actions-module"' in index_html(superuser_client)


# Script
def test_index_loads_section_script(superuser_client: Client) -> None:
    assert f'<script src="{static(SCRIPT)}" defer></script>' in index_html(superuser_client)


def test_other_pages_do_not_load_section_script(superuser_client: Client) -> None:
    response = superuser_client.get(reverse('admin:app_content_entry_changelist'))
    assert static(SCRIPT) not in response.content.decode()


def test_section_script_is_found() -> None:
    assert finders.find(SCRIPT) is not None
