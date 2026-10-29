import pytest
from django.apps import apps
from django.contrib import admin
from django.test import Client
from django.urls import reverse
from django.utils import translation

from app_accounts.models import User
from core import admin as core_admin

pytestmark = pytest.mark.django_db

INDEX_URL = reverse('admin:index')

SECTIONS = {
    'de': [
        ('Aufbau der Seite', ['Themengruppen', 'Themen']),
        ('Befehle & Grundlagen', ['Befehle', 'Grundlagen']),
        ('Anleitungen', ['Anleitungen', 'Anleitungsschritte']),
        ('Fehler', ['Fehlermeldungen', 'Debug-Anleitungen']),
        ('Begriffe & Neues', ['Begriffe', 'Neuigkeiten']),
        ('Nutzer & Anfragen', ['Nutzer', 'Anfragen', 'Berechtigungsgruppen']),
    ],
    'en': [
        ('Site structure', ['Topic groups', 'Topics']),
        ('Commands & concepts', ['Commands', 'Concepts']),
        ('Guides', ['Guides', 'Guide steps']),
        ('Errors', ['Error messages', 'Debug guides']),
        ('Terms & news', ['Terms', 'News']),
        ('Users & requests', ['Users', 'Requests', 'Permission groups']),
    ],
}

MODEL_NAMES = [
    ('app_accounts.user', 'Nutzer', 'Nutzer', 'user', 'users'),
    ('app_accounts.favorite', 'Favorit', 'Favoriten', 'favorite', 'favorites'),
    (
        'app_accounts.completedstep',
        'Erledigter Schritt',
        'Erledigte Schritte',
        'completed step',
        'completed steps',
    ),
    ('app_content.group', 'Themengruppe', 'Themengruppen', 'topic group', 'topic groups'),
    ('app_content.topic', 'Thema', 'Themen', 'topic', 'topics'),
    ('app_content.subtopic', 'Unterordner', 'Unterordner', 'subtopic', 'subtopics'),
    ('app_content.entry', 'Befehl', 'Befehle', 'command', 'commands'),
    ('app_content.concept', 'Grundlage', 'Grundlagen', 'concept', 'concepts'),
    (
        'app_content.errormessage',
        'Fehlermeldung',
        'Fehlermeldungen',
        'error message',
        'error messages',
    ),
    (
        'app_content.errorstep',
        'Lösungsschritt',
        'Lösungsschritte',
        'solution step',
        'solution steps',
    ),
    (
        'app_content.debugguide',
        'Debug-Anleitung',
        'Debug-Anleitungen',
        'debug guide',
        'debug guides',
    ),
    ('app_content.debugguidestep', 'Schritt', 'Schritte', 'step', 'steps'),
    ('app_content.blueprint', 'Anleitung', 'Anleitungen', 'guide', 'guides'),
    (
        'app_content.blueprintstep',
        'Anleitungsschritt',
        'Anleitungsschritte',
        'guide step',
        'guide steps',
    ),
    ('app_content.blueprintcode', 'Code-Block', 'Code-Blöcke', 'code block', 'code blocks'),
    ('app_content.glossaryterm', 'Begriff', 'Begriffe', 'term', 'terms'),
    ('app_content.glossaryalias', 'Anderer Name', 'Andere Namen', 'other name', 'other names'),
    ('app_content.news', 'Neuigkeit', 'Neuigkeiten', 'news item', 'news'),
    ('app_feedback.suggestion', 'Anfrage', 'Anfragen', 'request', 'requests'),
]

APP_NAMES = [
    ('app_accounts', 'Konten', 'Accounts'),
    ('app_content', 'Inhalte', 'Content'),
    ('app_feedback', 'Anfragen', 'Requests'),
]


@pytest.fixture
def superuser_client(client: Client) -> Client:
    superuser = User.objects.create_superuser('root@example.com', 'Kaffee-Tasse-2026!')
    client.force_login(superuser)
    return client


def section_names(app_list: list[dict]) -> list[tuple[str, list[str]]]:
    return [(str(app['name']), [str(model['name']) for model in app['models']]) for app in app_list]


def get_index(client: Client, language: str) -> list[dict]:
    return client.get(INDEX_URL, HTTP_ACCEPT_LANGUAGE=language).context['app_list']


# Names
@pytest.mark.parametrize(('label', 'singular', 'plural', 'en_singular', 'en_plural'), MODEL_NAMES)
def test_model_name_is_german_and_english(
    label: str, singular: str, plural: str, en_singular: str, en_plural: str
) -> None:
    meta = apps.get_model(label)._meta
    with translation.override('de'):
        assert (str(meta.verbose_name), str(meta.verbose_name_plural)) == (singular, plural)
    with translation.override('en'):
        assert (str(meta.verbose_name), str(meta.verbose_name_plural)) == (en_singular, en_plural)


@pytest.mark.parametrize(('label', 'name', 'en_name'), APP_NAMES)
def test_app_name_is_german_and_english(label: str, name: str, en_name: str) -> None:
    verbose_name = apps.get_app_config(label).verbose_name
    with translation.override('de'):
        assert str(verbose_name) == name
    with translation.override('en'):
        assert str(verbose_name) == en_name


def test_admin_site_is_snipatlas_site() -> None:
    assert isinstance(admin.site, core_admin.SnipAtlasAdminSite)
    assert admin.site.site_header == 'SnipAtlas Admin'
    assert admin.site.site_title == 'SnipAtlas Admin'


# Sections
@pytest.mark.parametrize('language', ['de', 'en'])
def test_index_groups_models_into_sections(superuser_client: Client, language: str) -> None:
    assert section_names(get_index(superuser_client, language)) == SECTIONS[language]


def test_index_falls_back_to_german_for_unknown_language(superuser_client: Client) -> None:
    assert section_names(get_index(superuser_client, 'fr')) == SECTIONS['de']


@pytest.mark.parametrize('language', ['de', 'en'])
def test_index_shows_section_headings(superuser_client: Client, language: str) -> None:
    response = superuser_client.get(INDEX_URL, HTTP_ACCEPT_LANGUAGE=language)
    content = response.content.decode()
    for name, _ in SECTIONS[language]:
        assert f'">{name.replace("&", "&amp;")}</span>' in content
    assert 'App_' not in content


def test_section_links_to_its_first_model(superuser_client: Client) -> None:
    app_list = get_index(superuser_client, 'de')
    errors = next(app for app in app_list if app['name'] == 'Fehler')
    assert errors['app_url'] == reverse('admin:app_content_errormessage_changelist')
    assert errors['app_label'] == 'errors'


def test_sidebar_uses_sections(superuser_client: Client) -> None:
    response = superuser_client.get(
        reverse('admin:app_content_entry_changelist'), HTTP_ACCEPT_LANGUAGE='en'
    )
    assert section_names(response.context['available_apps']) == SECTIONS['en']


def test_staff_sees_only_sections_with_allowed_models(staff_client: Client) -> None:
    assert section_names(get_index(staff_client, 'de')) == [('Nutzer & Anfragen', ['Nutzer'])]


def test_staff_without_rights_sees_no_sections(client: Client) -> None:
    staff = User.objects.create_user('plain@example.com', 'Kaffee-Tasse-2026!', is_staff=True)
    client.force_login(staff)
    response = client.get(INDEX_URL)
    assert response.context['app_list'] == []
    assert 'nicht die nötigen Rechte' in response.content.decode()


@pytest.mark.parametrize(('language', 'name'), [('de', 'Weitere'), ('en', 'More')])
def test_unlisted_model_lands_in_last_section(
    superuser_client: Client, monkeypatch: pytest.MonkeyPatch, language: str, name: str
) -> None:
    monkeypatch.setattr(core_admin, 'SECTIONS', core_admin.SECTIONS[1:])
    last = section_names(get_index(superuser_client, language))[-1]
    assert last == (name, sorted(SECTIONS[language][0][1]))


def test_app_page_keeps_app_grouping(superuser_client: Client) -> None:
    response = superuser_client.get(reverse('admin:app_list', args=['app_content']))
    assert response.status_code == 200
    assert [str(app['name']) for app in response.context['app_list']] == ['Inhalte']


def test_guest_is_sent_to_login(client: Client) -> None:
    response = client.get(INDEX_URL)
    assert response.status_code == 302
    assert response.url.startswith(reverse('admin:login'))


def test_every_registered_model_is_in_a_section() -> None:
    listed = {label for _, _, labels in core_admin.SECTIONS for label in labels}
    registered = {model._meta.label_lower for model in admin.site._registry}
    assert registered == listed
