import pytest
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle

from app_accounts.models import User
from app_content.models import Group, Subtopic, Topic

pytestmark = pytest.mark.django_db

WRITE_METHODS = ['post', 'put', 'patch', 'delete']


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
