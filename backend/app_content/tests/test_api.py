import pytest
from django.db.models import Model
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle

from app_accounts.models import User
from app_content.models import Concept, Entry, Group, Subtopic, Topic

pytestmark = pytest.mark.django_db

WRITE_METHODS = ['post', 'put', 'patch', 'delete']
CONTENT = ['entry', 'concept']
CONTENT_MODELS = {'entry': Entry, 'concept': Concept}


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
@pytest.mark.parametrize(
    'value',
    [
        'cobol',
        'PYTHON',
        'schleifen',
        "python' OR '1'='1",
        'python%',
        'python\n',
        'py\x00thon',
        'x' * 5000,
    ],
)
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
@pytest.mark.parametrize('value', ['git', 'py\x00thon'])
def test_content_detail_ignores_topic_param(
    api_client: APIClient, request: pytest.FixtureRequest, fixture: str, value: str
) -> None:
    request.getfixturevalue(fixture)
    url = reverse(f'{fixture}-detail', args=['for-schleife'])
    assert api_client.get(url, {'topic': value}).status_code == 200


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
@pytest.mark.parametrize('route', ['list', 'detail'])
def test_content_works_with_token(
    api_client: APIClient, user: User, request: pytest.FixtureRequest, fixture: str, route: str
) -> None:
    request.getfixturevalue(fixture)
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    args = ['for-schleife'] if route == 'detail' else []
    assert api_client.get(reverse(f'{fixture}-{route}', args=args)).status_code == 200


@pytest.mark.parametrize('fixture', CONTENT)
@pytest.mark.parametrize('route', ['list', 'detail'])
def test_content_rejects_invalid_token(
    api_client: APIClient, request: pytest.FixtureRequest, fixture: str, route: str
) -> None:
    request.getfixturevalue(fixture)
    api_client.credentials(HTTP_AUTHORIZATION='Token invalid')
    args = ['for-schleife'] if route == 'detail' else []
    response = api_client.get(reverse(f'{fixture}-{route}', args=args))
    assert response.status_code == 401
    assert response.json() == {'code': 'authentication_failed'}


@pytest.mark.parametrize('fixture', CONTENT)
@pytest.mark.parametrize('route', ['list', 'detail'])
def test_content_is_throttled(
    api_client: APIClient,
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    fixture: str,
    route: str,
) -> None:
    request.getfixturevalue(fixture)
    monkeypatch.setitem(AnonRateThrottle.THROTTLE_RATES, 'anon', '1/hour')
    args = ['for-schleife'] if route == 'detail' else []
    api_client.get(reverse(f'{fixture}-{route}', args=args))
    response = api_client.get(reverse(f'{fixture}-{route}', args=args))
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'


@pytest.mark.parametrize('fixture', CONTENT)
@pytest.mark.parametrize('route', ['list', 'detail'])
@pytest.mark.parametrize('method', WRITE_METHODS)
def test_content_rejects_writes(
    api_client: APIClient, request: pytest.FixtureRequest, fixture: str, route: str, method: str
) -> None:
    obj = request.getfixturevalue(fixture)
    args = ['for-schleife'] if route == 'detail' else []
    body = {'slug': 'neu', 'title': 'Hacked', 'subtopic': obj.subtopic.pk}
    response = getattr(api_client, method)(reverse(f'{fixture}-{route}', args=args), body)
    obj.refresh_from_db()
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert (type(obj).objects.count(), obj.title) == (1, obj.title_de)


@pytest.mark.parametrize('fixture', CONTENT)
@pytest.mark.parametrize('method', WRITE_METHODS)
def test_content_rejects_writes_with_token(
    api_client: APIClient,
    admin_user: User,
    request: pytest.FixtureRequest,
    fixture: str,
    method: str,
) -> None:
    obj = request.getfixturevalue(fixture)
    token = Token.objects.create(user=admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    url = reverse(f'{fixture}-detail', args=['for-schleife'])
    response = getattr(api_client, method)(url, {'title': 'Hacked'})
    assert response.status_code == 405
    assert type(obj).objects.get(pk=obj.pk).title == obj.title_de


@pytest.mark.parametrize('fixture', CONTENT)
def test_content_rejects_token_of_inactive_user(
    api_client: APIClient, user: User, request: pytest.FixtureRequest, fixture: str
) -> None:
    request.getfixturevalue(fixture)
    token = Token.objects.create(user=user)
    User.objects.filter(pk=user.pk).update(is_active=False)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    response = api_client.get(reverse(f'{fixture}-list'))
    assert response.status_code == 401
    assert response.json() == {'code': 'authentication_failed'}


@pytest.mark.parametrize('fixture', CONTENT)
@pytest.mark.parametrize('route', ['list', 'detail'])
@pytest.mark.parametrize('method', ['get', 'head', 'options'])
def test_content_allows_only_reading_methods(
    api_client: APIClient, request: pytest.FixtureRequest, fixture: str, route: str, method: str
) -> None:
    request.getfixturevalue(fixture)
    args = ['for-schleife'] if route == 'detail' else []
    response = getattr(api_client, method)(reverse(f'{fixture}-{route}', args=args))
    assert response.status_code == 200
    assert response['Allow'] == 'GET, HEAD, OPTIONS'


@pytest.mark.parametrize('fixture', CONTENT)
def test_content_understands_browser_language_header(
    api_client: APIClient, request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    url = reverse(f'{fixture}-detail', args=['for-schleife'])
    data = api_client.get(url, HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9,de;q=0.8').json()
    assert data['title'] == obj.title_en


@pytest.mark.parametrize('model', ['entries', 'concepts'])
@pytest.mark.parametrize('slug', ['for.schleife', 'for%20schleife', 'f%C3%BCr', '%00'])
def test_content_detail_with_invalid_characters_returns_404(
    api_client: APIClient, entry: Entry, concept: Concept, model: str, slug: str
) -> None:
    assert api_client.get(f'/api/{model}/{slug}/').status_code == 404
