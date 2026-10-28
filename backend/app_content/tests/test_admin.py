import pytest
from django.contrib.auth.models import Permission
from django.db.models import Model
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from app_accounts.models import User
from app_content.models import Concept, Entry, Group, Subtopic, Topic

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
CONTENT_ADMINS = ['group', 'topic', 'entry', 'concept']


@pytest.mark.parametrize('model', CONTENT_ADMINS)
def test_content_list_redirects_guest(client: Client, model: str) -> None:
    response = client.get(reverse(f'admin:app_content_{model}_changelist'))
    assert response.status_code == 302
    assert response.url.startswith(reverse('admin:login'))


@pytest.mark.parametrize('model', CONTENT_ADMINS)
def test_content_list_redirects_user_without_staff(client: Client, user: User, model: str) -> None:
    client.force_login(user)
    response = client.get(reverse(f'admin:app_content_{model}_changelist'))
    assert response.status_code == 302
    assert response.url.startswith(reverse('admin:login'))


@pytest.mark.parametrize('model', CONTENT_ADMINS)
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


@pytest.mark.parametrize('fixture', ['entry', 'concept'])
def test_admin_keeps_subtopic_with_content(
    admin_client: Client, group: Group, request: pytest.FixtureRequest, fixture: str
) -> None:
    subtopic = request.getfixturevalue(fixture).subtopic
    changes = {
        'slug': 'python',
        'subtopics-INITIAL_FORMS': 1,
        'subtopics-0-id': subtopic.pk,
        'subtopics-0-topic': subtopic.topic.pk,
        'subtopics-0-slug': 'schleifen',
        'subtopics-0-DELETE': 'on',
    }
    url = reverse('admin:app_content_topic_change', args=[subtopic.topic.pk])
    response = admin_client.post(url, topic_data(group, **changes))
    assert response.status_code == 200
    assert Subtopic.objects.filter(pk=subtopic.pk).exists()


# Entries and concepts
CONTENT = ['entry', 'concept']


def entry_data(subtopic: Subtopic, /, **changes: str) -> dict:
    data = {
        'subtopic': subtopic.pk,
        'slug': 'git-status',
        'title_de': 'Status anzeigen',
        'title_en': 'Show status',
        'description_de': 'Zeigt geänderte Dateien.',
        'description_en': '',
        'language': 'terminal',
        'code_de': 'git status',
        'code_en': '',
        'code_unix_de': '',
        'code_unix_en': '',
        'position': 0,
    }
    return data | changes


def concept_data(subtopic: Subtopic, /, **changes: str) -> dict:
    data = {
        'subtopic': subtopic.pk,
        'slug': 'while-schleife',
        'title_de': 'Die while-Schleife',
        'title_en': '',
        'summary_de': 'Läuft, solange die Bedingung gilt.',
        'summary_en': '',
        'explanation_de': 'Prüft vor jedem Durchlauf die Bedingung.',
        'explanation_en': '',
        'language': 'python',
        'code_de': 'while running: step()',
        'code_en': '',
        'note_de': '',
        'note_en': '',
        'position': 0,
    }
    return data | changes


CONTENT_FORMS = {'entry': (Entry, entry_data), 'concept': (Concept, concept_data)}


def content_model(model: str) -> type[Model]:
    return CONTENT_FORMS[model][0]


def add_content(
    admin_client: Client, model: str, subtopic: Subtopic, /, **changes: str
) -> HttpResponse:
    data = CONTENT_FORMS[model][1](subtopic, **changes)
    return admin_client.post(reverse(f'admin:app_content_{model}_add'), data)


@pytest.mark.parametrize('fixture', CONTENT)
def test_content_list_shows_title_topic_and_subtopic(
    admin_client: Client, request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    response = admin_client.get(reverse(f'admin:app_content_{fixture}_changelist'))
    content = response.content.decode()
    assert response.status_code == 200
    assert all(text in content for text in (obj.title_de, 'Python', 'Schleifen'))


@pytest.mark.parametrize('model', CONTENT)
def test_content_add_page_has_language_tabs(admin_client: Client, model: str) -> None:
    response = admin_client.get(reverse(f'admin:app_content_{model}_add'))
    fields = response.context['adminform'].form.fields
    assert {'title_de', 'title_en', 'code_de', 'code_en'} <= set(fields)


@pytest.mark.parametrize('model', CONTENT)
def test_content_subtopic_choices_name_topic(
    admin_client: Client, group: Group, subtopic: Subtopic, model: str
) -> None:
    git = Topic.objects.create(group=group, slug='git', name_de='Git', position=-1)
    Subtopic.objects.create(topic=git, slug='alltag', name_de='Alltag')
    response = admin_client.get(reverse(f'admin:app_content_{model}_add'))
    choices = response.context['adminform'].form.fields['subtopic'].choices
    assert [label for value, label in choices if value] == ['Git – Alltag', 'Python – Schleifen']


def test_admin_adds_entry_with_one_code(admin_client: Client, subtopic: Subtopic) -> None:
    response = add_content(admin_client, 'entry', subtopic)
    entry = Entry.objects.get(slug='git-status')
    assert response.status_code == 302
    assert (entry.subtopic, entry.os_code) == (subtopic, 'git status')


def test_admin_adds_entry_with_unix_code(admin_client: Client, subtopic: Subtopic) -> None:
    add_content(admin_client, 'entry', subtopic, code_de='dir', code_unix_de='ls')
    assert Entry.objects.get(slug='git-status').os_code == {'win': 'dir', 'unix': 'ls'}


def test_admin_adds_concept_without_note(admin_client: Client, subtopic: Subtopic) -> None:
    response = add_content(admin_client, 'concept', subtopic)
    assert response.status_code == 302
    assert not Concept.objects.get(slug='while-schleife').note


@pytest.mark.parametrize('model', CONTENT)
@pytest.mark.parametrize('field', ['title_de', 'code_de'])
def test_admin_requires_german_texts(
    admin_client: Client, subtopic: Subtopic, model: str, field: str
) -> None:
    response = add_content(admin_client, model, subtopic, **{field: ''})
    assert form_error_codes(response, field) == ['required']
    assert not content_model(model).objects.exists()


@pytest.mark.parametrize('model', CONTENT)
@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Git_Status', 'invalid'),
        ('language', 'cobol', 'invalid_choice'),
        ('subtopic', '999999', 'invalid_choice'),
    ],
)
def test_admin_rejects_invalid_values(
    admin_client: Client, subtopic: Subtopic, model: str, field: str, value: str, code: str
) -> None:
    response = add_content(admin_client, model, subtopic, **{field: value})
    assert form_error_codes(response, field) == [code]
    assert not content_model(model).objects.exists()


@pytest.mark.parametrize('model', CONTENT)
def test_admin_rejects_duplicate_content_slug(
    admin_client: Client, entry: Entry, concept: Concept, model: str
) -> None:
    response = add_content(admin_client, model, entry.subtopic, slug='for-schleife')
    assert form_error_codes(response, 'slug') == ['unique']
    assert content_model(model).objects.count() == 1


@pytest.mark.parametrize('fixture', CONTENT)
def test_content_change_page_loads(
    admin_client: Client, request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    response = admin_client.get(reverse(f'admin:app_content_{fixture}_change', args=[obj.pk]))
    assert response.status_code == 200
    assert obj.title_de in response.content.decode()


def test_admin_changes_entry(admin_client: Client, entry: Entry) -> None:
    data = entry_data(entry.subtopic, slug=entry.slug, title_de='Neuer Titel')
    url = reverse('admin:app_content_entry_change', args=[entry.pk])
    response = admin_client.post(url, data)
    entry.refresh_from_db()
    assert response.status_code == 302
    assert entry.title_de == 'Neuer Titel'


@pytest.mark.parametrize('fixture', CONTENT)
def test_admin_deletes_content(
    admin_client: Client, request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    url = reverse(f'admin:app_content_{fixture}_delete', args=[obj.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not type(obj).objects.exists()
    assert Subtopic.objects.filter(pk=obj.subtopic.pk).exists()


@pytest.mark.parametrize('model', CONTENT)
def test_content_list_filters_by_topic_and_subtopic(
    admin_client: Client, group: Group, subtopic: Subtopic, model: str
) -> None:
    git = Topic.objects.create(group=group, slug='git', name_de='Git')
    alltag = Subtopic.objects.create(topic=git, slug='alltag', name_de='Alltag')
    wanted = content_model(model).objects.create(
        subtopic=subtopic, language='python', slug='for', title_de='for'
    )
    content_model(model).objects.create(
        subtopic=alltag, language='python', slug='status', title_de='status'
    )
    url = reverse(f'admin:app_content_{model}_changelist')
    by_topic = admin_client.get(url, {'subtopic__topic__id__exact': subtopic.topic.pk})
    by_subtopic = admin_client.get(url, {'subtopic__id__exact': subtopic.pk})
    assert list(by_topic.context['cl'].result_list) == [wanted]
    assert list(by_subtopic.context['cl'].result_list) == [wanted]


@pytest.mark.parametrize('model', CONTENT)
def test_content_list_searches_by_title(
    admin_client: Client, subtopic: Subtopic, model: str
) -> None:
    wanted = content_model(model).objects.create(
        subtopic=subtopic, language='python', slug='stash', title_de='Stash'
    )
    content_model(model).objects.create(
        subtopic=subtopic, language='python', slug='merge', title_de='Merge'
    )
    url = reverse(f'admin:app_content_{model}_changelist')
    response = admin_client.get(url, {'q': 'stash'})
    assert list(response.context['cl'].result_list) == [wanted]


@pytest.mark.parametrize('model', CONTENT)
def test_staff_with_view_permission_cannot_add_content(
    staff_client: Client, staff_user: User, subtopic: Subtopic, model: str
) -> None:
    staff_user.user_permissions.add(Permission.objects.get(codename=f'view_{model}'))
    list_response = staff_client.get(reverse(f'admin:app_content_{model}_changelist'))
    add_response = add_content(staff_client, model, subtopic)
    assert list_response.status_code == 200
    assert add_response.status_code == 403
    assert not content_model(model).objects.exists()


@pytest.mark.parametrize('model', CONTENT)
def test_content_list_escapes_html_in_title(
    admin_client: Client, subtopic: Subtopic, model: str
) -> None:
    script = '<script>alert(1)</script>'
    content_model(model).objects.create(
        subtopic=subtopic, language='python', slug='xss', title_de=script
    )
    response = admin_client.get(reverse(f'admin:app_content_{model}_changelist'))
    content = response.content.decode()
    assert script not in content
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in content


@pytest.mark.parametrize('fixture', CONTENT)
def test_admin_keeps_topic_with_content(
    admin_client: Client, request: pytest.FixtureRequest, fixture: str
) -> None:
    topic = request.getfixturevalue(fixture).subtopic.topic
    url = reverse('admin:app_content_topic_delete', args=[topic.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.context['protected']
    assert Topic.objects.filter(pk=topic.pk).exists()


@pytest.mark.parametrize('fixture', CONTENT)
def test_content_list_saves_position(
    admin_client: Client, request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 1,
        'form-0-id': obj.pk,
        'form-0-position': 7,
        '_save': 'Save',
    }
    response = admin_client.post(reverse(f'admin:app_content_{fixture}_changelist'), data)
    obj.refresh_from_db()
    assert response.status_code == 302
    assert obj.position == 7


def test_admin_changes_concept(admin_client: Client, concept: Concept) -> None:
    data = concept_data(concept.subtopic, slug=concept.slug, note_de='Neuer Hinweis')
    url = reverse('admin:app_content_concept_change', args=[concept.pk])
    response = admin_client.post(url, data)
    concept.refresh_from_db()
    assert response.status_code == 302
    assert concept.note_de == 'Neuer Hinweis'


def test_admin_rejects_unix_code_only_in_english(admin_client: Client, subtopic: Subtopic) -> None:
    response = add_content(admin_client, 'entry', subtopic, code_unix_en='ls')
    assert form_error_codes(response, 'code_unix_de') == ['required']
    assert not Entry.objects.exists()
