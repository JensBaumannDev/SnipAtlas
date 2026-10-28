import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from app_accounts.models import User
from app_content.models import Group, Subtopic, Topic

pytestmark = pytest.mark.django_db


def topic_data(group: Group, **changes: str) -> dict:
    data = {
        'group': group.pk,
        'slug': 'django',
        'name_de': 'Django',
        'name_en': 'Django',
        'color': '#092e20',
        'position': 0,
        'subtopics-TOTAL_FORMS': 1,
        'subtopics-INITIAL_FORMS': 0,
        'subtopics-0-slug': 'models',
        'subtopics-0-name_de': 'Models',
        'subtopics-0-name_en': 'Models',
        'subtopics-0-position': 0,
    }
    return data | changes


def add_topic(admin_client: Client, group: Group, **changes: str) -> HttpResponse:
    return admin_client.post(reverse('admin:app_content_topic_add'), topic_data(group, **changes))


def form_error_codes(response: HttpResponse, field: str) -> list[str]:
    form = response.context['adminform'].form
    return [error.code for error in form.errors.as_data()[field]]


# Access
@pytest.mark.parametrize('model', ['group', 'topic'])
def test_content_list_redirects_user_without_staff(client: Client, user: User, model: str) -> None:
    client.force_login(user)
    response = client.get(reverse(f'admin:app_content_{model}_changelist'))
    assert response.status_code == 302
    assert response.url.startswith(reverse('admin:login'))


@pytest.mark.parametrize('model', ['group', 'topic'])
def test_content_list_forbids_staff_without_permission(staff_client: Client, model: str) -> None:
    response = staff_client.get(reverse(f'admin:app_content_{model}_changelist'))
    assert response.status_code == 403


# Group
def test_group_list_loads(admin_client: Client, group: Group) -> None:
    response = admin_client.get(reverse('admin:app_content_group_changelist'))
    assert response.status_code == 200
    assert 'Backend' in response.content.decode()


def test_group_add_page_has_language_tabs(admin_client: Client) -> None:
    response = admin_client.get(reverse('admin:app_content_group_add'))
    fields = response.context['adminform'].form.fields
    assert {'name_de', 'name_en'} <= set(fields)


def test_admin_adds_group(admin_client: Client) -> None:
    data = {'slug': 'tools', 'name_de': 'Werkzeuge', 'name_en': 'Tools', 'position': 2}
    response = admin_client.post(reverse('admin:app_content_group_add'), data)
    assert response.status_code == 302
    assert Group.objects.get(slug='tools').name_en == 'Tools'


def test_admin_requires_german_name(admin_client: Client) -> None:
    data = {'slug': 'tools', 'name_de': '', 'name_en': 'Tools', 'position': 2}
    response = admin_client.post(reverse('admin:app_content_group_add'), data)
    assert form_error_codes(response, 'name_de') == ['required']


def test_group_change_page_loads(admin_client: Client, group: Group) -> None:
    response = admin_client.get(reverse('admin:app_content_group_change', args=[group.pk]))
    assert response.status_code == 200


def test_admin_keeps_group_with_topics(admin_client: Client, topic: Topic) -> None:
    url = reverse('admin:app_content_group_delete', args=[topic.group.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.context['protected']
    assert Group.objects.filter(pk=topic.group.pk).exists()


def test_admin_deletes_empty_group(admin_client: Client, group: Group) -> None:
    url = reverse('admin:app_content_group_delete', args=[group.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not Group.objects.exists()


# Topic
def test_topic_list_loads(admin_client: Client, topic: Topic) -> None:
    response = admin_client.get(reverse('admin:app_content_topic_changelist'))
    assert response.status_code == 200
    assert 'Python' in response.content.decode()


def test_topic_list_filters_by_group(admin_client: Client, group: Group, topic: Topic) -> None:
    frontend = Group.objects.create(slug='frontend', name_de='Frontend')
    Topic.objects.create(group=frontend, slug='css', name_de='CSS')
    url = reverse('admin:app_content_topic_changelist')
    response = admin_client.get(url, {'group__id__exact': group.pk})
    assert list(response.context['cl'].result_list) == [topic]


def test_topic_list_searches_by_name(admin_client: Client, group: Group, topic: Topic) -> None:
    Topic.objects.create(group=group, slug='django', name_de='Django')
    url = reverse('admin:app_content_topic_changelist')
    response = admin_client.get(url, {'q': 'pyth'})
    assert list(response.context['cl'].result_list) == [topic]


def test_topic_change_page_loads(admin_client: Client, subtopic: Subtopic) -> None:
    url = reverse('admin:app_content_topic_change', args=[subtopic.topic.pk])
    response = admin_client.get(url)
    assert response.status_code == 200
    assert 'Schleifen' in response.content.decode()


def test_admin_adds_topic_with_subtopic(admin_client: Client, group: Group) -> None:
    response = add_topic(admin_client, group)
    topic = Topic.objects.get(slug='django')
    assert response.status_code == 302
    assert list(topic.subtopics.values_list('slug', flat=True)) == ['models']


def test_admin_rejects_topic_slug_debuggen(admin_client: Client, group: Group) -> None:
    response = add_topic(admin_client, group, slug='debuggen')
    assert form_error_codes(response, 'slug') == ['reserved']
    assert not Topic.objects.exists()


def test_admin_rejects_invalid_color(admin_client: Client, group: Group) -> None:
    response = add_topic(admin_client, group, color='blue')
    assert form_error_codes(response, 'color') == ['invalid']


def test_admin_rejects_duplicate_subtopic_slug(admin_client: Client, group: Group) -> None:
    changes = {
        'subtopics-TOTAL_FORMS': 2,
        'subtopics-1-slug': 'models',
        'subtopics-1-name_de': 'Models 2',
        'subtopics-1-position': 1,
    }
    response = add_topic(admin_client, group, **changes)
    formset = response.context['inline_admin_formsets'][0].formset
    assert formset.non_form_errors()
    assert not Topic.objects.exists()


def test_admin_changes_topic_and_deletes_subtopic(
    admin_client: Client, group: Group, subtopic: Subtopic
) -> None:
    topic = subtopic.topic
    changes = {
        'slug': 'python',
        'name_de': 'Python 3',
        'subtopics-INITIAL_FORMS': 1,
        'subtopics-0-id': subtopic.pk,
        'subtopics-0-topic': topic.pk,
        'subtopics-0-slug': 'schleifen',
        'subtopics-0-DELETE': 'on',
    }
    url = reverse('admin:app_content_topic_change', args=[topic.pk])
    response = admin_client.post(url, topic_data(group, **changes))
    topic.refresh_from_db()
    assert response.status_code == 302
    assert topic.name_de == 'Python 3'
    assert not topic.subtopics.exists()


def test_topic_list_saves_position(admin_client: Client, topic: Topic) -> None:
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 1,
        'form-0-id': topic.pk,
        'form-0-position': 5,
        '_save': 'Save',
    }
    response = admin_client.post(reverse('admin:app_content_topic_changelist'), data)
    topic.refresh_from_db()
    assert response.status_code == 302
    assert topic.position == 5
