import pytest
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle

from app_accounts.models import CompletedStep, User
from app_content.models import Blueprint, BlueprintStep

pytestmark = pytest.mark.django_db

CSRF_TOKEN = 'a' * 32
BLUEPRINT = 'django-projekt-anlegen'
LIST_URL = reverse('progress-list')


def step_url(step: str = 'virtuelle-umgebung', blueprint: str = BLUEPRINT) -> str:
    return reverse('progress-step', args=[blueprint, step])


def blueprint_url(blueprint: str = BLUEPRINT) -> str:
    return reverse('progress-blueprint', args=[blueprint])


def done_steps(user: User) -> list[tuple[str, str]]:
    return list(user.completed_steps.values_list('step__blueprint__slug', 'step__slug'))


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture
def git_blueprint(blueprint: Blueprint) -> Blueprint:
    git = Blueprint.objects.create(
        topic=blueprint.topic, slug='git-einrichten', title_de='Git', summary_de='Git.'
    )
    git.steps.create(slug='installieren', title_de='Installieren', why_de='Nötig.')
    git.steps.create(slug='virtuelle-umgebung', title_de='Gleicher Slug', why_de='Test.')
    return git


@pytest.fixture
def progress(user: User, blueprint: Blueprint, git_blueprint: Blueprint) -> User:
    for step in [*blueprint.steps.all(), git_blueprint.steps.get(slug='installieren')]:
        CompletedStep.objects.create(user=user, step=step)
    return user


@pytest.fixture
def other_user(venv_step: BlueprintStep) -> User:
    other = User.objects.create_user('grace@example.com', 'Kaffee-Tasse-2026!')
    CompletedStep.objects.create(user=other, step=venv_step)
    return other


# List
def test_progress_returns_done_steps_per_blueprint(logged_in: APIClient, progress: User) -> None:
    response = logged_in.get(LIST_URL)
    assert response.status_code == 200
    assert response.json() == {
        BLUEPRINT: ['ordner-anlegen', 'virtuelle-umgebung'],
        'git-einrichten': ['installieren'],
    }


def test_progress_is_empty_object_without_done_steps(logged_in: APIClient) -> None:
    assert logged_in.get(LIST_URL).json() == {}


def test_progress_hides_steps_of_other_users(logged_in: APIClient, other_user: User) -> None:
    assert logged_in.get(LIST_URL).json() == {}


def test_progress_ignores_query_parameters(logged_in: APIClient, other_user: User) -> None:
    assert logged_in.get(LIST_URL, {'user': other_user.pk, 'blueprint': '\x00'}).json() == {}


def test_progress_shows_new_step_slug(logged_in: APIClient, progress: User) -> None:
    BlueprintStep.objects.filter(slug='ordner-anlegen').update(slug='ordner-erstellen')
    assert logged_in.get(LIST_URL).json()[BLUEPRINT] == ['ordner-erstellen', 'virtuelle-umgebung']


def test_progress_drops_deleted_blueprint(
    logged_in: APIClient, progress: User, blueprint: Blueprint
) -> None:
    blueprint.delete()
    assert logged_in.get(LIST_URL).json() == {'git-einrichten': ['installieren']}


def test_progress_keeps_digits_in_slugs(
    logged_in: APIClient, user: User, venv_step: BlueprintStep
) -> None:
    BlueprintStep.objects.filter(pk=venv_step.pk).update(slug='schritt-2a')
    CompletedStep.objects.create(user=user, step=venv_step)
    assert logged_in.get(LIST_URL).json() == {BLUEPRINT: ['schritt-2a']}


def test_progress_loads_in_three_queries(
    logged_in: APIClient, progress: User, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(3):
        logged_in.get(LIST_URL)


# Mark step
def test_put_step_marks_it_done(logged_in: APIClient, user: User, blueprint: Blueprint) -> None:
    response = logged_in.put(step_url())
    assert response.status_code == 204
    assert response.content == b''
    assert done_steps(user) == [(BLUEPRINT, 'virtuelle-umgebung')]


def test_put_step_twice_keeps_one(logged_in: APIClient, user: User, blueprint: Blueprint) -> None:
    logged_in.put(step_url())
    assert logged_in.put(step_url()).status_code == 204
    assert done_steps(user) == [(BLUEPRINT, 'virtuelle-umgebung')]


def test_put_step_uses_step_of_given_blueprint(
    logged_in: APIClient, user: User, git_blueprint: Blueprint
) -> None:
    logged_in.put(step_url(blueprint='git-einrichten'))
    assert done_steps(user) == [('git-einrichten', 'virtuelle-umgebung')]


def test_put_step_ignores_body(
    logged_in: APIClient, user: User, other_user: User, git_blueprint: Blueprint
) -> None:
    body = {'user': other_user.pk, 'step': 'installieren', 'blueprint': 'git-einrichten'}
    logged_in.put(step_url(), body, format='json')
    assert done_steps(user) == [(BLUEPRINT, 'virtuelle-umgebung')]
    assert done_steps(other_user) == [(BLUEPRINT, 'virtuelle-umgebung')]


def test_put_step_loads_in_seven_queries(
    logged_in: APIClient, blueprint: Blueprint, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(7):
        logged_in.put(step_url())


# Unmark step
def test_delete_step_marks_it_not_done(logged_in: APIClient, progress: User) -> None:
    response = logged_in.delete(step_url())
    assert response.status_code == 204
    assert done_steps(progress) == [
        (BLUEPRINT, 'ordner-anlegen'),
        ('git-einrichten', 'installieren'),
    ]


def test_delete_step_that_is_not_done_is_allowed(
    logged_in: APIClient, blueprint: Blueprint
) -> None:
    assert logged_in.delete(step_url()).status_code == 204


def test_delete_step_keeps_same_slug_in_other_blueprint(
    logged_in: APIClient, user: User, git_blueprint: Blueprint
) -> None:
    CompletedStep.objects.create(user=user, step=git_blueprint.steps.get(slug='virtuelle-umgebung'))
    logged_in.delete(step_url())
    assert done_steps(user) == [('git-einrichten', 'virtuelle-umgebung')]


def test_delete_step_keeps_progress_of_other_user(
    logged_in: APIClient, progress: User, other_user: User
) -> None:
    logged_in.delete(step_url())
    assert done_steps(other_user) == [(BLUEPRINT, 'virtuelle-umgebung')]


# Reset blueprint
def test_delete_blueprint_resets_only_its_steps(logged_in: APIClient, progress: User) -> None:
    response = logged_in.delete(blueprint_url())
    assert response.status_code == 204
    assert response.content == b''
    assert done_steps(progress) == [('git-einrichten', 'installieren')]


def test_delete_blueprint_without_progress_is_allowed(
    logged_in: APIClient, blueprint: Blueprint
) -> None:
    assert logged_in.delete(blueprint_url()).status_code == 204


def test_delete_blueprint_keeps_progress_of_other_user(
    logged_in: APIClient, progress: User, other_user: User
) -> None:
    logged_in.delete(blueprint_url())
    assert done_steps(other_user) == [(BLUEPRINT, 'virtuelle-umgebung')]


def test_delete_blueprint_keeps_steps(logged_in: APIClient, progress: User) -> None:
    logged_in.delete(blueprint_url())
    assert BlueprintStep.objects.count() == 4


# Unknown blueprint or step
@pytest.mark.parametrize('method', ['put', 'delete'])
@pytest.mark.parametrize(
    ('blueprint_slug', 'step'),
    [
        ('cobol', 'virtuelle-umgebung'),
        (BLUEPRINT, 'installieren'),
        (BLUEPRINT, 'cobol'),
        (BLUEPRINT, 'VIRTUELLE-UMGEBUNG'),
        (BLUEPRINT, 'virtuelle_umgebung'),
        ('DJANGO-PROJEKT-ANLEGEN', 'virtuelle-umgebung'),
        (BLUEPRINT, 'x' * 5000),
    ],
)
def test_step_with_unknown_blueprint_or_step_returns_404(
    logged_in: APIClient, progress: User, method: str, blueprint_slug: str, step: str
) -> None:
    before = done_steps(progress)
    response = getattr(logged_in, method)(step_url(step, blueprint_slug))
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert done_steps(progress) == before


@pytest.mark.parametrize('slug', ['cobol', 'virtuelle-umgebung', 'DJANGO-PROJEKT-ANLEGEN'])
def test_reset_with_unknown_blueprint_returns_404(
    logged_in: APIClient, progress: User, slug: str
) -> None:
    response = logged_in.delete(blueprint_url(slug))
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert len(done_steps(progress)) == 3


@pytest.mark.parametrize('method', ['put', 'delete'])
@pytest.mark.parametrize(
    'path',
    [
        f'{BLUEPRINT}/virtuelle.umgebung',
        f'{BLUEPRINT}/f%C3%BCr',
        f'{BLUEPRINT}/%00',
        'django%00/virtuelle-umgebung',
        f'{BLUEPRINT}/virtuelle-umgebung/extra',
        '..',
    ],
)
def test_progress_with_invalid_characters_returns_404(
    logged_in: APIClient, progress: User, method: str, path: str
) -> None:
    response = getattr(logged_in, method)(f'/api/me/progress/{path}/')
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert len(done_steps(progress)) == 3


# Security
ENDPOINTS = [
    ('get', LIST_URL),
    ('put', step_url()),
    ('delete', step_url()),
    ('delete', blueprint_url()),
]
WRITES = [endpoint for endpoint in ENDPOINTS if endpoint[0] != 'get']


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_progress_of_guest_is_rejected(
    api_client: APIClient, blueprint: Blueprint, method: str, url: str
) -> None:
    response = getattr(api_client, method)(url)
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}
    assert not CompletedStep.objects.exists()


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_progress_with_unknown_session_is_rejected(
    api_client: APIClient, blueprint: Blueprint, method: str, url: str
) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert getattr(api_client, method)(url).status_code == 401


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_progress_of_deactivated_user_is_rejected(
    logged_in: APIClient, user: User, blueprint: Blueprint, method: str, url: str
) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert getattr(logged_in, method)(url).status_code == 401


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_progress_after_logout_is_rejected(
    logged_in: APIClient, blueprint: Blueprint, method: str, url: str
) -> None:
    logged_in.post(reverse('auth-logout'))
    assert getattr(logged_in, method)(url).status_code == 401


@pytest.mark.parametrize(('method', 'url'), WRITES)
def test_progress_change_without_csrf_token_is_rejected(
    csrf_client: APIClient, progress: User, method: str, url: str
) -> None:
    if method == 'put':
        progress.completed_steps.filter(step__slug='virtuelle-umgebung').delete()
    before = done_steps(progress)
    csrf_client.force_login(progress)
    response = getattr(csrf_client, method)(url)
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert done_steps(progress) == before


@pytest.mark.parametrize(('method', 'url'), WRITES)
def test_progress_change_with_csrf_token_is_allowed(
    csrf_client: APIClient, user: User, blueprint: Blueprint, method: str, url: str
) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    assert getattr(csrf_client, method)(url, HTTP_X_CSRFTOKEN=CSRF_TOKEN).status_code == 204


def test_progress_list_needs_no_csrf_token(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    assert csrf_client.get(LIST_URL).status_code == 200


def test_progress_is_throttled(
    logged_in: APIClient, user: User, blueprint: Blueprint, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, 'user', '1/hour')
    logged_in.get(LIST_URL)
    response = logged_in.put(step_url())
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert not user.completed_steps.exists()


LIST_ALLOW = 'GET, HEAD, OPTIONS'
STEP_ALLOW = 'PUT, DELETE, OPTIONS'
BLUEPRINT_ALLOW = 'DELETE, OPTIONS'


@pytest.mark.parametrize(
    ('url', 'method', 'allow'),
    [
        *[(LIST_URL, method, LIST_ALLOW) for method in ['post', 'put', 'patch', 'delete']],
        *[(step_url(), method, STEP_ALLOW) for method in ['get', 'post', 'patch']],
        *[(blueprint_url(), method, BLUEPRINT_ALLOW) for method in ['get', 'post', 'put', 'patch']],
    ],
)
def test_progress_rejects_other_methods(
    logged_in: APIClient, progress: User, url: str, method: str, allow: str
) -> None:
    before = list(CompletedStep.objects.values_list('pk', 'user', 'step', 'created_at'))
    response = getattr(logged_in, method)(url, {'step': 'installieren'}, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == allow
    assert list(CompletedStep.objects.values_list('pk', 'user', 'step', 'created_at')) == before
