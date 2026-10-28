import pytest
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle

from app_accounts.models import Favorite, User
from app_content.models import Concept, Entry, Subtopic

pytestmark = pytest.mark.django_db

CSRF_TOKEN = 'a' * 32
LIST_URL = reverse('favorite-list')


def detail_url(slug: str = 'for-schleife') -> str:
    return reverse('favorite-detail', args=[slug])


def favorite_slugs(user: User) -> list[str]:
    return list(user.favorites.values_list('entry__slug', flat=True))


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture
def other_user(entry: Entry) -> User:
    other = User.objects.create_user('grace@example.com', 'Kaffee-Tasse-2026!')
    Favorite.objects.create(user=other, entry=entry)
    return other


@pytest.fixture
def favorites(user: User, entry: Entry, os_entry: Entry) -> list[Favorite]:
    return [
        Favorite.objects.create(user=user, entry=os_entry),
        Favorite.objects.create(user=user, entry=entry),
    ]


# List
def test_favorites_list_returns_own_favorites_in_order(
    logged_in: APIClient, favorites: list[Favorite]
) -> None:
    response = logged_in.get(LIST_URL)
    assert response.status_code == 200
    assert response.json() == [
        {
            'topic': 'python',
            'subtopic': 'schleifen',
            'slug': 'venv-aktivieren',
            'title': 'venv aktivieren',
        },
        {
            'topic': 'python',
            'subtopic': 'schleifen',
            'slug': 'for-schleife',
            'title': 'For-Schleife',
        },
    ]


def test_favorites_list_is_empty_without_favorites(logged_in: APIClient, entry: Entry) -> None:
    assert logged_in.get(LIST_URL).json() == []


def test_favorites_list_hides_favorites_of_other_users(
    logged_in: APIClient, other_user: User
) -> None:
    assert logged_in.get(LIST_URL).json() == []


def test_favorites_list_ignores_query_parameters(logged_in: APIClient, other_user: User) -> None:
    response = logged_in.get(LIST_URL, {'user': other_user.pk, 'topic': 'py\x00thon'})
    assert response.json() == []


def test_favorites_list_drops_deleted_entry(
    logged_in: APIClient, favorites: list[Favorite], os_entry: Entry
) -> None:
    os_entry.delete()
    assert [item['slug'] for item in logged_in.get(LIST_URL).json()] == ['for-schleife']


def test_favorites_list_shows_new_entry_slug(
    logged_in: APIClient, favorites: list[Favorite], entry: Entry
) -> None:
    Entry.objects.filter(pk=entry.pk).update(slug='for-loop')
    assert logged_in.get(LIST_URL).json()[1]['slug'] == 'for-loop'


def test_favorites_list_loads_in_three_queries(
    logged_in: APIClient,
    favorites: list[Favorite],
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    with django_assert_num_queries(3):
        logged_in.get(LIST_URL)


# List: language
def test_favorites_list_uses_accept_language(
    logged_in: APIClient, favorites: list[Favorite]
) -> None:
    data = logged_in.get(LIST_URL, HTTP_ACCEPT_LANGUAGE='en').json()
    assert data[1]['title'] == 'For loop'


def test_favorites_list_falls_back_to_german_title(
    logged_in: APIClient, favorites: list[Favorite]
) -> None:
    data = logged_in.get(LIST_URL, HTTP_ACCEPT_LANGUAGE='en').json()
    assert data[0]['title'] == 'venv aktivieren'


@pytest.mark.parametrize(
    ('header', 'title'),
    [('en-US,en;q=0.9,de;q=0.8', 'For loop'), ('fr', 'For-Schleife'), ('', 'For-Schleife')],
)
def test_favorites_list_understands_browser_language_header(
    logged_in: APIClient, favorites: list[Favorite], header: str, title: str
) -> None:
    data = logged_in.get(LIST_URL, HTTP_ACCEPT_LANGUAGE=header).json()
    assert data[1]['title'] == title


def test_favorites_list_returns_text_unchanged_as_json(
    logged_in: APIClient, favorites: list[Favorite], entry: Entry
) -> None:
    Entry.objects.filter(pk=entry.pk).update(title_de='<script>alert(1)</script>')
    response = logged_in.get(LIST_URL)
    assert response['Content-Type'] == 'application/json'
    assert response.json()[1]['title'] == '<script>alert(1)</script>'


# Set
def test_put_favorite_adds_entry(logged_in: APIClient, user: User, entry: Entry) -> None:
    response = logged_in.put(detail_url())
    assert response.status_code == 204
    assert response.content == b''
    assert favorite_slugs(user) == ['for-schleife']


def test_put_favorite_twice_keeps_one(logged_in: APIClient, user: User, entry: Entry) -> None:
    logged_in.put(detail_url())
    response = logged_in.put(detail_url())
    assert response.status_code == 204
    assert favorite_slugs(user) == ['for-schleife']


def test_put_favorite_appends_to_end(
    logged_in: APIClient, user: User, entry: Entry, os_entry: Entry
) -> None:
    logged_in.put(detail_url('venv-aktivieren'))
    logged_in.put(detail_url())
    assert [item['slug'] for item in logged_in.get(LIST_URL).json()] == [
        'venv-aktivieren',
        'for-schleife',
    ]


def test_put_favorite_ignores_body(
    logged_in: APIClient, user: User, other_user: User, entry: Entry, os_entry: Entry
) -> None:
    body = {'user': other_user.pk, 'entry': os_entry.pk, 'slug': 'venv-aktivieren'}
    logged_in.put(detail_url(), body, format='json')
    assert favorite_slugs(user) == ['for-schleife']
    assert favorite_slugs(other_user) == ['for-schleife']


def test_put_favorite_keeps_favorite_of_other_user(
    logged_in: APIClient, user: User, other_user: User
) -> None:
    logged_in.put(detail_url())
    assert Favorite.objects.count() == 2


def test_put_favorite_loads_in_seven_queries(
    logged_in: APIClient, entry: Entry, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    with django_assert_num_queries(7):
        logged_in.put(detail_url())


# Remove
def test_delete_favorite_removes_entry(
    logged_in: APIClient, user: User, favorites: list[Favorite]
) -> None:
    response = logged_in.delete(detail_url())
    assert response.status_code == 204
    assert response.content == b''
    assert favorite_slugs(user) == ['venv-aktivieren']


def test_delete_favorite_that_is_not_set_is_allowed(
    logged_in: APIClient, user: User, entry: Entry
) -> None:
    assert logged_in.delete(detail_url()).status_code == 204


def test_delete_favorite_keeps_favorite_of_other_user(
    logged_in: APIClient, user: User, other_user: User
) -> None:
    logged_in.delete(detail_url())
    assert favorite_slugs(other_user) == ['for-schleife']


def test_delete_favorite_keeps_entry(
    logged_in: APIClient, favorites: list[Favorite], entry: Entry
) -> None:
    logged_in.delete(detail_url())
    assert Entry.objects.filter(pk=entry.pk).exists()


# Set and remove: unknown entry
@pytest.mark.parametrize('method', ['put', 'delete'])
@pytest.mark.parametrize('slug', ['cobol', 'FOR-SCHLEIFE', 'for_schleife', 'schleifen', 'x' * 5000])
def test_favorite_with_unknown_entry_returns_404(
    logged_in: APIClient, user: User, entry: Entry, method: str, slug: str
) -> None:
    response = getattr(logged_in, method)(detail_url(slug))
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert not user.favorites.exists()


@pytest.mark.parametrize('method', ['put', 'delete'])
def test_favorite_ignores_slug_of_concept(
    logged_in: APIClient, user: User, subtopic: Subtopic, method: str
) -> None:
    Concept.objects.create(
        subtopic=subtopic,
        slug='nur-grundlage',
        title_de='Grundlage',
        summary_de='Kurz.',
        explanation_de='Lang.',
        language='python',
        code_de='pass',
    )
    response = getattr(logged_in, method)(detail_url('nur-grundlage'))
    assert response.status_code == 404
    assert not user.favorites.exists()


@pytest.mark.parametrize('method', ['put', 'delete'])
@pytest.mark.parametrize('slug', ['for.schleife', 'for%20schleife', 'f%C3%BCr', '%00', '..'])
def test_favorite_with_invalid_characters_returns_404(
    logged_in: APIClient, user: User, entry: Entry, method: str, slug: str
) -> None:
    response = getattr(logged_in, method)(f'/api/me/favorites/{slug}/')
    assert response.status_code == 404
    assert response.json() == {'code': 'not_found'}
    assert not user.favorites.exists()


# Security
ENDPOINTS = [('get', LIST_URL), ('put', detail_url()), ('delete', detail_url())]


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_favorites_of_guest_are_rejected(
    api_client: APIClient, entry: Entry, method: str, url: str
) -> None:
    response = getattr(api_client, method)(url)
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}
    assert not Favorite.objects.exists()


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_favorites_with_unknown_session_are_rejected(
    api_client: APIClient, entry: Entry, method: str, url: str
) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert getattr(api_client, method)(url).status_code == 401


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_favorites_of_deactivated_user_are_rejected(
    logged_in: APIClient, user: User, entry: Entry, method: str, url: str
) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert getattr(logged_in, method)(url).status_code == 401


@pytest.mark.parametrize(('method', 'url'), ENDPOINTS)
def test_favorites_after_logout_are_rejected(
    logged_in: APIClient, entry: Entry, method: str, url: str
) -> None:
    logged_in.post(reverse('auth-logout'))
    assert getattr(logged_in, method)(url).status_code == 401


@pytest.mark.parametrize('method', ['put', 'delete'])
def test_favorite_change_without_csrf_token_is_rejected(
    csrf_client: APIClient, user: User, favorites: list[Favorite], os_entry: Entry, method: str
) -> None:
    Favorite.objects.filter(entry=os_entry).delete()
    csrf_client.force_login(user)
    slug = 'venv-aktivieren' if method == 'put' else 'for-schleife'
    response = getattr(csrf_client, method)(detail_url(slug))
    assert response.status_code == 403
    assert response.json() == {'code': 'csrf_failed'}
    assert favorite_slugs(user) == ['for-schleife']


@pytest.mark.parametrize('method', ['put', 'delete'])
def test_favorite_change_with_csrf_token_is_allowed(
    csrf_client: APIClient, user: User, entry: Entry, method: str
) -> None:
    csrf_client.force_login(user)
    csrf_client.cookies['csrftoken'] = CSRF_TOKEN
    response = getattr(csrf_client, method)(detail_url(), HTTP_X_CSRFTOKEN=CSRF_TOKEN)
    assert response.status_code == 204


def test_favorites_list_needs_no_csrf_token(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    assert csrf_client.get(LIST_URL).status_code == 200


def test_favorites_are_throttled(
    logged_in: APIClient, user: User, entry: Entry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, 'user', '1/hour')
    logged_in.get(LIST_URL)
    response = logged_in.put(detail_url())
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'
    assert not user.favorites.exists()


@pytest.mark.parametrize(
    ('url', 'method', 'allow'),
    [
        (LIST_URL, 'post', 'GET, HEAD, OPTIONS'),
        (LIST_URL, 'put', 'GET, HEAD, OPTIONS'),
        (LIST_URL, 'patch', 'GET, HEAD, OPTIONS'),
        (LIST_URL, 'delete', 'GET, HEAD, OPTIONS'),
        (detail_url(), 'get', 'PUT, DELETE, OPTIONS'),
        (detail_url(), 'post', 'PUT, DELETE, OPTIONS'),
        (detail_url(), 'patch', 'PUT, DELETE, OPTIONS'),
    ],
)
def test_favorites_reject_other_methods(
    logged_in: APIClient, user: User, favorites: list[Favorite], url: str, method: str, allow: str
) -> None:
    before = list(Favorite.objects.values_list('pk', 'user', 'entry', 'created_at'))
    response = getattr(logged_in, method)(url, {'entry': 'venv-aktivieren'}, format='json')
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == allow
    assert list(Favorite.objects.values_list('pk', 'user', 'entry', 'created_at')) == before


def test_favorite_rejects_head_on_detail(logged_in: APIClient, entry: Entry) -> None:
    assert logged_in.head(detail_url()).status_code == 405
