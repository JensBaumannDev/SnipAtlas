import pytest
from django.db.models import Model
from django.forms.models import model_to_dict
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle

from app_accounts.models import User
from app_content.models import (
    Concept,
    DebugGuide,
    Entry,
    ErrorMessage,
    Group,
    Subtopic,
    Topic,
)

pytestmark = pytest.mark.django_db

WRITE_METHODS = ['post', 'put', 'patch', 'delete']
CONTENT = ['entry', 'concept']
CONTENT_MODELS = {'entry': Entry, 'concept': Concept}
BROKEN_TOPICS = [
    'cobol',
    'PYTHON',
    'schleifen',
    "python' OR '1'='1",
    'python%',
    'python\n',
    'py\x00thon',
    'x' * 5000,
]


# Groups
def test_groups_list_is_public(api_client: APIClient, subtopic: Subtopic) -> None:
    response = api_client.get(reverse('group-list'))
    assert response.status_code == 200
    assert response.json() == [
        {
            'slug': 'backend',
            'name': 'Backend',
            'topics': [
                {
                    'slug': 'python',
                    'name': 'Python',
                    'color': '#3776ab',
                    'subtopics': [{'slug': 'schleifen', 'name': 'Schleifen'}],
                }
            ],
        }
    ]


def test_groups_list_keeps_order(api_client: APIClient, group: Group, topic: Topic) -> None:
    Group.objects.create(slug='frontend', name_de='Frontend', position=-1)
    Topic.objects.create(group=group, slug='django', name_de='Django', position=-1)
    data = api_client.get(reverse('group-list')).json()
    assert [item['slug'] for item in data] == ['frontend', 'backend']
    assert [item['slug'] for item in data[1]['topics']] == ['django', 'python']


def test_groups_list_uses_accept_language(api_client: APIClient, subtopic: Subtopic) -> None:
    data = api_client.get(reverse('group-list'), HTTP_ACCEPT_LANGUAGE='en').json()
    assert data[0]['topics'][0]['subtopics'][0]['name'] == 'Loops'


def test_groups_list_falls_back_to_german(api_client: APIClient) -> None:
    Group.objects.create(slug='tools', name_de='Werkzeuge')
    data = api_client.get(reverse('group-list'), HTTP_ACCEPT_LANGUAGE='en').json()
    assert data[0]['name'] == 'Werkzeuge'


def test_groups_list_is_empty_without_groups(api_client: APIClient, db: None) -> None:
    assert api_client.get(reverse('group-list')).json() == []


def test_groups_list_uses_german_for_unknown_language(
    api_client: APIClient, subtopic: Subtopic
) -> None:
    data = api_client.get(reverse('group-list'), HTTP_ACCEPT_LANGUAGE='fr').json()
    assert data[0]['topics'][0]['subtopics'][0]['name'] == 'Schleifen'


def test_groups_list_loads_in_three_queries(
    api_client: APIClient,
    group: Group,
    subtopic: Subtopic,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    frontend = Group.objects.create(slug='frontend', name_de='Frontend')
    css = Topic.objects.create(group=frontend, slug='css', name_de='CSS', color='#1572b6')
    Subtopic.objects.create(topic=css, slug='grid', name_de='Grid')
    with django_assert_num_queries(3):
        api_client.get(reverse('group-list'))


def test_groups_list_works_with_token(api_client: APIClient, user: User, group: Group) -> None:
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    assert api_client.get(reverse('group-list')).status_code == 200


def test_groups_list_rejects_invalid_token(api_client: APIClient, group: Group) -> None:
    api_client.credentials(HTTP_AUTHORIZATION='Token invalid')
    response = api_client.get(reverse('group-list'))
    assert response.status_code == 401
    assert response.json() == {'code': 'authentication_failed'}


def test_groups_list_is_throttled(
    api_client: APIClient, group: Group, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(AnonRateThrottle.THROTTLE_RATES, 'anon', '1/hour')
    api_client.get(reverse('group-list'))
    response = api_client.get(reverse('group-list'))
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'


@pytest.mark.parametrize('method', WRITE_METHODS)
def test_groups_list_rejects_writes(api_client: APIClient, group: Group, method: str) -> None:
    response = getattr(api_client, method)(reverse('group-list'), {'slug': 'tools'})
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert Group.objects.count() == 1


# Topic
def test_topic_detail_is_public(api_client: APIClient, subtopic: Subtopic) -> None:
    response = api_client.get(reverse('topic-detail', args=['python']))
    assert response.status_code == 200
    assert response.json() == {
        'slug': 'python',
        'name': 'Python',
        'color': '#3776ab',
        'subtopics': [{'slug': 'schleifen', 'name': 'Schleifen'}],
    }


def test_topic_detail_uses_accept_language(api_client: APIClient, subtopic: Subtopic) -> None:
    url = reverse('topic-detail', args=['python'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE='en').json()
    assert data['subtopics'] == [{'slug': 'schleifen', 'name': 'Loops'}]


def test_topic_detail_unknown_slug_returns_404(api_client: APIClient, topic: Topic) -> None:
    response = api_client.get(reverse('topic-detail', args=['cobol']))
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}


def test_topic_detail_slug_is_case_sensitive(api_client: APIClient, topic: Topic) -> None:
    response = api_client.get(reverse('topic-detail', args=['PYTHON']))
    assert response.status_code == 404


def test_topic_detail_loads_in_two_queries(
    api_client: APIClient, subtopic: Subtopic, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(2):
        api_client.get(reverse('topic-detail', args=['python']))


@pytest.mark.parametrize('method', WRITE_METHODS)
def test_topic_detail_rejects_writes(api_client: APIClient, topic: Topic, method: str) -> None:
    url = reverse('topic-detail', args=['python'])
    response = getattr(api_client, method)(url, {'name': 'Hacked'})
    topic.refresh_from_db()
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert topic.name == 'Python'


# Entries
ENTRY_JSON = {
    'slug': 'for-schleife',
    'topic': 'python',
    'subtopic': 'schleifen',
    'title': 'For-Schleife',
    'description': 'Wiederholt Code für jedes Element.',
    'language': 'python',
    'code': 'for item in items: print(item)',
}


def test_entries_list_is_public(api_client: APIClient, entry: Entry) -> None:
    response = api_client.get(reverse('entry-list'))
    assert response.status_code == 200
    assert response.json() == [ENTRY_JSON]


def test_entries_list_splits_code_by_os(api_client: APIClient, os_entry: Entry) -> None:
    data = api_client.get(reverse('entry-list')).json()
    assert data[0]['code'] == {
        'win': r'.venv\Scripts\activate',
        'unix': 'source .venv/bin/activate',
    }


def test_entry_detail_is_public(api_client: APIClient, entry: Entry) -> None:
    response = api_client.get(reverse('entry-detail', args=['for-schleife']))
    assert response.status_code == 200
    assert response.json() == ENTRY_JSON


def test_entry_detail_uses_accept_language(api_client: APIClient, entry: Entry) -> None:
    url = reverse('entry-detail', args=['for-schleife'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE='en').json()
    assert data['title'] == 'For loop'
    assert data['description'] == 'Repeats code for each item.'
    assert data['code'] == 'for item in items: print(item)'


def test_entry_detail_falls_back_to_german_code(api_client: APIClient, os_entry: Entry) -> None:
    os_entry.code_en = r'.venv\Scripts\Activate.ps1'
    os_entry.save()
    url = reverse('entry-detail', args=['venv-aktivieren'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE='en').json()
    assert data['title'] == 'venv aktivieren'
    assert data['code'] == {
        'win': r'.venv\Scripts\Activate.ps1',
        'unix': 'source .venv/bin/activate',
    }


# Concepts
CONCEPT_JSON = {
    'slug': 'for-schleife',
    'topic': 'python',
    'subtopic': 'schleifen',
    'title': 'Die for-Schleife',
    'summary': 'Läuft über alle Elemente.',
    'explanation': 'Python nimmt nacheinander jedes Element.',
    'language': 'python',
    'code': 'for item in items: print(item)',
    'note': 'Nicht die Liste in der Schleife ändern.',
}


def test_concepts_list_is_public(api_client: APIClient, concept: Concept) -> None:
    response = api_client.get(reverse('concept-list'))
    assert response.status_code == 200
    assert response.json() == [CONCEPT_JSON]


def test_concept_detail_is_public(api_client: APIClient, concept: Concept) -> None:
    response = api_client.get(reverse('concept-detail', args=['for-schleife']))
    assert response.status_code == 200
    assert response.json() == CONCEPT_JSON


def test_concept_without_note_has_empty_note(api_client: APIClient, concept: Concept) -> None:
    concept.note_de = ''
    concept.save()
    data = api_client.get(reverse('concept-detail', args=['for-schleife'])).json()
    assert data['note'] == ''


def test_concept_detail_uses_accept_language(api_client: APIClient, concept: Concept) -> None:
    url = reverse('concept-detail', args=['for-schleife'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE='en').json()
    assert [data['title'], data['summary']] == ['The for loop', 'Runs over all items.']
    assert data['note'] == 'Nicht die Liste in der Schleife ändern.'


# Entries and concepts: filter
def create_item(model: str, subtopic: Subtopic, slug: str, **fields: object) -> Model:
    return CONTENT_MODELS[model].objects.create(
        subtopic=subtopic, slug=slug, title_de=slug, language='python', code_de='pass', **fields
    )


def list_slugs(api_client: APIClient, model: str, **params: str) -> list[str]:
    response = api_client.get(reverse(f'{model}-list'), params)
    assert response.status_code == 200
    return [item['slug'] for item in response.json()]


@pytest.fixture
def git_alltag(group: Group) -> Subtopic:
    git = Topic.objects.create(group=group, slug='git', name_de='Git', position=-1)
    return Subtopic.objects.create(topic=git, slug='alltag', name_de='Alltag')


@pytest.mark.parametrize('model', CONTENT)
def test_content_list_filters_by_topic(
    api_client: APIClient, subtopic: Subtopic, git_alltag: Subtopic, model: str
) -> None:
    create_item(model, subtopic, 'for')
    create_item(model, git_alltag, 'status')
    assert list_slugs(api_client, model, topic='python') == ['for']
    assert list_slugs(api_client, model, topic='git') == ['status']


@pytest.mark.parametrize('model', CONTENT)
@pytest.mark.parametrize('params', [{}, {'topic': ''}, {'page': '2', 'search': 'x'}])
def test_content_list_without_topic_returns_all_in_order(
    api_client: APIClient, subtopic: Subtopic, git_alltag: Subtopic, model: str, params: dict
) -> None:
    create_item(model, subtopic, 'while', position=2)
    create_item(model, subtopic, 'for', position=1)
    create_item(model, git_alltag, 'status', position=9)
    assert list_slugs(api_client, model, **params) == ['status', 'for', 'while']


@pytest.mark.parametrize('model', CONTENT)
@pytest.mark.parametrize('value', BROKEN_TOPICS)
def test_content_list_with_unknown_topic_is_empty(
    api_client: APIClient, subtopic: Subtopic, model: str, value: str
) -> None:
    create_item(model, subtopic, 'for')
    assert list_slugs(api_client, model, topic=value) == []


@pytest.mark.parametrize('model', CONTENT)
def test_content_list_is_empty_without_content(
    api_client: APIClient, subtopic: Subtopic, model: str
) -> None:
    assert list_slugs(api_client, model) == []


@pytest.mark.parametrize('model', CONTENT)
def test_content_list_uses_german_for_unknown_language(
    api_client: APIClient, subtopic: Subtopic, model: str
) -> None:
    create_item(model, subtopic, 'for', title_en='English')
    data = api_client.get(reverse(f'{model}-list'), HTTP_ACCEPT_LANGUAGE='fr').json()
    assert data[0]['title'] == 'for'


@pytest.mark.parametrize('model', CONTENT)
def test_content_list_loads_in_one_query(
    api_client: APIClient,
    subtopic: Subtopic,
    git_alltag: Subtopic,
    model: str,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    create_item(model, subtopic, 'for')
    create_item(model, git_alltag, 'status')
    with django_assert_num_queries(1):
        api_client.get(reverse(f'{model}-list'), {'topic': 'python'})
    with django_assert_num_queries(1):
        api_client.get(reverse(f'{model}-list'))


# Entries and concepts: detail
@pytest.mark.parametrize('model', CONTENT)
@pytest.mark.parametrize('slug', ['cobol', 'FOR-SCHLEIFE', 'for_schleife', 'schleifen'])
def test_content_detail_unknown_slug_returns_404(
    api_client: APIClient, entry: Entry, concept: Concept, model: str, slug: str
) -> None:
    response = api_client.get(reverse(f'{model}-detail', args=[slug]))
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}


@pytest.mark.parametrize(('model', 'other'), [('entry', 'concept'), ('concept', 'entry')])
def test_content_detail_ignores_slug_of_other_area(
    api_client: APIClient, subtopic: Subtopic, model: str, other: str
) -> None:
    create_item(other, subtopic, 'nur-dort')
    response = api_client.get(reverse(f'{model}-detail', args=['nur-dort']))
    assert response.status_code == 404


@pytest.mark.parametrize('fixture', CONTENT)
def test_content_detail_loads_in_one_query(
    api_client: APIClient,
    request: pytest.FixtureRequest,
    fixture: str,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    request.getfixturevalue(fixture)
    with django_assert_num_queries(1):
        api_client.get(reverse(f'{fixture}-detail', args=['for-schleife']))


# Entries and concepts: security
@pytest.mark.parametrize('model', CONTENT)
def test_content_returns_text_unchanged_as_json(
    api_client: APIClient, subtopic: Subtopic, model: str
) -> None:
    script = '<script>alert(1)</script>'
    create_item(model, subtopic, 'xss', title_en=script, code_en=script)
    response = api_client.get(reverse(f'{model}-detail', args=['xss']), HTTP_ACCEPT_LANGUAGE='en')
    assert response['Content-Type'] == 'application/json'
    assert [response.json()['title'], response.json()['code']] == [script, script]


@pytest.mark.parametrize('fixture', CONTENT)
def test_content_understands_browser_language_header(
    api_client: APIClient, request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    url = reverse(f'{fixture}-detail', args=['for-schleife'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9,de;q=0.8').json()
    assert data['title'] == obj.title_en


# Public content: security
AREAS = {
    'entry': ('entry', 'for-schleife'),
    'concept': ('concept', 'for-schleife'),
    'error': ('error_message', 'module-not-found'),
    'debug-guide': ('debug_guide', 'vorgehen'),
}
ROUTES = ['list', 'detail']
HACKED = {'slug': 'neu', 'title': 'Hacked', 'message': 'Hacked', 'code': 'rm -rf /'}


def stored(obj: Model) -> dict:
    return model_to_dict(type(obj).objects.get(pk=obj.pk))


def area_url(request: pytest.FixtureRequest, area: str, route: str = 'detail') -> tuple[Model, str]:
    fixture, slug = AREAS[area]
    obj = request.getfixturevalue(fixture)
    args = [slug] if route == 'detail' else []
    return obj, reverse(f'{area}-{route}', args=args)


@pytest.mark.parametrize('area', AREAS)
@pytest.mark.parametrize('value', ['git', 'py\x00thon'])
def test_detail_ignores_topic_param(
    api_client: APIClient, request: pytest.FixtureRequest, area: str, value: str
) -> None:
    url = area_url(request, area)[1]
    assert api_client.get(url, {'topic': value}).status_code == 200


@pytest.mark.parametrize('area', AREAS)
@pytest.mark.parametrize('route', ROUTES)
def test_public_content_works_with_token(
    api_client: APIClient, user: User, request: pytest.FixtureRequest, area: str, route: str
) -> None:
    url = area_url(request, area, route)[1]
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    assert api_client.get(url).status_code == 200


@pytest.mark.parametrize('area', AREAS)
@pytest.mark.parametrize('route', ROUTES)
def test_public_content_rejects_invalid_token(
    api_client: APIClient, request: pytest.FixtureRequest, area: str, route: str
) -> None:
    url = area_url(request, area, route)[1]
    api_client.credentials(HTTP_AUTHORIZATION='Token invalid')
    response = api_client.get(url)
    assert response.status_code == 401
    assert response.json() == {'code': 'authentication_failed'}


@pytest.mark.parametrize('area', AREAS)
def test_public_content_rejects_token_of_inactive_user(
    api_client: APIClient, user: User, request: pytest.FixtureRequest, area: str
) -> None:
    url = area_url(request, area, 'list')[1]
    token = Token.objects.create(user=user)
    User.objects.filter(pk=user.pk).update(is_active=False)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    response = api_client.get(url)
    assert response.status_code == 401
    assert response.json() == {'code': 'authentication_failed'}


@pytest.mark.parametrize('area', AREAS)
@pytest.mark.parametrize('route', ROUTES)
def test_public_content_is_throttled(
    api_client: APIClient,
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    area: str,
    route: str,
) -> None:
    url = area_url(request, area, route)[1]
    monkeypatch.setitem(AnonRateThrottle.THROTTLE_RATES, 'anon', '1/hour')
    api_client.get(url)
    response = api_client.get(url)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'


@pytest.mark.parametrize('area', AREAS)
@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('method', WRITE_METHODS)
def test_public_content_rejects_writes(
    api_client: APIClient, request: pytest.FixtureRequest, area: str, route: str, method: str
) -> None:
    obj, url = area_url(request, area, route)
    before = stored(obj)
    response = getattr(api_client, method)(url, HACKED)
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert (type(obj).objects.count(), stored(obj)) == (1, before)


@pytest.mark.parametrize('area', AREAS)
@pytest.mark.parametrize('method', WRITE_METHODS)
def test_public_content_rejects_writes_with_admin_token(
    api_client: APIClient, admin_user: User, request: pytest.FixtureRequest, area: str, method: str
) -> None:
    obj, url = area_url(request, area)
    token = Token.objects.create(user=admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    before = stored(obj)
    response = getattr(api_client, method)(url, HACKED)
    assert response.status_code == 405
    assert (type(obj).objects.count(), stored(obj)) == (1, before)


@pytest.mark.parametrize('area', AREAS)
@pytest.mark.parametrize('route', ROUTES)
@pytest.mark.parametrize('method', ['get', 'head', 'options'])
def test_public_content_allows_only_reading_methods(
    api_client: APIClient, request: pytest.FixtureRequest, area: str, route: str, method: str
) -> None:
    url = area_url(request, area, route)[1]
    response = getattr(api_client, method)(url)
    assert response.status_code == 200
    assert response['Allow'] == 'GET, HEAD, OPTIONS'


@pytest.mark.parametrize('path', ['entries', 'concepts', 'errors', 'debug-guides'])
@pytest.mark.parametrize('slug', ['for.schleife', 'for%20schleife', 'f%C3%BCr', '%00'])
def test_detail_with_invalid_characters_returns_404(
    api_client: APIClient,
    entry: Entry,
    concept: Concept,
    error_message: ErrorMessage,
    debug_guide: DebugGuide,
    path: str,
    slug: str,
) -> None:
    assert api_client.get(f'/api/{path}/{slug}/').status_code == 404


# Errors
ERROR_JSON = {
    'slug': 'module-not-found',
    'topic': 'python',
    'message': "ModuleNotFoundError: No module named 'django'",
    'meaning': 'Python findet das Paket nicht.',
    'cause': 'Die virtuelle Umgebung ist nicht aktiv.',
    'steps': ['Umgebung aktivieren.', 'Paket installieren.'],
    'solution': {'language': 'terminal', 'code': 'pip install django'},
}


def create_error(topic: Topic, slug: str, **fields: object) -> ErrorMessage:
    return ErrorMessage.objects.create(**({'topic': topic, 'slug': slug, 'message': slug} | fields))


def test_errors_list_is_public(api_client: APIClient, error_message: ErrorMessage) -> None:
    response = api_client.get(reverse('error-list'))
    assert response.status_code == 200
    assert response.json() == [ERROR_JSON]


def test_error_detail_is_public(api_client: APIClient, error_message: ErrorMessage) -> None:
    response = api_client.get(reverse('error-detail', args=['module-not-found']))
    assert response.status_code == 200
    assert response.json() == ERROR_JSON


def test_error_without_solution_has_no_solution_key(
    api_client: APIClient, error_message: ErrorMessage
) -> None:
    ErrorMessage.objects.filter(pk=error_message.pk).update(language='', code_de='')
    data = api_client.get(reverse('error-detail', args=['module-not-found'])).json()
    assert 'solution' not in data
    assert data == {key: value for key, value in ERROR_JSON.items() if key != 'solution'}


def test_error_without_steps_has_empty_steps(
    api_client: APIClient, error_message: ErrorMessage
) -> None:
    error_message.steps.all().delete()
    data = api_client.get(reverse('error-detail', args=['module-not-found'])).json()
    assert data['steps'] == []


@pytest.mark.parametrize('header', ['en', 'en-US,en;q=0.9,de;q=0.8'])
def test_error_detail_uses_accept_language(
    api_client: APIClient, error_message: ErrorMessage, header: str
) -> None:
    url = reverse('error-detail', args=['module-not-found'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE=header).json()
    assert [data['meaning'], data['cause']] == [
        'Python cannot find the package.',
        'The virtual environment is not active.',
    ]
    assert data['steps'] == ['Activate the environment.', 'Paket installieren.']
    assert data['message'] == ERROR_JSON['message']
    assert data['solution'] == ERROR_JSON['solution']


def test_error_uses_german_for_unknown_language(
    api_client: APIClient, error_message: ErrorMessage
) -> None:
    url = reverse('error-detail', args=['module-not-found'])
    assert api_client.get(url, HTTP_ACCEPT_LANGUAGE='fr').json() == ERROR_JSON


def test_errors_list_filters_by_topic(
    api_client: APIClient, topic: Topic, git_alltag: Subtopic
) -> None:
    create_error(topic, 'module')
    create_error(git_alltag.topic, 'push')
    assert list_slugs(api_client, 'error', topic='python') == ['module']
    assert list_slugs(api_client, 'error', topic='git') == ['push']


@pytest.mark.parametrize('params', [{}, {'topic': ''}, {'page': '2', 'search': 'x'}])
def test_errors_list_without_topic_returns_all_in_order(
    api_client: APIClient, topic: Topic, git_alltag: Subtopic, params: dict
) -> None:
    create_error(topic, 'port', position=2)
    create_error(topic, 'module', position=1)
    create_error(git_alltag.topic, 'push', position=9)
    assert list_slugs(api_client, 'error', **params) == ['push', 'module', 'port']


@pytest.mark.parametrize('value', BROKEN_TOPICS)
def test_errors_list_with_unknown_topic_is_empty(
    api_client: APIClient, error_message: ErrorMessage, value: str
) -> None:
    assert list_slugs(api_client, 'error', topic=value) == []


def test_errors_list_is_empty_without_errors(api_client: APIClient, topic: Topic) -> None:
    assert list_slugs(api_client, 'error') == []


def test_errors_load_in_two_queries(
    api_client: APIClient,
    error_message: ErrorMessage,
    git_alltag: Subtopic,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    create_error(git_alltag.topic, 'push').steps.create(text_de='Erst pullen.')
    with django_assert_num_queries(2):
        api_client.get(reverse('error-list'))
    with django_assert_num_queries(2):
        api_client.get(reverse('error-list'), {'topic': 'python'})
    with django_assert_num_queries(2):
        api_client.get(reverse('error-detail', args=['module-not-found']))


@pytest.mark.parametrize('slug', ['cobol', 'MODULE-NOT-FOUND', 'module_not_found', 'python'])
def test_error_detail_unknown_slug_returns_404(
    api_client: APIClient, error_message: ErrorMessage, slug: str
) -> None:
    response = api_client.get(reverse('error-detail', args=[slug]))
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}


def test_error_detail_ignores_slug_of_other_area(api_client: APIClient, entry: Entry) -> None:
    assert api_client.get(reverse('error-detail', args=['for-schleife'])).status_code == 404


def test_error_returns_text_unchanged_as_json(api_client: APIClient, topic: Topic) -> None:
    script = '<script>alert(1)</script>'
    error = create_error(topic, 'xss', message=script, meaning_de=script)
    error.steps.create(text_de=script)
    response = api_client.get(reverse('error-detail', args=['xss']))
    data = response.json()
    assert response['Content-Type'] == 'application/json'
    assert [data['message'], data['meaning'], data['steps']] == [script, script, [script]]


def test_error_detail_uses_english_code(api_client: APIClient, error_message: ErrorMessage) -> None:
    error_message.code_en = 'python -m pip install django'
    error_message.save()
    url = reverse('error-detail', args=['module-not-found'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE='en').json()
    assert data['solution'] == {'language': 'terminal', 'code': 'python -m pip install django'}


def test_errors_list_keeps_steps_with_their_error(
    api_client: APIClient, error_message: ErrorMessage, git_alltag: Subtopic
) -> None:
    push = create_error(git_alltag.topic, 'push')
    push.steps.create(text_de='Zuerst pullen.', position=1)
    push.steps.create(text_de='Konflikte lösen.', position=2)
    create_error(git_alltag.topic, 'merge')
    data = api_client.get(reverse('error-list')).json()
    assert {item['slug']: item['steps'] for item in data} == {
        'push': ['Zuerst pullen.', 'Konflikte lösen.'],
        'merge': [],
        'module-not-found': ['Umgebung aktivieren.', 'Paket installieren.'],
    }


def test_errors_list_for_topic_without_errors_is_empty(
    api_client: APIClient, error_message: ErrorMessage, group: Group
) -> None:
    Topic.objects.create(group=group, slug='django', name_de='Django')
    assert list_slugs(api_client, 'error', topic='django') == []


@pytest.mark.parametrize(
    ('header', 'meaning'),
    [
        ('en', 'Python cannot find the package.'),
        ('en-US,en;q=0.9,de;q=0.8', 'Python cannot find the package.'),
        ('fr', 'Python findet das Paket nicht.'),
        ('de', 'Python findet das Paket nicht.'),
    ],
)
def test_errors_list_uses_accept_language(
    api_client: APIClient, error_message: ErrorMessage, header: str, meaning: str
) -> None:
    data = api_client.get(reverse('error-list'), HTTP_ACCEPT_LANGUAGE=header).json()
    assert [item['meaning'] for item in data] == [meaning]


# Debug guides
GUIDE_JSON = {
    'slug': 'vorgehen',
    'label': 'Vorgehen',
    'title': 'Der Ablauf bei jedem Fehler',
    'summary': 'Vier Schritte für jeden Fehler.',
    'steps': [
        {'title': 'Die Meldung lesen', 'text': 'Die wichtige Zeile steht unten.'},
        {
            'title': 'Änderungen ansehen',
            'text': 'git diff zeigt sie.',
            'code': {'language': 'terminal', 'code': 'git diff'},
        },
    ],
}
TOPIC_GUIDE_JSON = {
    'slug': 'python-debuggen',
    'topic': 'python',
    'title': 'Python debuggen',
    'summary': 'Mit Tests und Ausgaben.',
    'steps': [
        {
            'title': 'Tests starten',
            'text': 'Startet alle Tests.',
            'code': {
                'language': 'terminal',
                'code': {'win': 'python manage.py test', 'unix': 'python3 manage.py test'},
            },
        }
    ],
}


def create_guide(topic: Topic | None, slug: str, **fields: object) -> DebugGuide:
    label = {} if topic else {'label_de': slug}
    data = {'topic': topic, 'slug': slug, 'title_de': slug, 'summary_de': slug} | label
    return DebugGuide.objects.create(**(data | fields))


@pytest.fixture
def guides(debug_guide: DebugGuide, topic_guide: DebugGuide) -> None:
    pass


def test_debug_guides_list_is_public(api_client: APIClient, guides: None) -> None:
    response = api_client.get(reverse('debug-guide-list'))
    assert response.status_code == 200
    assert response.json() == [GUIDE_JSON, TOPIC_GUIDE_JSON]


@pytest.mark.parametrize(
    ('slug', 'expected'),
    [('vorgehen', GUIDE_JSON), ('python-debuggen', TOPIC_GUIDE_JSON)],
)
def test_debug_guide_detail_is_public(
    api_client: APIClient, guides: None, slug: str, expected: dict
) -> None:
    response = api_client.get(reverse('debug-guide-detail', args=[slug]))
    assert response.status_code == 200
    assert response.json() == expected


def test_debug_guide_without_steps_has_empty_steps(
    api_client: APIClient, debug_guide: DebugGuide
) -> None:
    debug_guide.steps.all().delete()
    data = api_client.get(reverse('debug-guide-detail', args=['vorgehen'])).json()
    assert data['steps'] == []


@pytest.mark.parametrize(
    ('params', 'expected'),
    [
        ({'general': 'true'}, ['vorgehen']),
        ({'general': 'true', 'topic': 'python'}, ['vorgehen']),
        ({'topic': 'python'}, ['python-debuggen']),
        ({'topic': 'python', 'general': 'false'}, ['python-debuggen']),
        ({'topic': ''}, ['vorgehen', 'python-debuggen']),
    ],
)
def test_debug_guides_list_filters(
    api_client: APIClient, guides: None, params: dict, expected: list[str]
) -> None:
    assert list_slugs(api_client, 'debug-guide', **params) == expected


@pytest.mark.parametrize('value', ['false', '1', 'TRUE', 'True', 'yes', '', 'true\n'])
def test_debug_guides_list_ignores_other_general_values(
    api_client: APIClient, guides: None, value: str
) -> None:
    assert list_slugs(api_client, 'debug-guide', general=value) == ['vorgehen', 'python-debuggen']


@pytest.mark.parametrize('value', BROKEN_TOPICS)
def test_debug_guides_list_with_unknown_topic_is_empty(
    api_client: APIClient, guides: None, value: str
) -> None:
    assert list_slugs(api_client, 'debug-guide', topic=value) == []


def test_debug_guides_list_is_empty_without_guides(api_client: APIClient, db: None) -> None:
    assert list_slugs(api_client, 'debug-guide') == []
    assert list_slugs(api_client, 'debug-guide', general='true') == []


def test_general_list_is_empty_without_general_guides(
    api_client: APIClient, topic_guide: DebugGuide
) -> None:
    assert list_slugs(api_client, 'debug-guide', general='true') == []


def test_debug_guides_list_starts_with_general_ones_in_order(
    api_client: APIClient, topic: Topic, git_alltag: Subtopic
) -> None:
    create_guide(topic, 'python-debuggen', position=-9)
    create_guide(git_alltag.topic, 'git-debuggen', position=9)
    create_guide(None, 'browser', position=2)
    create_guide(None, 'vorgehen', position=1)
    expected = ['vorgehen', 'browser', 'git-debuggen', 'python-debuggen']
    assert list_slugs(api_client, 'debug-guide') == expected


@pytest.mark.parametrize('header', ['en', 'en-US,en;q=0.9,de;q=0.8'])
def test_debug_guide_detail_uses_accept_language(
    api_client: APIClient, debug_guide: DebugGuide, header: str
) -> None:
    debug_guide.steps.filter(code_de='git diff').update(code_en='git diff --stat')
    url = reverse('debug-guide-detail', args=['vorgehen'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE=header).json()
    assert [data['label'], data['title']] == ['Approach', 'The process for every error']
    assert [step['title'] for step in data['steps']] == ['Die Meldung lesen', 'Änderungen ansehen']
    assert data['steps'][1]['code'] == {'language': 'terminal', 'code': 'git diff --stat'}


@pytest.mark.parametrize('route', ROUTES)
def test_debug_guides_use_german_for_unknown_language(
    api_client: APIClient, debug_guide: DebugGuide, route: str
) -> None:
    args = ['vorgehen'] if route == 'detail' else []
    data = api_client.get(reverse(f'debug-guide-{route}', args=args), HTTP_ACCEPT_LANGUAGE='fr')
    assert data.json() == (GUIDE_JSON if route == 'detail' else [GUIDE_JSON])


def test_debug_guides_list_uses_accept_language(
    api_client: APIClient, debug_guide: DebugGuide
) -> None:
    data = api_client.get(reverse('debug-guide-list'), HTTP_ACCEPT_LANGUAGE='en').json()
    assert [item['label'] for item in data] == ['Approach']


def test_debug_guides_list_keeps_steps_with_their_guide(
    api_client: APIClient, guides: None
) -> None:
    create_guide(None, 'leer')
    data = api_client.get(reverse('debug-guide-list')).json()
    assert {item['slug']: [step['title'] for step in item['steps']] for item in data} == {
        'vorgehen': ['Die Meldung lesen', 'Änderungen ansehen'],
        'leer': [],
        'python-debuggen': ['Tests starten'],
    }


@pytest.mark.parametrize('params', [{}, {'general': 'true'}, {'topic': 'python'}])
def test_debug_guides_list_loads_in_two_queries(
    api_client: APIClient,
    guides: None,
    params: dict,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    with django_assert_num_queries(2):
        api_client.get(reverse('debug-guide-list'), params)


def test_debug_guide_detail_loads_in_two_queries(
    api_client: APIClient, guides: None, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(2):
        api_client.get(reverse('debug-guide-detail', args=['python-debuggen']))


@pytest.mark.parametrize('slug', ['cobol', 'VORGEHEN', 'python_debuggen', 'python', 'debuggen'])
def test_debug_guide_detail_unknown_slug_returns_404(
    api_client: APIClient, guides: None, slug: str
) -> None:
    response = api_client.get(reverse('debug-guide-detail', args=[slug]))
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}


def test_debug_guide_detail_ignores_slug_of_other_area(
    api_client: APIClient, error_message: ErrorMessage
) -> None:
    url = reverse('debug-guide-detail', args=['module-not-found'])
    assert api_client.get(url).status_code == 404


@pytest.mark.parametrize('slug', ['vorgehen', 'python-debuggen'])
def test_debug_guide_detail_ignores_general_param(
    api_client: APIClient, guides: None, slug: str
) -> None:
    url = reverse('debug-guide-detail', args=[slug])
    assert api_client.get(url, {'general': 'true'}).status_code == 200


def test_debug_guide_returns_text_unchanged_as_json(api_client: APIClient, db: None) -> None:
    script = '<script>alert(1)</script>'
    guide = create_guide(None, 'xss', label_de=script, title_de=script)
    guide.steps.create(title_de=script, text_de=script, language='html', code_de=script)
    response = api_client.get(reverse('debug-guide-detail', args=['xss']))
    data = response.json()
    assert response['Content-Type'] == 'application/json'
    assert [data['label'], data['title']] == [script, script]
    assert data['steps'] == [
        {'title': script, 'text': script, 'code': {'language': 'html', 'code': script}}
    ]


def test_debug_guide_steps_use_english_texts_and_os_code(
    api_client: APIClient, topic_guide: DebugGuide
) -> None:
    topic_guide.steps.update(
        title_en='Run tests',
        text_en='Runs all tests.',
        code_en='py manage.py test',
        code_unix_en='python3 -m pytest',
    )
    url = reverse('debug-guide-detail', args=['python-debuggen'])
    step = api_client.get(url, HTTP_ACCEPT_LANGUAGE='en').json()['steps'][0]
    assert step == {
        'title': 'Run tests',
        'text': 'Runs all tests.',
        'code': {
            'language': 'terminal',
            'code': {'win': 'py manage.py test', 'unix': 'python3 -m pytest'},
        },
    }


@pytest.mark.parametrize('value', BROKEN_TOPICS)
def test_general_wins_over_broken_topic(api_client: APIClient, guides: None, value: str) -> None:
    assert list_slugs(api_client, 'debug-guide', general='true', topic=value) == ['vorgehen']


def test_errors_list_ignores_general_param(
    api_client: APIClient, error_message: ErrorMessage
) -> None:
    assert list_slugs(api_client, 'error', general='true') == ['module-not-found']
