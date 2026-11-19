import pytest
from django.forms.models import model_to_dict
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle

from app_accounts.models import User
from app_content.models import RoadmapBlock, RoadmapPhase, RoadmapStep, Topic

pytestmark = pytest.mark.django_db

Blocks = dict[str, RoadmapBlock]
WRITE_METHODS = ['post', 'put', 'patch', 'delete']
BROKEN_SLUGS = [
    'cobol',
    'Django',
    'django_rest',
    "django' OR '1'='1",
    'django%',
    'djan\ngo',
    'x' * 5000,
]
ROADMAP_URLS = ['roadmap', 'roadmap-tree']
ALL_URLS = ['roadmap-block-list', *ROADMAP_URLS]


@pytest.fixture
def member_client(api_client: APIClient, user: User) -> APIClient:
    api_client.force_authenticate(user)
    return api_client


@pytest.mark.parametrize('name', ALL_URLS)
def test_guest_cannot_read_roadmap(api_client: APIClient, name: str) -> None:
    response = get(api_client, name)
    assert response.status_code == 401
    assert response.json()['code'] == 'not_authenticated'


def node(path: str, **extra: object) -> dict:
    name = path.rstrip('/').rpartition('/')[2]
    return {'name': name, 'path': path, 'folder': path.endswith('/'), 'tracked': True} | extra


def get(client: APIClient, name: str, blocks: str | None = 'django', **headers: str) -> Response:
    params = {} if blocks is None else {'blocks': blocks}
    return client.get(reverse(name), params, **headers)


def add_step(phase: RoadmapPhase, slug: str, position: int, *paths: tuple) -> RoadmapStep:
    step = phase.steps.create(
        slug=slug, title_de=slug, why_de='Weil.', verification_de='Geht.', position=position
    )
    for index, (path, explanation, *tracked) in enumerate(paths):
        step.paths.create(
            path=path,
            change='new',
            explanation_de=explanation,
            tracked=not tracked,
            position=index,
        )
    return step


@pytest.fixture
def plan(blocks: Blocks, roadmap_step: RoadmapStep) -> RoadmapPhase:
    start = RoadmapPhase.objects.create(
        slug='vorbereiten', title_de='Vorbereiten', summary_de='Git und Ordner.', position=1
    )
    add_step(start, 'repo', 1, ('README.md', 'Beschreibt das Projekt.'), ('.gitignore', 'Liste.'))
    backend = roadmap_step.phase
    add_step(
        backend,
        'projekt',
        1,
        ('backend/', 'Alles für Django.'),
        ('backend/.venv/', 'Pakete nur hier.', 'untracked'),
        ('backend/core/', 'Einstellungen.'),
        ('backend/manage.py', 'Startet Befehle.'),
    )
    docker = add_step(backend, 'app-anlegen-docker', 9)
    docker.conditions.create(block=blocks['docker'], rule='requires')
    frontend = RoadmapPhase.objects.create(
        slug='frontend-anlegen', title_de='Frontend anlegen', summary_de='Angular.', position=3
    )
    frontend.conditions.create(block=blocks['angular'], rule='requires')
    add_step(frontend, 'ng-new', 1, ('frontend/', 'Alles für Angular.'))
    empty = RoadmapPhase.objects.create(
        slug='container', title_de='Container', summary_de='Docker.', position=4
    )
    add_step(empty, 'compose', 1).conditions.create(block=blocks['docker'], rule='requires')
    return backend


# Blocks
BLOCKS_JSON = [
    {'slug': 'angular', 'name': 'Angular', 'kind': 'frontend', 'requirement': 'any'},
    {'slug': 'react', 'name': 'React', 'kind': 'frontend', 'requirement': 'any'},
    {'slug': 'django', 'name': 'Django', 'kind': 'backend', 'requirement': 'any'},
    {'slug': 'docker', 'name': 'Docker', 'kind': 'extra', 'requirement': 'any'},
    {'slug': 'postgresql', 'name': 'PostgreSQL', 'kind': 'extra', 'requirement': 'backend'},
    {'slug': 'static-hosting', 'name': 'Netlify', 'kind': 'hosting', 'requirement': 'no-backend'},
]


def test_blocks_list_includes_unavailable_blocks(member_client: APIClient, blocks: Blocks) -> None:
    response = get(member_client, 'roadmap-block-list', None)
    expected = [item | {'available': item['slug'] != 'react'} for item in BLOCKS_JSON]
    assert response.status_code == 200
    assert response.json() == expected


def test_blocks_list_names_topic_for_logo(
    member_client: APIClient, blocks: Blocks, topic: Topic
) -> None:
    RoadmapBlock.objects.filter(slug='django').update(topic=topic)
    data = get(member_client, 'roadmap-block-list', None).json()
    assert data[2]['topic'] == 'python'
    assert all('topic' not in item for index, item in enumerate(data) if index != 2)


def test_blocks_list_keeps_position_order(member_client: APIClient, blocks: Blocks) -> None:
    RoadmapBlock.objects.filter(slug='docker').update(position=-1)
    data = get(member_client, 'roadmap-block-list', None).json()
    assert [item['slug'] for item in data][:2] == ['docker', 'angular']


def test_blocks_list_uses_accept_language(member_client: APIClient, blocks: Blocks) -> None:
    RoadmapBlock.objects.filter(slug='static-hosting').update(name_en='Static hosting')
    data = get(member_client, 'roadmap-block-list', None, HTTP_ACCEPT_LANGUAGE='en').json()
    assert [data[5]['name'], data[2]['name']] == ['Static hosting', 'Django']


def test_blocks_list_is_empty_without_blocks(member_client: APIClient, db: None) -> None:
    assert get(member_client, 'roadmap-block-list', None).json() == []


def test_blocks_list_loads_in_one_query(
    member_client: APIClient,
    blocks: Blocks,
    topic: Topic,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    RoadmapBlock.objects.update(topic=topic)
    with django_assert_num_queries(1):
        get(member_client, 'roadmap-block-list', None)


# Roadmap: answer
def test_roadmap_for_backend_only(member_client: APIClient, plan: RoadmapPhase) -> None:
    response = get(member_client, 'roadmap')
    assert response.status_code == 200
    data = response.json()
    assert data['blocks'] == ['django']
    assert [phase['slug'] for phase in data['phases']] == ['vorbereiten', 'backend-anlegen']
    assert [step['slug'] for step in data['phases'][1]['steps']] == ['projekt', 'app-anlegen']


def test_roadmap_phase_has_exact_form(member_client: APIClient, plan: RoadmapPhase) -> None:
    phase = get(member_client, 'roadmap').json()['phases'][0]
    readme = {'path': 'README.md', 'change': 'new', 'tracked': True}
    gitignore = {'path': '.gitignore', 'change': 'new', 'tracked': True}
    assert phase == {
        'slug': 'vorbereiten',
        'title': 'Vorbereiten',
        'summary': 'Git und Ordner.',
        'steps': [
            {
                'slug': 'repo',
                'title': 'repo',
                'why': 'Weil.',
                'verification': 'Geht.',
                'code': [],
                'paths': [
                    readme | {'explanation': 'Beschreibt das Projekt.'},
                    gitignore | {'explanation': 'Liste.'},
                ],
                'tree': [
                    node('.gitignore', change='new', explanation='Liste.'),
                    node('README.md', change='new', explanation='Beschreibt das Projekt.'),
                ],
                'errors': [],
                'concepts': [],
            }
        ],
    }


def test_roadmap_step_has_exact_form_with_all_parts(
    member_client: APIClient, plan: RoadmapPhase
) -> None:
    step = get(member_client, 'roadmap').json()['phases'][1]['steps'][1]
    del step['tree']
    assert step == {
        'slug': 'app-anlegen',
        'title': 'Django-App anlegen',
        'why': 'Jede Aufgabe bekommt eine eigene App.',
        'folder': 'backend/',
        'context': 'Umgebung aktiv',
        'verification': 'Neben core/ liegt app_recipes/.',
        'note': 'Das Präfix app_ macht eigene Apps erkennbar.',
        'code': [
            {
                'kind': 'command',
                'language': 'terminal',
                'code': {
                    'win': 'python manage.py startapp app_recipes',
                    'unix': 'python3 manage.py startapp app_recipes',
                },
            },
            {
                'kind': 'change',
                'path': 'backend/core/settings.py',
                'language': 'python',
                'code': "INSTALLED_APPS += ['app_recipes']",
            },
        ],
        'paths': [
            {
                'path': 'backend/app_recipes/',
                'change': 'new',
                'tracked': True,
                'explanation': 'Die App für alles rund um Rezepte.',
            },
            {
                'path': 'backend/core/settings.py',
                'change': 'changed',
                'tracked': True,
                'explanation': 'Kennt jetzt die neue App.',
            },
        ],
        'errors': [
            {
                'topic': 'python',
                'slug': 'module-not-found',
                'message': "ModuleNotFoundError: No module named 'django'",
            }
        ],
        'concepts': [
            {
                'topic': 'python',
                'subtopic': 'schleifen',
                'slug': 'for-schleife',
                'title': 'Die for-Schleife',
            }
        ],
    }


def test_roadmap_step_tree_builds_on_earlier_steps(
    member_client: APIClient, plan: RoadmapPhase
) -> None:
    steps = get(member_client, 'roadmap').json()['phases'][1]['steps']
    venv = node('backend/.venv/', tracked=False, explanation='Pakete nur hier.')
    root_files = [
        node('.gitignore', explanation='Liste.'),
        node('README.md', explanation='Beschreibt das Projekt.'),
    ]
    assert steps[0]['tree'] == [
        node(
            'backend/',
            change='new',
            explanation='Alles für Django.',
            children=[
                venv | {'change': 'new'},
                node('backend/core/', change='new', explanation='Einstellungen.'),
                node('backend/manage.py', change='new', explanation='Startet Befehle.'),
            ],
        ),
        *root_files,
    ]
    settings = node(
        'backend/core/settings.py', change='changed', explanation='Kennt jetzt die neue App.'
    )
    assert steps[1]['tree'] == [
        node(
            'backend/',
            explanation='Alles für Django.',
            children=[
                venv,
                node(
                    'backend/app_recipes/',
                    change='new',
                    explanation='Die App für alles rund um Rezepte.',
                ),
                node('backend/core/', explanation='Einstellungen.', children=[settings]),
                node('backend/manage.py', explanation='Startet Befehle.'),
            ],
        ),
        *root_files,
    ]


def test_roadmap_leaves_out_empty_optional_fields(
    member_client: APIClient, plan: RoadmapPhase
) -> None:
    step = get(member_client, 'roadmap').json()['phases'][1]['steps'][0]
    assert {'folder', 'context', 'note'} & set(step) == set()


# Roadmap: choice
@pytest.mark.parametrize(
    ('chosen', 'phases'),
    [
        ('django', ['vorbereiten', 'backend-anlegen']),
        ('angular', ['vorbereiten', 'frontend-anlegen']),
        ('angular,django', ['vorbereiten', 'backend-anlegen', 'frontend-anlegen']),
        ('django,docker', ['vorbereiten', 'backend-anlegen', 'container']),
    ],
)
def test_roadmap_shows_only_matching_phases(
    member_client: APIClient, plan: RoadmapPhase, chosen: str, phases: list[str]
) -> None:
    data = get(member_client, 'roadmap', chosen).json()
    assert [phase['slug'] for phase in data['phases']] == phases


def test_roadmap_takes_the_step_variant_for_the_choice(
    member_client: APIClient, plan: RoadmapPhase
) -> None:
    data = get(member_client, 'roadmap', 'django,docker').json()
    assert [step['slug'] for step in data['phases'][1]['steps']] == [
        'projekt',
        'app-anlegen-docker',
    ]


def test_roadmap_leaves_out_phase_without_matching_steps(
    member_client: APIClient, plan: RoadmapPhase
) -> None:
    data = get(member_client, 'roadmap', 'angular').json()
    assert 'container' not in [phase['slug'] for phase in data['phases']]


@pytest.mark.parametrize(
    'value',
    ['docker,django', 'django,docker,django', ' docker , django ', 'django,,docker,'],
)
def test_roadmap_cleans_the_choice(
    member_client: APIClient, plan: RoadmapPhase, value: str
) -> None:
    assert get(member_client, 'roadmap', value).json()['blocks'] == ['django', 'docker']


def test_roadmap_orders_phases_and_steps_by_position(
    member_client: APIClient, plan: RoadmapPhase
) -> None:
    RoadmapPhase.objects.filter(slug='vorbereiten').update(position=9)
    RoadmapStep.objects.filter(slug='projekt').update(position=20)
    data = get(member_client, 'roadmap').json()
    assert [phase['slug'] for phase in data['phases']] == ['backend-anlegen', 'vorbereiten']
    assert [step['slug'] for step in data['phases'][0]['steps']] == ['app-anlegen', 'projekt']


def test_roadmap_ignores_unknown_params(member_client: APIClient, plan: RoadmapPhase) -> None:
    response = member_client.get(reverse('roadmap'), {'blocks': 'django', 'page': '2', 'x': 'y'})
    assert response.status_code == 200


# Roadmap: errors
def error_fields(response: Response) -> dict:
    assert response.status_code == 400
    data = response.json()
    assert data['code'] == 'validation_error'
    return data['fields']


@pytest.mark.parametrize('name', ROADMAP_URLS)
def test_roadmap_without_choice_is_rejected(
    member_client: APIClient, plan: RoadmapPhase, name: str
) -> None:
    assert error_fields(get(member_client, name, None)) == {'blocks': ['required']}


@pytest.mark.parametrize('name', ROADMAP_URLS)
@pytest.mark.parametrize('value', ['', ',', ' , ,'])
def test_roadmap_with_empty_choice_is_rejected(
    member_client: APIClient, plan: RoadmapPhase, name: str, value: str
) -> None:
    assert error_fields(get(member_client, name, value)) == {'blocks': ['blank']}


@pytest.mark.parametrize('name', ROADMAP_URLS)
@pytest.mark.parametrize('value', [*BROKEN_SLUGS, 'django,cobol', 'django,Docker'])
def test_roadmap_with_unknown_block_is_rejected(
    member_client: APIClient, plan: RoadmapPhase, name: str, value: str
) -> None:
    assert error_fields(get(member_client, name, value)) == {'blocks': ['does_not_exist']}


@pytest.mark.parametrize('name', ROADMAP_URLS)
@pytest.mark.parametrize('value', ['py\x00thon', 'django,py\x00thon'])
def test_roadmap_with_null_character_is_rejected(
    member_client: APIClient, plan: RoadmapPhase, name: str, value: str
) -> None:
    expected = {'blocks': ['null_characters_not_allowed']}
    assert error_fields(get(member_client, name, value)) == expected


@pytest.mark.parametrize('name', ROADMAP_URLS)
@pytest.mark.parametrize(
    ('value', 'codes'),
    [
        ('docker', ['empty']),
        ('react', ['unavailable']),
        ('angular,react', ['unavailable', 'duplicate_kind']),
        ('angular,postgresql', ['needs_backend']),
        ('django,static-hosting', ['no_backend']),
        ('postgresql', ['empty', 'needs_backend']),
    ],
)
def test_roadmap_with_impossible_choice_is_rejected(
    member_client: APIClient, plan: RoadmapPhase, name: str, value: str, codes: list[str]
) -> None:
    assert error_fields(get(member_client, name, value)) == {'blocks': codes}


# Roadmap: language
def test_roadmap_uses_accept_language(member_client: APIClient, plan: RoadmapPhase) -> None:
    data = get(member_client, 'roadmap', HTTP_ACCEPT_LANGUAGE='en').json()
    phase = data['phases'][1]
    step = phase['steps'][1]
    assert [phase['title'], phase['summary']] == [
        'Set up the backend',
        'From an empty folder to a running server.',
    ]
    assert [step['title'], step['why'], step['context'], step['verification']] == [
        'Create a Django app',
        'Each task gets its own app.',
        'Environment active',
        'app_recipes/ sits next to core/.',
    ]
    assert step['paths'][0]['explanation'] == 'The app for everything about recipes.'
    assert step['tree'][0]['children'][1]['explanation'] == 'The app for everything about recipes.'


def test_roadmap_falls_back_to_german(member_client: APIClient, plan: RoadmapPhase) -> None:
    data = get(member_client, 'roadmap', HTTP_ACCEPT_LANGUAGE='en').json()
    step = data['phases'][1]['steps'][1]
    assert data['phases'][0]['title'] == 'Vorbereiten'
    assert step['note'] == 'Das Präfix app_ macht eigene Apps erkennbar.'
    assert step['paths'][1]['explanation'] == 'Kennt jetzt die neue App.'
    assert step['code'][0]['code']['unix'] == 'python3 manage.py startapp app_recipes'


@pytest.mark.parametrize(
    ('header', 'title'), [('en-US,en;q=0.9', 'Create a Django app'), ('fr', 'Django-App anlegen')]
)
def test_roadmap_understands_browser_language_header(
    member_client: APIClient, plan: RoadmapPhase, header: str, title: str
) -> None:
    data = get(member_client, 'roadmap', HTTP_ACCEPT_LANGUAGE=header).json()
    assert data['phases'][1]['steps'][1]['title'] == title


def test_tree_uses_accept_language(member_client: APIClient, plan: RoadmapPhase) -> None:
    data = get(member_client, 'roadmap-tree', HTTP_ACCEPT_LANGUAGE='en').json()
    app = data[0]['children'][1]
    assert app['explanation'] == 'The app for everything about recipes.'


# Roadmap: safety
def test_roadmap_returns_text_unchanged_as_json(
    member_client: APIClient, plan: RoadmapPhase
) -> None:
    script = '<script>alert(1)</script>'
    RoadmapStep.objects.filter(slug='app-anlegen').update(title_de=script)
    plan.steps.get(slug='projekt').paths.filter(path='backend/').update(explanation_de=script)
    response = get(member_client, 'roadmap')
    assert response['Content-Type'] == 'application/json'
    steps = response.json()['phases'][1]['steps']
    assert steps[1]['title'] == script
    assert steps[1]['tree'][0]['explanation'] == script


def test_roadmap_queries_do_not_grow_with_steps(
    member_client: APIClient,
    plan: RoadmapPhase,
    blocks: Blocks,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    with django_assert_num_queries(9):
        get(member_client, 'roadmap', 'angular,django')
    more = RoadmapPhase.objects.create(slug='mehr', title_de='x', summary_de='x', position=5)
    more.conditions.create(block=blocks['angular'], rule='requires')
    for index in range(3):
        step = add_step(more, f'schritt-{index}', index, (f'docs/{index}.md', 'Text.'))
        step.conditions.create(block=blocks['docker'], rule='excludes')
        step.codes.create(kind='command', language='terminal', code_de='ls')
    with django_assert_num_queries(9):
        get(member_client, 'roadmap', 'angular,django')


def test_tree_queries_do_not_grow_with_steps(
    member_client: APIClient, plan: RoadmapPhase, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(9):
        get(member_client, 'roadmap-tree', 'angular,django')
    add_step(plan, 'extra', 30, ('backend/extra.py', 'Mehr.'))
    with django_assert_num_queries(9):
        get(member_client, 'roadmap-tree', 'angular,django')


# Tree
def test_tree_shows_the_finished_project(member_client: APIClient, plan: RoadmapPhase) -> None:
    response = get(member_client, 'roadmap-tree', 'angular,django')
    origin = {'phase': 'backend-anlegen', 'step': 'projekt'}
    assert response.status_code == 200
    assert response.json() == [
        node(
            'backend/',
            explanation='Alles für Django.',
            children=[
                node('backend/.venv/', tracked=False, explanation='Pakete nur hier.', children=[])
                | origin,
                node(
                    'backend/app_recipes/',
                    explanation='Die App für alles rund um Rezepte.',
                    phase='backend-anlegen',
                    step='app-anlegen',
                    children=[],
                ),
                node(
                    'backend/core/',
                    explanation='Einstellungen.',
                    children=[
                        node(
                            'backend/core/settings.py',
                            explanation='Kennt jetzt die neue App.',
                            phase='backend-anlegen',
                            step='app-anlegen',
                        )
                    ],
                )
                | origin,
                node('backend/manage.py', explanation='Startet Befehle.') | origin,
            ],
        )
        | origin,
        node(
            'frontend/',
            explanation='Alles für Angular.',
            phase='frontend-anlegen',
            step='ng-new',
            children=[],
        ),
        node('.gitignore', explanation='Liste.', phase='vorbereiten', step='repo'),
        node('README.md', explanation='Beschreibt das Projekt.', phase='vorbereiten', step='repo'),
    ]


def test_tree_follows_the_choice(member_client: APIClient, plan: RoadmapPhase) -> None:
    data = get(member_client, 'roadmap-tree', 'angular').json()
    assert [item['path'] for item in data] == ['frontend/', '.gitignore', 'README.md']


def test_tree_is_empty_without_paths(member_client: APIClient, blocks: Blocks) -> None:
    assert get(member_client, 'roadmap-tree').json() == []


# Security
def stored(obj: object) -> dict:
    return model_to_dict(type(obj).objects.get(pk=obj.pk))


@pytest.mark.parametrize('name', ALL_URLS)
def test_roadmap_works_when_logged_in(
    api_client: APIClient, user: User, plan: RoadmapPhase, name: str
) -> None:
    api_client.force_login(user)
    assert get(api_client, name).status_code == 200


@pytest.mark.parametrize('name', ALL_URLS)
def test_roadmap_treats_unknown_session_as_guest(
    api_client: APIClient, plan: RoadmapPhase, name: str
) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert get(api_client, name).status_code == 401


@pytest.mark.parametrize('name', ALL_URLS)
def test_roadmap_treats_inactive_user_as_guest(
    api_client: APIClient, user: User, plan: RoadmapPhase, name: str
) -> None:
    api_client.force_login(user)
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert get(api_client, name).status_code == 401


@pytest.mark.parametrize('name', ALL_URLS)
def test_roadmap_is_throttled(
    member_client: APIClient, plan: RoadmapPhase, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, 'user', '1/hour')
    get(member_client, name)
    response = get(member_client, name)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'


@pytest.mark.parametrize('name', ROADMAP_URLS)
def test_roadmap_errors_are_throttled_too(
    member_client: APIClient, plan: RoadmapPhase, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, 'user', '1/hour')
    get(member_client, name, 'cobol')
    assert get(member_client, name, 'cobol').status_code == 429


@pytest.mark.parametrize('name', ALL_URLS)
@pytest.mark.parametrize('method', WRITE_METHODS)
@pytest.mark.parametrize('admin', [False, True])
def test_roadmap_rejects_writes(
    member_client: APIClient,
    admin_user: User,
    plan: RoadmapPhase,
    blocks: Blocks,
    name: str,
    method: str,
    admin: bool,
) -> None:
    if admin:
        member_client.force_authenticate(admin_user)
    before = [stored(blocks['django']), stored(plan)]
    hacked = {'slug': 'neu', 'name': 'Hacked', 'blocks': 'angular', 'title': 'Hacked'}
    response = getattr(member_client, method)(f'{reverse(name)}?blocks=django', hacked)
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert [stored(blocks['django']), stored(plan)] == before
    assert (RoadmapBlock.objects.count(), RoadmapPhase.objects.count()) == (6, 4)


@pytest.mark.parametrize('name', ALL_URLS)
@pytest.mark.parametrize('method', ['get', 'head', 'options'])
def test_roadmap_allows_only_reading_methods(
    member_client: APIClient, plan: RoadmapPhase, name: str, method: str
) -> None:
    response = getattr(member_client, method)(f'{reverse(name)}?blocks=django')
    assert response.status_code == 200
    assert response['Allow'] == 'GET, HEAD, OPTIONS'


@pytest.mark.parametrize('path', ['roadmap/x/', 'roadmap/blocks/django/', 'roadmap/tree/x/'])
def test_unknown_roadmap_paths_return_404(
    member_client: APIClient, plan: RoadmapPhase, path: str
) -> None:
    response = member_client.get(f'/api/{path}?blocks=django')
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
