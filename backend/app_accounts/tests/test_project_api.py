from datetime import datetime

import pytest
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle

from app_accounts.models import Project, ProjectNote, ProjectStep, User
from app_content.models import RoadmapBlock, RoadmapPhase, RoadmapStep

pytestmark = pytest.mark.django_db

Blocks = dict[str, RoadmapBlock]
CSRF_TOKEN = 'a' * 32
PASSWORD = 'Kaffee-Tasse-2026!'
PHASE = 'backend-anlegen'
STEP = 'app-anlegen'
PROJECT_URL = reverse('project')


def step_url(step: str = STEP, phase: str = PHASE) -> str:
    return reverse('project-step', args=[phase, step])


def note_url(step: str = STEP, phase: str = PHASE) -> str:
    return reverse('project-note', args=[phase, step])


def done(project: Project) -> list[str]:
    return [item.step.slug for item in project.completed_steps.all()]


def notes(project: Project) -> dict[str, str]:
    return {item.step.slug: item.text for item in project.notes.all()}


def put_blocks(client: APIClient, blocks: object) -> Response:
    return client.put(PROJECT_URL, {'blocks': blocks}, format='json')


def field_codes(response: Response) -> dict:
    assert response.status_code == 400
    data = response.json()
    assert data['code'] == 'validation_error'
    return data['fields']


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture
def my_project(user: User, blocks: Blocks, roadmap_step: RoadmapStep) -> Project:
    project = Project.objects.create(user=user)
    project.blocks.set([blocks['angular'], blocks['django']])
    return project


@pytest.fixture
def second_step(roadmap_step: RoadmapStep) -> RoadmapStep:
    return roadmap_step.phase.steps.create(
        slug='migrieren', title_de='Migrieren', why_de='x', verification_de='x', position=10
    )


@pytest.fixture
def docker_step(roadmap_step: RoadmapStep, blocks: Blocks) -> RoadmapStep:
    step = roadmap_step.phase.steps.create(
        slug='app-anlegen-docker', title_de='x', why_de='x', verification_de='x', position=9
    )
    step.conditions.create(block=blocks['docker'], rule='requires')
    return step


@pytest.fixture
def other_project(blocks: Blocks, roadmap_step: RoadmapStep) -> Project:
    other = User.objects.create_user('grace@example.com', PASSWORD)
    project = Project.objects.create(user=other)
    project.blocks.set([blocks['django']])
    project.completed_steps.create(step=roadmap_step)
    project.notes.create(step=roadmap_step, text='Fremde Notiz')
    return project


@pytest.fixture
def filled_project(
    my_project: Project, roadmap_step: RoadmapStep, second_step: RoadmapStep
) -> Project:
    start = RoadmapPhase.objects.create(slug='vorbereiten', title_de='x', summary_de='x')
    git = start.steps.create(slug='git', title_de='Git', why_de='x', verification_de='x')
    for step in (second_step, git, roadmap_step):
        my_project.completed_steps.create(step=step)
    my_project.notes.create(step=second_step, text='Später')
    my_project.notes.create(step=roadmap_step, text='Port 8020.')
    return my_project


# Read
def test_project_without_project_returns_404(logged_in: APIClient, other_project: Project) -> None:
    response = logged_in.get(PROJECT_URL)
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}


def test_project_returns_exact_form(logged_in: APIClient, my_project: Project) -> None:
    response = logged_in.get(PROJECT_URL)
    data = response.json()
    assert response.status_code == 200
    assert set(data) == {'blocks', 'completed', 'notes', 'createdAt', 'updatedAt'}
    assert (data['blocks'], data['completed'], data['notes']) == (['angular', 'django'], {}, {})
    assert datetime.fromisoformat(data['createdAt']) == my_project.created_at
    assert datetime.fromisoformat(data['updatedAt']) == my_project.updated_at


def test_project_groups_progress_and_notes_in_roadmap_order(
    logged_in: APIClient, filled_project: Project
) -> None:
    data = logged_in.get(PROJECT_URL).json()
    assert data['completed'] == {'vorbereiten': ['git'], PHASE: [STEP, 'migrieren']}
    assert list(data['completed']) == ['vorbereiten', PHASE]
    assert data['notes'] == {PHASE: {STEP: 'Port 8020.', 'migrieren': 'Später'}}
    assert list(data['notes'][PHASE]) == [STEP, 'migrieren']


def test_project_keeps_progress_outside_the_choice(
    logged_in: APIClient, my_project: Project, docker_step: RoadmapStep
) -> None:
    my_project.completed_steps.create(step=docker_step)
    assert logged_in.get(PROJECT_URL).json()['completed'] == {PHASE: ['app-anlegen-docker']}


def test_project_hides_data_of_other_users(
    logged_in: APIClient, my_project: Project, other_project: Project
) -> None:
    data = logged_in.get(PROJECT_URL).json()
    assert (data['completed'], data['notes']) == ({}, {})


def test_project_ignores_query_parameters(
    logged_in: APIClient, my_project: Project, other_project: Project
) -> None:
    response = logged_in.get(PROJECT_URL, {'user': other_project.user.pk, 'blocks': 'docker'})
    assert response.json()['blocks'] == ['angular', 'django']


def test_project_returns_note_text_unchanged_as_json(
    logged_in: APIClient, my_project: Project, roadmap_step: RoadmapStep
) -> None:
    script = '<script>alert(1)</script>\nZeile 2'
    my_project.notes.create(step=roadmap_step, text=script)
    response = logged_in.get(PROJECT_URL)
    assert response['Content-Type'] == 'application/json'
    assert response.json()['notes'] == {PHASE: {STEP: script}}


def test_project_queries_do_not_grow(
    logged_in: APIClient,
    filled_project: Project,
    docker_step: RoadmapStep,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    with django_assert_num_queries(6):
        logged_in.get(PROJECT_URL)
    filled_project.completed_steps.create(step=docker_step)
    filled_project.notes.create(step=docker_step, text='Noch eine')
    with django_assert_num_queries(6):
        logged_in.get(PROJECT_URL)


# Choose blocks
def test_put_project_creates_it(logged_in: APIClient, user: User, blocks: Blocks) -> None:
    response = put_blocks(logged_in, ['django', 'angular', 'docker'])
    project = user.projects.get()
    assert response.status_code == 201
    assert response.json()['blocks'] == ['angular', 'django', 'docker']
    assert project.block_slugs() == {'angular', 'django', 'docker'}


def test_put_project_replaces_blocks_and_keeps_progress(
    logged_in: APIClient, filled_project: Project
) -> None:
    before = filled_project.updated_at
    response = put_blocks(logged_in, ['angular'])
    filled_project.refresh_from_db()
    assert response.status_code == 200
    assert response.json()['blocks'] == ['angular']
    assert filled_project.block_slugs() == {'angular'}
    assert (len(done(filled_project)), len(notes(filled_project))) == (3, 2)
    assert filled_project.updated_at > before
    assert Project.objects.count() == 1


def test_put_project_counts_repeated_slugs_once(
    logged_in: APIClient, user: User, blocks: Blocks
) -> None:
    response = put_blocks(logged_in, ['django', 'django', ' angular '])
    assert response.status_code == 201
    assert user.projects.get().block_slugs() == {'angular', 'django'}


def test_put_project_ignores_other_fields(
    logged_in: APIClient, user: User, blocks: Blocks, other_project: Project
) -> None:
    body = {'blocks': ['django'], 'user': other_project.user.pk, 'createdAt': '2000-01-01'}
    response = logged_in.put(PROJECT_URL, body, format='json')
    assert response.status_code == 201
    assert user.projects.get().block_slugs() == {'django'}
    assert other_project.block_slugs() == {'django'}
    assert other_project.user.projects.count() == 1


@pytest.mark.parametrize(
    ('body', 'codes'),
    [
        ({}, ['required']),
        ({'blocks': None}, ['null']),
        ({'blocks': 'django'}, ['not_a_list']),
        ({'blocks': ['cobol']}, ['does_not_exist']),
        ({'blocks': ['django', 'Docker']}, ['does_not_exist']),
        ({'blocks': ['django', 'x' * 5000]}, ['does_not_exist']),
        ({'blocks': ["django' OR '1'='1"]}, ['does_not_exist']),
        ({'blocks': []}, ['empty']),
        ({'blocks': ['docker']}, ['empty']),
        ({'blocks': ['react']}, ['unavailable']),
        ({'blocks': ['angular', 'react']}, ['unavailable', 'duplicate_kind']),
        ({'blocks': ['angular', 'postgresql']}, ['needs_backend']),
        ({'blocks': ['django', 'static-hosting']}, ['no_backend']),
    ],
)
def test_put_project_rejects_invalid_choice(
    logged_in: APIClient, my_project: Project, body: dict, codes: list[str]
) -> None:
    response = logged_in.put(PROJECT_URL, body, format='json')
    assert field_codes(response) == {'blocks': codes}
    assert my_project.block_slugs() == {'angular', 'django'}


def test_put_project_with_invalid_choice_creates_nothing(
    logged_in: APIClient, user: User, blocks: Blocks
) -> None:
    field_codes(put_blocks(logged_in, ['docker']))
    assert not user.projects.exists()


# Delete project
def test_delete_project_removes_it_with_progress_and_notes(
    logged_in: APIClient, filled_project: Project, other_project: Project
) -> None:
    response = logged_in.delete(PROJECT_URL)
    assert response.status_code == 204
    assert list(Project.objects.all()) == [other_project]
    assert ProjectStep.objects.get().project == other_project
    assert ProjectNote.objects.get().project == other_project
    assert RoadmapStep.objects.filter(slug=STEP).exists()


def test_delete_project_without_project_is_allowed(
    logged_in: APIClient, other_project: Project
) -> None:
    assert logged_in.delete(PROJECT_URL).status_code == 204
    assert Project.objects.count() == 1


# Steps
def test_put_step_marks_it_done(logged_in: APIClient, my_project: Project) -> None:
    response = logged_in.put(step_url())
    assert response.status_code == 204
    assert response.content == b''
    assert done(my_project) == [STEP]


def test_put_step_twice_keeps_one(logged_in: APIClient, my_project: Project) -> None:
    logged_in.put(step_url())
    assert logged_in.put(step_url()).status_code == 204
    assert done(my_project) == [STEP]


def test_put_step_ignores_body(
    logged_in: APIClient, my_project: Project, second_step: RoadmapStep, other_project: Project
) -> None:
    body = {'step': 'migrieren', 'project': other_project.pk}
    logged_in.put(step_url(), body, format='json')
    assert done(my_project) == [STEP]
    assert done(other_project) == [STEP]


def test_put_step_outside_the_choice_returns_404(
    logged_in: APIClient, my_project: Project, docker_step: RoadmapStep
) -> None:
    response = logged_in.put(step_url('app-anlegen-docker'))
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert done(my_project) == []


def test_put_step_of_phase_outside_the_choice_returns_404(
    logged_in: APIClient, my_project: Project
) -> None:
    my_project.set_blocks([RoadmapBlock.objects.get(slug='angular')])
    assert logged_in.put(step_url()).status_code == 404
    assert done(my_project) == []


def test_delete_step_marks_it_not_done(logged_in: APIClient, filled_project: Project) -> None:
    assert logged_in.delete(step_url()).status_code == 204
    assert done(filled_project) == ['git', 'migrieren']


def test_delete_step_that_is_not_done_is_allowed(logged_in: APIClient, my_project: Project) -> None:
    assert logged_in.delete(step_url()).status_code == 204


def test_delete_step_outside_the_choice_is_allowed(
    logged_in: APIClient, my_project: Project, docker_step: RoadmapStep
) -> None:
    my_project.completed_steps.create(step=docker_step)
    assert logged_in.delete(step_url('app-anlegen-docker')).status_code == 204
    assert done(my_project) == []


def test_step_changes_keep_progress_of_other_user(
    logged_in: APIClient, my_project: Project, other_project: Project
) -> None:
    logged_in.put(step_url())
    logged_in.delete(step_url())
    assert done(other_project) == [STEP]


# Notes
def test_put_note_saves_it(logged_in: APIClient, my_project: Project) -> None:
    response = logged_in.put(
        note_url(), {'text': '  Port 8020, weil 8000 belegt ist.\n'}, format='json'
    )
    assert response.status_code == 200
    assert response.json() == {'text': 'Port 8020, weil 8000 belegt ist.'}
    assert notes(my_project) == {STEP: 'Port 8020, weil 8000 belegt ist.'}


def test_put_note_replaces_it(logged_in: APIClient, filled_project: Project) -> None:
    logged_in.put(note_url(), {'text': 'Neu'}, format='json')
    assert notes(filled_project) == {STEP: 'Neu', 'migrieren': 'Später'}
    assert ProjectNote.objects.filter(project=filled_project).count() == 2


def test_put_note_keeps_text_as_given(logged_in: APIClient, my_project: Project) -> None:
    text = '<script>alert(1)</script>\n  eingerückt\n\nEnde'
    logged_in.put(note_url(), {'text': text}, format='json')
    assert notes(my_project) == {STEP: text}


def test_put_note_with_maximum_length_is_saved(logged_in: APIClient, my_project: Project) -> None:
    response = logged_in.put(note_url(), {'text': 'x' * 2000}, format='json')
    assert response.status_code == 200


@pytest.mark.parametrize(
    ('body', 'code'),
    [
        ({}, 'required'),
        ({'text': None}, 'null'),
        ({'text': ''}, 'blank'),
        ({'text': ' \n '}, 'blank'),
        ({'text': 'x' * 2001}, 'max_length'),
    ],
)
def test_put_note_rejects_invalid_text(
    logged_in: APIClient, filled_project: Project, body: dict, code: str
) -> None:
    response = logged_in.put(note_url(), body, format='json')
    assert field_codes(response) == {'text': [code]}
    assert notes(filled_project)[STEP] == 'Port 8020.'


def test_put_note_outside_the_choice_returns_404(
    logged_in: APIClient, my_project: Project, docker_step: RoadmapStep
) -> None:
    response = logged_in.put(note_url('app-anlegen-docker'), {'text': 'x'}, format='json')
    assert response.status_code == 404
    assert notes(my_project) == {}


def test_delete_note_removes_it(logged_in: APIClient, filled_project: Project) -> None:
    assert logged_in.delete(note_url()).status_code == 204
    assert notes(filled_project) == {'migrieren': 'Später'}


def test_delete_note_without_note_is_allowed(logged_in: APIClient, my_project: Project) -> None:
    assert logged_in.delete(note_url()).status_code == 204


def test_note_changes_keep_note_of_other_user(
    logged_in: APIClient, my_project: Project, other_project: Project
) -> None:
    logged_in.put(note_url(), {'text': 'Meine'}, format='json')
    logged_in.delete(note_url())
    assert notes(other_project) == {STEP: 'Fremde Notiz'}


# Unknown project, phase or step
DETAIL_URLS = [step_url, note_url]
DETAIL_WRITES = [(url, method) for url in DETAIL_URLS for method in ('put', 'delete')]


@pytest.mark.parametrize(('url', 'method'), DETAIL_WRITES)
def test_steps_and_notes_without_project_return_404(
    logged_in: APIClient,
    roadmap_step: RoadmapStep,
    other_project: Project,
    url: object,
    method: str,
) -> None:
    response = getattr(logged_in, method)(url(), {'text': 'x'}, format='json')
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert (done(other_project), notes(other_project)) == ([STEP], {STEP: 'Fremde Notiz'})


@pytest.mark.parametrize(('url', 'method'), DETAIL_WRITES)
@pytest.mark.parametrize(
    ('phase', 'step'),
    [
        ('cobol', STEP),
        (PHASE, 'cobol'),
        (PHASE, 'APP-ANLEGEN'),
        (PHASE, 'app_anlegen'),
        ('BACKEND-ANLEGEN', STEP),
        ('vorbereiten', STEP),
        (PHASE, 'x' * 5000),
    ],
)
def test_steps_and_notes_with_unknown_phase_or_step_return_404(
    logged_in: APIClient,
    filled_project: Project,
    url: object,
    method: str,
    phase: str,
    step: str,
) -> None:
    response = getattr(logged_in, method)(url(step, phase), {'text': 'x'}, format='json')
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert len(done(filled_project)) == 3
    assert len(notes(filled_project)) == 2


@pytest.mark.parametrize('kind', ['steps', 'notes'])
@pytest.mark.parametrize(
    'path',
    [f'{PHASE}/app.anlegen', f'{PHASE}/f%C3%BCr', f'{PHASE}/%00', f'{PHASE}/{STEP}/extra', '..'],
)
def test_steps_and_notes_with_invalid_characters_return_404(
    logged_in: APIClient, my_project: Project, kind: str, path: str
) -> None:
    response = logged_in.put(f'/api/me/project/{kind}/{path}/', {'text': 'x'}, format='json')
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert done(my_project) == []


# Security
ENDPOINTS = [
    ('get', PROJECT_URL),
    ('put', PROJECT_URL),
    ('delete', PROJECT_URL),
    ('put', step_url()),
    ('delete', step_url()),
    ('put', note_url()),
    ('delete', note_url()),
]
WRITES = [endpoint for endpoint in ENDPOINTS if endpoint[0] != 'get']
BODY = {'blocks': ['angular'], 'text': 'Neu'}


def snapshot() -> list:
    projects = list(Project.objects.values_list('pk', 'user', 'updated_at'))
    blocks = list(Project.blocks.through.objects.values_list('project', 'block'))
    steps = list(ProjectStep.objects.values_list('pk', 'project', 'step'))
    texts = list(ProjectNote.objects.values_list('pk', 'project', 'step', 'text'))
    return [projects, blocks, steps, texts]


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_project_of_guest_is_rejected(
    api_client: APIClient, other_project: Project, method: str, url: str
) -> None:
    before = snapshot()
    response = getattr(api_client, method)(url, BODY, format='json')
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}
    assert snapshot() == before


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_project_with_unknown_session_is_rejected(
    api_client: APIClient, my_project: Project, method: str, url: str
) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert getattr(api_client, method)(url, BODY, format='json').status_code == 401


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_project_of_deactivated_user_is_rejected(
    logged_in: APIClient, user: User, my_project: Project, method: str, url: str
) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    before = snapshot()
    assert getattr(logged_in, method)(url, BODY, format='json').status_code == 401
    assert snapshot() == before


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_project_after_logout_is_rejected(
    logged_in: APIClient, my_project: Project, method: str, url: str
) -> None:
    logged_in.post(reverse('auth-logout'))
    assert getattr(logged_in, method)(url, BODY, format='json').status_code == 401


@pytest.mark.parametrize(('method', 'url'), WRITES)
def test_project_change_without_csrf_token_is_rejected(
    csrf_client: APIClient, user: User, filled_project: Project, method: str, url: str
) -> None:
    csrf_client.force_login(user)
    before = snapshot()
    response = getattr(csrf_client, method)(url, BODY, format='json')
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert snapshot() == before


@pytest.mark.parametrize(('method', 'url'), WRITES)
def test_project_change_with_csrf_token_is_allowed(
    csrf_client: APIClient, user: User, my_project: Project, method: str, url: str
) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    response = getattr(csrf_client, method)(url, BODY, format='json', HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code in (200, 204)


def test_project_read_needs_no_csrf_token(
    csrf_client: APIClient, user: User, my_project: Project
) -> None:
    csrf_client.force_login(user)
    assert csrf_client.get(PROJECT_URL).status_code == 200


@pytest.mark.parametrize(('method', 'url'), WRITES)
def test_project_is_throttled(
    logged_in: APIClient,
    my_project: Project,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    url: str,
) -> None:
    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, 'user', '1/hour')
    logged_in.get(PROJECT_URL)
    before = snapshot()
    response = getattr(logged_in, method)(url, BODY, format='json')
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert snapshot() == before


PROJECT_ALLOW = 'GET, PUT, DELETE, HEAD, OPTIONS'
DETAIL_ALLOW = 'PUT, DELETE, OPTIONS'


@pytest.mark.parametrize(
    ('url', 'method', 'allow'),
    [
        *[(PROJECT_URL, method, PROJECT_ALLOW) for method in ['post', 'patch']],
        *[(step_url(), method, DETAIL_ALLOW) for method in ['get', 'post', 'patch']],
        *[(note_url(), method, DETAIL_ALLOW) for method in ['get', 'post', 'patch']],
    ],
)
def test_project_rejects_other_methods(
    logged_in: APIClient, filled_project: Project, url: str, method: str, allow: str
) -> None:
    before = snapshot()
    response = getattr(logged_in, method)(url, BODY, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == allow
    assert snapshot() == before
