from datetime import UTC, datetime

import pytest
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle

from app_accounts.models import User
from app_content.models import Topic
from app_feedback.models import Suggestion

pytestmark = pytest.mark.django_db

URL = reverse('my-requests')


@pytest.fixture
def logged_in(api_client: APIClient, user: User) -> APIClient:
    api_client.force_login(user)
    return api_client


@pytest.fixture
def other_user(db: None) -> User:
    return User.objects.create_user('grace@example.com', 'Kaffee-Tasse-2026!')


def add_improvement(user: User | None, **changes: object) -> Suggestion:
    data = {'kind': 'improvement', 'user': user, 'area': 'feature', 'idea': 'x' * 30}
    if user is None:
        data['email'] = 'guest@example.com'
    return Suggestion.objects.create(**(data | changes))


def set_created_at(suggestion: Suggestion, *day: int) -> None:
    created_at = datetime(*day, 10, 0, tzinfo=UTC)
    Suggestion.objects.filter(pk=suggestion.pk).update(created_at=created_at)


# Read
def test_my_requests_are_empty_without_requests(logged_in: APIClient) -> None:
    response = logged_in.get(URL)
    assert response.status_code == 200
    assert response.json() == []


def test_my_requests_return_open_request(logged_in: APIClient, bug_suggestion: Suggestion) -> None:
    set_created_at(bug_suggestion, 2026, 10, 12)
    assert logged_in.get(URL).json() == [
        {
            'id': bug_suggestion.pk,
            'kind': 'bug',
            'subject': 'Virtuelle Umgebung anlegen',
            'date': '2026-10-12',
            'status': 'open',
        }
    ]


def test_my_requests_return_answer(logged_in: APIClient, bug_suggestion: Suggestion) -> None:
    bug_suggestion.answer = 'Danke für den Hinweis, ist korrigiert.'
    bug_suggestion.save()
    request = logged_in.get(URL).json()[0]
    assert request['status'] == 'done'
    assert request['answer'] == 'Danke für den Hinweis, ist korrigiert.'


def test_my_requests_return_done_request_without_answer(
    logged_in: APIClient, bug_suggestion: Suggestion
) -> None:
    Suggestion.objects.filter(pk=bug_suggestion.pk).update(status='done')
    request = logged_in.get(URL).json()[0]
    assert request['status'] == 'done'
    assert 'answer' not in request


def test_my_requests_return_subject_of_each_kind(
    logged_in: APIClient, user: User, topic: Topic
) -> None:
    add_improvement(user, idea='Eine Suche über alle Bereiche, die auch Aliase findet und mehr.')
    Suggestion.objects.create(
        kind='entry', user=user, area='command', topic=topic, title='git stash', reason='x' * 20
    )
    subjects = [request['subject'] for request in logged_in.get(URL).json()]
    assert subjects == ['git stash', 'Eine Suche über alle Bereiche, die auch Aliase findet und…']


def test_my_requests_are_newest_first(logged_in: APIClient, user: User) -> None:
    older, newer, same_time = (add_improvement(user) for _ in range(3))
    set_created_at(older, 2026, 10, 1)
    set_created_at(newer, 2026, 10, 20)
    set_created_at(same_time, 2026, 10, 20)
    ids = [request['id'] for request in logged_in.get(URL).json()]
    assert ids == [same_time.pk, newer.pk, older.pk]


def test_my_requests_return_only_own_requests(
    logged_in: APIClient, user: User, other_user: User, entry_suggestion: Suggestion
) -> None:
    own = add_improvement(user)
    add_improvement(other_user)
    assert [request['id'] for request in logged_in.get(URL).json()] == [own.pk]


def test_my_requests_skip_guest_request_with_same_email(logged_in: APIClient, user: User) -> None:
    add_improvement(None, email='ada@example.com')
    assert logged_in.get(URL).json() == []


def test_my_requests_keep_html_as_text(logged_in: APIClient, user: User) -> None:
    add_improvement(user, answer='<script>alert(1)</script>')
    response = logged_in.get(URL)
    assert response['Content-Type'] == 'application/json'
    assert response.json()[0]['answer'] == '<script>alert(1)</script>'


def test_my_requests_ignore_query_parameters(
    logged_in: APIClient, user: User, other_user: User
) -> None:
    add_improvement(other_user)
    assert logged_in.get(URL, {'user': other_user.pk, 'status': 'done'}).json() == []


def test_my_requests_load_in_three_queries(
    logged_in: APIClient, user: User, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    for _ in range(3):
        add_improvement(user)
    with django_assert_num_queries(3):
        logged_in.get(URL)


# Security
def test_my_requests_of_guest_are_rejected(api_client: APIClient) -> None:
    response = api_client.get(URL)
    assert response.status_code == 401
    assert response.json() == {'code': 'not_authenticated'}


def test_my_requests_with_unknown_session_are_rejected(api_client: APIClient) -> None:
    api_client.cookies['sessionid'] = 'invalid'
    assert api_client.get(URL).status_code == 401


def test_my_requests_of_deactivated_user_are_rejected(logged_in: APIClient, user: User) -> None:
    User.objects.filter(pk=user.pk).update(is_active=False)
    assert logged_in.get(URL).status_code == 401


def test_my_requests_after_logout_are_rejected(logged_in: APIClient) -> None:
    logged_in.post(reverse('auth-logout'))
    assert logged_in.get(URL).status_code == 401


def test_my_requests_need_no_csrf_token(csrf_client: APIClient, user: User) -> None:
    csrf_client.force_login(user)
    assert csrf_client.get(URL).status_code == 200


def test_my_requests_are_throttled(logged_in: APIClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(UserRateThrottle.THROTTLE_RATES, 'user', '1/hour')
    logged_in.get(URL)
    response = logged_in.get(URL)
    assert response.status_code == 429
    assert response.json()['code'] == 'throttled'


@pytest.mark.parametrize('method', ['post', 'put', 'patch', 'delete'])
def test_my_requests_reject_other_methods(
    logged_in: APIClient, bug_suggestion: Suggestion, method: str
) -> None:
    response = getattr(logged_in, method)(URL, {'status': 'done'}, format='json')
    bug_suggestion.refresh_from_db()
    assert response.status_code == 405
    assert response.json() == {'code': 'method_not_allowed'}
    assert response['Allow'] == 'GET, HEAD, OPTIONS'
    assert bug_suggestion.status == 'open'
    assert Suggestion.objects.count() == 1
