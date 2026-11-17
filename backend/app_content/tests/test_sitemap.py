import re

import pytest
from django.core.cache import cache
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from app_content.models import (
    Blueprint,
    Concept,
    DebugGuide,
    Entry,
    ErrorMessage,
    Subtopic,
    Topic,
)

BASE = 'http://testserver'

STATIC_PATHS = [
    '/',
    '/befehle',
    '/grundlagen',
    '/anleitungen',
    '/fehler',
    '/ki-coding',
    '/begriffe',
    '/neu',
    '/faq',
    '/vscode-theme',
]


def sitemap_paths(client: Client, **headers: str) -> list[str]:
    response = client.get('/sitemap.xml', headers=headers)
    assert response.status_code == 200
    locations = re.findall(r'<loc>(.*?)</loc>', response.content.decode())
    return [location.removeprefix(BASE) for location in locations]


def test_sitemap_is_xml(db: None, client: Client) -> None:
    response = client.get('/sitemap.xml')
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/xml'
    assert b'<urlset' in response.content


def test_sitemap_without_content_lists_only_static_pages(db: None, client: Client) -> None:
    assert sitemap_paths(client) == STATIC_PATHS


def test_sitemap_uses_full_urls_of_the_request_host(db: None, client: Client) -> None:
    content = client.get('/sitemap.xml').content.decode()
    assert '<loc>http://testserver/</loc>' in content


def test_sitemap_uses_https_behind_the_proxy(db: None, client: Client) -> None:
    headers = {'Host': 'testserver', 'X-Forwarded-Proto': 'https'}
    content = client.get('/sitemap.xml', headers=headers).content.decode()
    assert '<loc>https://testserver/befehle</loc>' in content
    assert '<loc>http://' not in content


def test_sitemap_lists_entry_with_topic_and_subtopic_pages(client: Client, entry: Entry) -> None:
    paths = sitemap_paths(client)
    assert '/befehle/python' in paths
    assert '/befehle/python/schleifen' in paths
    assert '/befehle/python/schleifen/for-schleife' in paths


def test_sitemap_lists_concept_with_topic_and_subtopic_pages(
    client: Client, concept: Concept
) -> None:
    paths = sitemap_paths(client)
    assert '/grundlagen/python' in paths
    assert '/grundlagen/python/schleifen' in paths
    assert '/grundlagen/python/schleifen/for-schleife' in paths


def test_sitemap_lists_blueprint_with_topic_page(client: Client, blueprint: Blueprint) -> None:
    paths = sitemap_paths(client)
    assert '/anleitungen/python' in paths
    assert '/anleitungen/python/django-projekt-anlegen' in paths


def test_sitemap_lists_error_with_topic_page(client: Client, error_message: ErrorMessage) -> None:
    paths = sitemap_paths(client)
    assert '/fehler/python' in paths
    assert '/fehler/python/module-not-found' in paths


def test_sitemap_lists_general_debug_guide(client: Client, debug_guide: DebugGuide) -> None:
    assert '/fehler/debuggen/vorgehen' in sitemap_paths(client)


def test_sitemap_lists_topic_page_for_topic_debug_guide(
    client: Client, topic_guide: DebugGuide
) -> None:
    paths = sitemap_paths(client)
    assert '/fehler/python' in paths
    assert not any('python-debuggen' in path for path in paths)


def test_sitemap_lists_topic_only_in_areas_with_content(client: Client, entry: Entry) -> None:
    paths = sitemap_paths(client)
    assert '/grundlagen/python' not in paths
    assert '/anleitungen/python' not in paths
    assert '/fehler/python' not in paths


def test_sitemap_skips_subtopic_without_items(client: Client, entry: Entry, topic: Topic) -> None:
    Subtopic.objects.create(topic=topic, slug='leer', name_de='Leer')
    assert '/befehle/python/leer' not in sitemap_paths(client)


def test_sitemap_lists_each_path_once(
    client: Client,
    entry: Entry,
    os_entry: Entry,
    error_message: ErrorMessage,
    topic_guide: DebugGuide,
) -> None:
    paths = sitemap_paths(client)
    assert len(paths) == len(set(paths))
    assert '/befehle/python/schleifen/venv-aktivieren' in paths


def test_sitemap_lists_ai_topics_under_ai_coding(client: Client, ai_subtopic: Subtopic) -> None:
    Entry.objects.create(
        subtopic=ai_subtopic, slug='init', title_de='Init', description_de='x', language='terminal'
    )
    Blueprint.objects.create(
        topic=ai_subtopic.topic, slug='einrichten', title_de='Einrichten', summary_de='x'
    )
    paths = sitemap_paths(client)
    assert '/ki-coding/befehle/claude-code/start/init' in paths
    assert '/ki-coding/anleitungen/claude-code/einrichten' in paths
    assert not any(path.startswith('/befehle/claude-code') for path in paths)


def test_sitemap_keeps_general_and_ai_content_apart(
    client: Client, entry: Entry, ai_subtopic: Subtopic
) -> None:
    Concept.objects.create(
        subtopic=ai_subtopic, slug='kontext', title_de='Kontext', summary_de='x', language='python'
    )
    paths = sitemap_paths(client)
    assert '/befehle/python/schleifen/for-schleife' in paths
    assert '/ki-coding/grundlagen/claude-code/start/kontext' in paths


def test_sitemap_hides_private_pages(client: Client, entry: Entry) -> None:
    paths = sitemap_paths(client)
    for private in ('/profil', '/einstellungen', '/anfrage', '/passwort-zuruecksetzen'):
        assert private not in paths
    assert not any(path.startswith('/api') for path in paths)


def test_sitemap_is_the_same_in_every_language(
    client: Client, entry: Entry, concept: Concept
) -> None:
    german = sitemap_paths(client)
    assert sitemap_paths(client, **{'Accept-Language': 'en'}) == german


def count_sitemap_queries(client: Client) -> int:
    cache.clear()
    with CaptureQueriesContext(connection) as queries:
        client.get('/sitemap.xml')
    return len(queries)


def test_sitemap_query_count_does_not_grow_with_content(
    client: Client,
    entry: Entry,
    concept: Concept,
    blueprint: Blueprint,
    error_message: ErrorMessage,
    debug_guide: DebugGuide,
    topic_guide: DebugGuide,
    request: pytest.FixtureRequest,
) -> None:
    few = count_sitemap_queries(client)
    request.getfixturevalue('os_entry')
    ai_subtopic = request.getfixturevalue('ai_subtopic')
    Concept.objects.create(subtopic=ai_subtopic, slug='kontext', language='python')
    Blueprint.objects.create(topic=ai_subtopic.topic, slug='einrichten')
    ErrorMessage.objects.create(topic=ai_subtopic.topic, slug='kein-zugriff')
    DebugGuide.objects.create(slug='logs-lesen', label_de='Logs')
    assert count_sitemap_queries(client) == few <= 15


def test_sitemap_is_cached(client: Client, entry: Entry, concept: Concept) -> None:
    first = sitemap_paths(client)
    concept.delete()
    assert sitemap_paths(client) == first
    assert 'max-age=3600' in client.get('/sitemap.xml')['Cache-Control']


def test_sitemap_cache_needs_no_query(
    client: Client, entry: Entry, django_assert_num_queries
) -> None:
    client.get('/sitemap.xml')
    with django_assert_num_queries(0):
        client.get('/sitemap.xml')
