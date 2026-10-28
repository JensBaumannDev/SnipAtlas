import pytest
from django.contrib.auth.models import Permission
from django.db.models import Model
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from app_accounts.models import User
from app_content.models import (
    Blueprint,
    BlueprintCode,
    BlueprintStep,
    Concept,
    DebugGuide,
    Entry,
    ErrorMessage,
    GlossaryAlias,
    GlossaryTerm,
    Group,
    News,
    Subtopic,
    Topic,
)

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
CONTENT_ADMINS = [
    'group',
    'topic',
    'entry',
    'concept',
    'errormessage',
    'debugguide',
    'blueprint',
    'blueprintstep',
    'glossaryterm',
    'news',
]


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


# Errors and debug guides
GUIDE_ADMINS = {'errormessage': 'error_message', 'debugguide': 'debug_guide'}


def error_data(topic: Topic, /, **changes: str) -> dict:
    data = {
        'topic': topic.pk,
        'slug': 'port-in-use',
        'message': 'Error: That port is already in use.',
        'meaning_de': 'Der Port ist belegt.',
        'meaning_en': '',
        'cause_de': 'Ein anderer Server läuft noch.',
        'cause_en': '',
        'language': 'terminal',
        'code_de': 'python manage.py runserver 8001',
        'code_en': '',
        'position': 0,
        'steps-TOTAL_FORMS': 2,
        'steps-INITIAL_FORMS': 0,
        'steps-0-text_de': 'Anderen Port nehmen.',
        'steps-0-text_en': '',
        'steps-0-position': 1,
        'steps-1-text_de': 'Den anderen Server beenden.',
        'steps-1-text_en': '',
        'steps-1-position': 0,
    }
    return data | changes


def guide_data(**changes: str) -> dict:
    data = {
        'topic': '',
        'slug': 'debugger',
        'label_de': 'Debugger',
        'label_en': '',
        'title_de': 'Mit dem Debugger arbeiten',
        'title_en': '',
        'summary_de': 'Code Zeile für Zeile ansehen.',
        'summary_en': '',
        'position': 0,
        'steps-TOTAL_FORMS': 1,
        'steps-INITIAL_FORMS': 0,
        'steps-0-title_de': 'Haltepunkt setzen',
        'steps-0-title_en': '',
        'steps-0-text_de': 'Links neben die Zeile klicken.',
        'steps-0-text_en': '',
        'steps-0-language': '',
        'steps-0-code_de': '',
        'steps-0-code_en': '',
        'steps-0-code_unix_de': '',
        'steps-0-code_unix_en': '',
        'steps-0-position': 0,
    }
    return data | changes


def add_error(admin_client: Client, topic: Topic, /, **changes: str) -> HttpResponse:
    url = reverse('admin:app_content_errormessage_add')
    return admin_client.post(url, error_data(topic, **changes))


def add_guide(admin_client: Client, /, **changes: str) -> HttpResponse:
    return admin_client.post(reverse('admin:app_content_debugguide_add'), guide_data(**changes))


def step_error_codes(response: HttpResponse, field: str) -> list[str]:
    form = response.context['inline_admin_formsets'][0].formset.forms[0]
    return [error.code for error in form.errors.as_data()[field]]


@pytest.mark.parametrize(('model', 'fixture'), GUIDE_ADMINS.items())
def test_error_and_guide_change_page_shows_steps(
    admin_client: Client, request: pytest.FixtureRequest, model: str, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    response = admin_client.get(reverse(f'admin:app_content_{model}_change', args=[obj.pk]))
    formset = response.context['inline_admin_formsets'][0].formset
    assert response.status_code == 200
    assert {'text_de', 'text_en'} <= set(formset.forms[0].fields)
    assert len(formset.forms) == 3


@pytest.mark.parametrize(('model', 'fixture'), GUIDE_ADMINS.items())
def test_error_and_guide_list_saves_position(
    admin_client: Client, request: pytest.FixtureRequest, model: str, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 1,
        'form-0-id': obj.pk,
        'form-0-position': 4,
        '_save': 'Save',
    }
    response = admin_client.post(reverse(f'admin:app_content_{model}_changelist'), data)
    obj.refresh_from_db()
    assert response.status_code == 302
    assert obj.position == 4


@pytest.mark.parametrize(('model', 'fixture'), GUIDE_ADMINS.items())
def test_admin_deletes_error_and_guide_with_steps(
    admin_client: Client, request: pytest.FixtureRequest, model: str, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    url = reverse(f'admin:app_content_{model}_delete', args=[obj.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not type(obj).objects.exists()
    assert not type(obj).steps.rel.related_model.objects.exists()


@pytest.mark.parametrize(('model', 'fixture'), GUIDE_ADMINS.items())
def test_staff_with_view_permission_cannot_change_error_or_guide(
    staff_client: Client,
    staff_user: User,
    request: pytest.FixtureRequest,
    model: str,
    fixture: str,
) -> None:
    obj = request.getfixturevalue(fixture)
    staff_user.user_permissions.add(Permission.objects.get(codename=f'view_{model}'))
    url = reverse(f'admin:app_content_{model}_change', args=[obj.pk])
    assert staff_client.get(url).status_code == 200
    assert staff_client.post(url, {'slug': 'neu'}).status_code == 403
    assert type(obj).objects.get(pk=obj.pk).slug == obj.slug


@pytest.mark.parametrize('fixture', ['error_message', 'topic_guide'])
def test_admin_keeps_topic_with_errors_or_guides(
    admin_client: Client, request: pytest.FixtureRequest, fixture: str
) -> None:
    topic = request.getfixturevalue(fixture).topic
    url = reverse('admin:app_content_topic_delete', args=[topic.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.context['protected']
    assert Topic.objects.filter(pk=topic.pk).exists()


# Errors
def test_error_list_shows_message_and_topic(
    admin_client: Client, error_message: ErrorMessage
) -> None:
    response = admin_client.get(reverse('admin:app_content_errormessage_changelist'))
    content = response.content.decode()
    assert response.status_code == 200
    assert all(text in content for text in ('ModuleNotFoundError', 'Python'))


def test_error_add_page_has_language_tabs(admin_client: Client) -> None:
    response = admin_client.get(reverse('admin:app_content_errormessage_add'))
    fields = response.context['adminform'].form.fields
    assert {'meaning_de', 'meaning_en', 'code_de', 'code_en', 'message'} <= set(fields)
    assert 'message_en' not in fields


def test_admin_adds_error_with_steps(admin_client: Client, topic: Topic) -> None:
    response = add_error(admin_client, topic)
    error = ErrorMessage.objects.get(slug='port-in-use')
    assert response.status_code == 302
    assert (error.topic, error.language, error.code) == (topic, 'terminal', error.code_de)
    texts = [step.text for step in error.steps.all()]
    assert texts == ['Den anderen Server beenden.', 'Anderen Port nehmen.']


def test_admin_adds_error_without_solution(admin_client: Client, topic: Topic) -> None:
    response = add_error(admin_client, topic, language='', code_de='')
    assert response.status_code == 302
    assert not ErrorMessage.objects.get(slug='port-in-use').code


@pytest.mark.parametrize('field', ['message', 'meaning_de', 'cause_de'])
def test_admin_requires_error_texts(admin_client: Client, topic: Topic, field: str) -> None:
    response = add_error(admin_client, topic, **{field: ''})
    assert form_error_codes(response, field) == ['required']
    assert not ErrorMessage.objects.exists()


@pytest.mark.parametrize(
    ('changes', 'field'),
    [({'code_de': ''}, 'code_de'), ({'language': ''}, 'language')],
)
def test_admin_requires_language_and_code_together(
    admin_client: Client, topic: Topic, changes: dict, field: str
) -> None:
    response = add_error(admin_client, topic, **changes)
    assert form_error_codes(response, field) == ['required']
    assert not ErrorMessage.objects.exists()


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Port_In_Use', 'invalid'),
        ('language', 'cobol', 'invalid_choice'),
        ('topic', '999999', 'invalid_choice'),
        ('message', 'x' * 301, 'max_length'),
    ],
)
def test_admin_rejects_invalid_error_values(
    admin_client: Client, topic: Topic, field: str, value: str, code: str
) -> None:
    response = add_error(admin_client, topic, **{field: value})
    assert code in form_error_codes(response, field)
    assert not ErrorMessage.objects.exists()


def test_admin_rejects_duplicate_error_slug(
    admin_client: Client, error_message: ErrorMessage
) -> None:
    response = add_error(admin_client, error_message.topic, slug='module-not-found')
    assert form_error_codes(response, 'slug') == ['unique']
    assert ErrorMessage.objects.count() == 1


def test_admin_requires_error_step_text(admin_client: Client, topic: Topic) -> None:
    response = add_error(admin_client, topic, **{'steps-0-text_de': ''})
    assert step_error_codes(response, 'text_de') == ['required']
    assert not ErrorMessage.objects.exists()


def test_admin_changes_error(admin_client: Client, error_message: ErrorMessage) -> None:
    changes = {'slug': error_message.slug, 'steps-TOTAL_FORMS': 0}
    url = reverse('admin:app_content_errormessage_change', args=[error_message.pk])
    response = admin_client.post(url, error_data(error_message.topic, **changes))
    error_message.refresh_from_db()
    assert response.status_code == 302
    assert error_message.message == 'Error: That port is already in use.'


def test_error_list_filters_by_topic(
    admin_client: Client, group: Group, error_message: ErrorMessage
) -> None:
    git = Topic.objects.create(group=group, slug='git', name_de='Git')
    ErrorMessage.objects.create(topic=git, slug='push', message='rejected')
    url = reverse('admin:app_content_errormessage_changelist')
    response = admin_client.get(url, {'topic__id__exact': error_message.topic.pk})
    assert list(response.context['cl'].result_list) == [error_message]


def test_error_list_searches_by_message(admin_client: Client, error_message: ErrorMessage) -> None:
    ErrorMessage.objects.create(topic=error_message.topic, slug='port', message='Port in use')
    url = reverse('admin:app_content_errormessage_changelist')
    response = admin_client.get(url, {'q': 'modulenotfound'})
    assert list(response.context['cl'].result_list) == [error_message]


def test_error_list_escapes_html_in_message(admin_client: Client, topic: Topic) -> None:
    ErrorMessage.objects.create(topic=topic, slug='xss', message='<script>alert(1)</script>')
    response = admin_client.get(reverse('admin:app_content_errormessage_changelist'))
    content = response.content.decode()
    assert '<script>alert(1)</script>' not in content
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in content


# Debug guides
def test_debug_guide_list_shows_title_and_label(
    admin_client: Client, debug_guide: DebugGuide, topic_guide: DebugGuide
) -> None:
    response = admin_client.get(reverse('admin:app_content_debugguide_changelist'))
    content = response.content.decode()
    assert response.status_code == 200
    assert all(text in content for text in ('Der Ablauf', 'Vorgehen', 'Python debuggen'))


def test_admin_adds_general_debug_guide(admin_client: Client, db: None) -> None:
    response = add_guide(admin_client)
    guide = DebugGuide.objects.get(slug='debugger')
    assert response.status_code == 302
    assert (guide.topic, guide.label) == (None, 'Debugger')
    assert guide.steps.get().title == 'Haltepunkt setzen'


def test_admin_adds_topic_debug_guide(admin_client: Client, topic: Topic) -> None:
    response = add_guide(admin_client, topic=topic.pk, label_de='')
    assert response.status_code == 302
    assert DebugGuide.objects.get(slug='debugger').topic == topic


def test_admin_requires_label_for_general_guide(admin_client: Client, db: None) -> None:
    response = add_guide(admin_client, label_de='')
    assert form_error_codes(response, 'label_de') == ['required']
    assert not DebugGuide.objects.exists()


def test_admin_rejects_label_for_topic_guide(admin_client: Client, topic: Topic) -> None:
    response = add_guide(admin_client, topic=topic.pk)
    assert form_error_codes(response, 'label_de') == ['invalid']
    assert not DebugGuide.objects.exists()


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Der_Debugger', 'invalid'),
        ('topic', '999999', 'invalid_choice'),
        ('label_de', 'x' * 31, 'max_length'),
        ('title_de', '', 'required'),
        ('summary_de', '', 'required'),
    ],
)
def test_admin_rejects_invalid_guide_values(
    admin_client: Client, db: None, field: str, value: str, code: str
) -> None:
    response = add_guide(admin_client, **{field: value})
    assert code in form_error_codes(response, field)
    assert not DebugGuide.objects.exists()


def test_admin_adds_guide_step_with_unix_code(admin_client: Client, db: None) -> None:
    changes = {
        'steps-0-language': 'terminal',
        'steps-0-code_de': 'dir',
        'steps-0-code_unix_de': 'ls',
    }
    add_guide(admin_client, **changes)
    step = DebugGuide.objects.get(slug='debugger').steps.get()
    assert step.os_code == {'win': 'dir', 'unix': 'ls'}


@pytest.mark.parametrize(
    ('changes', 'field'),
    [
        ({'steps-0-code_de': 'dir'}, 'language'),
        ({'steps-0-language': 'terminal'}, 'code_de'),
        ({'steps-0-code_unix_de': 'ls'}, 'code_de'),
        ({'steps-0-title_de': ''}, 'title_de'),
    ],
)
def test_admin_checks_guide_steps(
    admin_client: Client, db: None, changes: dict, field: str
) -> None:
    response = add_guide(admin_client, **changes)
    assert step_error_codes(response, field) == ['required']
    assert not DebugGuide.objects.exists()


def test_debug_guide_list_filters_general_guides(
    admin_client: Client, debug_guide: DebugGuide, topic_guide: DebugGuide
) -> None:
    url = reverse('admin:app_content_debugguide_changelist')
    general = admin_client.get(url, {'topic__isnull': 'True'})
    by_topic = admin_client.get(url, {'topic__id__exact': topic_guide.topic.pk})
    assert list(general.context['cl'].result_list) == [debug_guide]
    assert list(by_topic.context['cl'].result_list) == [topic_guide]


def test_debug_guide_list_searches_by_title(
    admin_client: Client, debug_guide: DebugGuide, topic_guide: DebugGuide
) -> None:
    url = reverse('admin:app_content_debugguide_changelist')
    response = admin_client.get(url, {'q': 'ablauf'})
    assert list(response.context['cl'].result_list) == [debug_guide]


# Changes and escaping
def test_admin_rejects_duplicate_guide_slug(admin_client: Client, debug_guide: DebugGuide) -> None:
    response = add_guide(admin_client, slug='vorgehen')
    assert form_error_codes(response, 'slug') == ['unique']
    assert DebugGuide.objects.count() == 1


def test_admin_changes_debug_guide(admin_client: Client, debug_guide: DebugGuide) -> None:
    data = guide_data(slug='vorgehen', title_de='Neuer Ablauf', **{'steps-TOTAL_FORMS': 0})
    url = reverse('admin:app_content_debugguide_change', args=[debug_guide.pk])
    response = admin_client.post(url, data)
    debug_guide.refresh_from_db()
    assert response.status_code == 302
    assert debug_guide.title_de == 'Neuer Ablauf'
    assert debug_guide.steps.count() == 2


def test_admin_rejects_topic_guide_turned_general_without_label(
    admin_client: Client, topic_guide: DebugGuide
) -> None:
    changes = {'slug': 'python-debuggen', 'label_de': '', 'steps-TOTAL_FORMS': 0}
    url = reverse('admin:app_content_debugguide_change', args=[topic_guide.pk])
    response = admin_client.post(url, guide_data(**changes))
    topic_guide.refresh_from_db()
    assert form_error_codes(response, 'label_de') == ['required']
    assert topic_guide.topic is not None


def existing_steps(error: ErrorMessage) -> dict:
    data = {'steps-TOTAL_FORMS': 2, 'steps-INITIAL_FORMS': 2}
    for index, step in enumerate(error.steps.all()):
        prefix = f'steps-{index}-'
        data |= {f'{prefix}id': step.pk, f'{prefix}error': error.pk}
        data |= {f'{prefix}text_de': step.text_de, f'{prefix}position': step.position}
    return data


def test_admin_deletes_single_error_step(admin_client: Client, error_message: ErrorMessage) -> None:
    changes = existing_steps(error_message) | {'slug': error_message.slug, 'steps-0-DELETE': 'on'}
    url = reverse('admin:app_content_errormessage_change', args=[error_message.pk])
    response = admin_client.post(url, error_data(error_message.topic, **changes))
    assert response.status_code == 302
    assert [step.text for step in error_message.steps.all()] == ['Paket installieren.']


SCRIPT = '<script>alert(1)</script>'
ESCAPED = '&lt;script&gt;alert(1)&lt;/script&gt;'


def test_debug_guide_list_escapes_html_in_title(admin_client: Client, db: None) -> None:
    DebugGuide.objects.create(slug='xss', label_de='XSS', title_de=SCRIPT)
    content = admin_client.get(reverse('admin:app_content_debugguide_changelist')).content
    assert SCRIPT not in content.decode()
    assert ESCAPED in content.decode()


@pytest.mark.parametrize(('model', 'fixture'), GUIDE_ADMINS.items())
def test_change_page_escapes_html_in_steps(
    admin_client: Client, request: pytest.FixtureRequest, model: str, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    obj.steps.update(text_de=SCRIPT)
    url = reverse(f'admin:app_content_{model}_change', args=[obj.pk])
    content = admin_client.get(url).content.decode()
    assert SCRIPT not in content
    assert ESCAPED in content


# Blueprints
BLUEPRINT_ADMINS = {'blueprint': 'blueprint', 'blueprintstep': 'venv_step'}


def blueprint_data(topic: Topic, /, **changes: str) -> dict:
    data = {
        'topic': topic.pk,
        'slug': 'angular-projekt',
        'title_de': 'Neues Angular-Projekt',
        'title_en': '',
        'summary_de': 'Vom leeren Ordner bis zur ersten Komponente.',
        'summary_en': '',
        'position': 0,
        'steps-TOTAL_FORMS': 2,
        'steps-INITIAL_FORMS': 0,
    }
    for index, (slug, position) in enumerate([('cli-installieren', 1), ('ordner-anlegen', 0)]):
        prefix = f'steps-{index}-'
        data |= {f'{prefix}slug': slug, f'{prefix}title_de': slug, f'{prefix}title_en': ''}
        data |= {f'{prefix}why_de': 'Weil.', f'{prefix}why_en': '', f'{prefix}note_de': ''}
        data |= {f'{prefix}note_en': '', f'{prefix}position': position}
    return data | changes


def step_data(blueprint: Blueprint, /, **changes: str) -> dict:
    data = {
        'blueprint': blueprint.pk,
        'slug': 'server-starten',
        'title_de': 'Server starten',
        'title_en': '',
        'why_de': 'Zeigt die Seite im Browser.',
        'why_en': '',
        'note_de': '',
        'note_en': '',
        'position': 5,
        'codes-TOTAL_FORMS': 1,
        'codes-INITIAL_FORMS': 0,
        'codes-0-language': 'terminal',
        'codes-0-code_de': 'python manage.py runserver',
        'codes-0-code_en': '',
        'codes-0-code_unix_de': '',
        'codes-0-code_unix_en': '',
        'codes-0-position': 0,
    }
    return data | changes


def add_blueprint(admin_client: Client, topic: Topic, /, **changes: str) -> HttpResponse:
    url = reverse('admin:app_content_blueprint_add')
    return admin_client.post(url, blueprint_data(topic, **changes))


def add_step(admin_client: Client, blueprint: Blueprint, /, **changes: str) -> HttpResponse:
    url = reverse('admin:app_content_blueprintstep_add')
    return admin_client.post(url, step_data(blueprint, **changes))


def test_admin_adds_blueprint_with_steps(admin_client: Client, topic: Topic) -> None:
    response = add_blueprint(admin_client, topic)
    blueprint = Blueprint.objects.get(slug='angular-projekt')
    assert response.status_code == 302
    assert blueprint.topic == topic
    assert [step.slug for step in blueprint.steps.all()] == ['ordner-anlegen', 'cli-installieren']


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Angular_Projekt', 'invalid'),
        ('topic', '999999', 'invalid_choice'),
        ('title_de', '', 'required'),
        ('title_de', 'x' * 121, 'max_length'),
        ('summary_de', '', 'required'),
    ],
)
def test_admin_rejects_invalid_blueprint_values(
    admin_client: Client, topic: Topic, field: str, value: str, code: str
) -> None:
    response = add_blueprint(admin_client, topic, **{field: value})
    assert form_error_codes(response, field) == [code]
    assert not Blueprint.objects.exists()


def test_admin_rejects_duplicate_blueprint_slug(admin_client: Client, blueprint: Blueprint) -> None:
    response = add_blueprint(admin_client, blueprint.topic, slug='django-projekt-anlegen')
    assert form_error_codes(response, 'slug') == ['unique']
    assert Blueprint.objects.count() == 1


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [('slug', 'Ordner_Anlegen', 'invalid'), ('why_de', '', 'required')],
)
def test_admin_checks_blueprint_steps(
    admin_client: Client, topic: Topic, field: str, value: str, code: str
) -> None:
    response = add_blueprint(admin_client, topic, **{f'steps-0-{field}': value})
    assert step_error_codes(response, field) == [code]
    assert not Blueprint.objects.exists()


def test_admin_rejects_duplicate_step_slugs_in_blueprint(
    admin_client: Client, topic: Topic
) -> None:
    response = add_blueprint(admin_client, topic, **{'steps-1-slug': 'cli-installieren'})
    formset = response.context['inline_admin_formsets'][0].formset
    assert formset.non_form_errors()
    assert not Blueprint.objects.exists()


def test_blueprint_change_page_links_to_steps(
    admin_client: Client, blueprint: Blueprint, venv_step: BlueprintStep
) -> None:
    response = admin_client.get(reverse('admin:app_content_blueprint_change', args=[blueprint.pk]))
    step_url = reverse('admin:app_content_blueprintstep_change', args=[venv_step.pk])
    assert response.status_code == 200
    assert step_url in response.content.decode()


def test_admin_changes_blueprint(admin_client: Client, blueprint: Blueprint) -> None:
    changes = {'slug': blueprint.slug, 'title_de': 'Django-Projekt', 'steps-TOTAL_FORMS': 0}
    url = reverse('admin:app_content_blueprint_change', args=[blueprint.pk])
    response = admin_client.post(url, blueprint_data(blueprint.topic, **changes))
    blueprint.refresh_from_db()
    assert response.status_code == 302
    assert (blueprint.title_de, blueprint.steps.count()) == ('Django-Projekt', 2)


def test_admin_adds_step_with_code(admin_client: Client, blueprint: Blueprint) -> None:
    response = add_step(admin_client, blueprint, **{'codes-0-code_unix_de': 'python3 -m venv'})
    step = blueprint.steps.get(slug='server-starten')
    assert response.status_code == 302
    assert step.codes.get().os_code == {
        'win': 'python manage.py runserver',
        'unix': 'python3 -m venv',
    }


def test_admin_adds_step_without_code(admin_client: Client, blueprint: Blueprint) -> None:
    response = add_step(admin_client, blueprint, **{'codes-0-language': '', 'codes-0-code_de': ''})
    assert response.status_code == 302
    assert not blueprint.steps.get(slug='server-starten').codes.exists()


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Server_Starten', 'invalid'),
        ('blueprint', '999999', 'invalid_choice'),
        ('title_de', '', 'required'),
        ('why_de', '', 'required'),
    ],
)
def test_admin_rejects_invalid_step_values(
    admin_client: Client, blueprint: Blueprint, field: str, value: str, code: str
) -> None:
    response = add_step(admin_client, blueprint, **{field: value})
    assert form_error_codes(response, field) == [code]
    assert not blueprint.steps.filter(position=5).exists()


def test_admin_rejects_duplicate_step_slug(admin_client: Client, blueprint: Blueprint) -> None:
    response = add_step(admin_client, blueprint, slug='ordner-anlegen')
    assert form_error_codes(response, '__all__') == ['unique_together']
    assert blueprint.steps.count() == 2


@pytest.mark.parametrize(
    ('changes', 'field'),
    [
        ({'codes-0-language': ''}, 'language'),
        ({'codes-0-code_de': ''}, 'code_de'),
        ({'codes-0-code_unix_en': 'ls'}, 'code_unix_de'),
    ],
)
def test_admin_checks_step_codes(
    admin_client: Client, blueprint: Blueprint, changes: dict, field: str
) -> None:
    response = add_step(admin_client, blueprint, **changes)
    assert step_error_codes(response, field) == ['required']
    assert not blueprint.steps.filter(slug='server-starten').exists()


def test_admin_changes_step(admin_client: Client, venv_step: BlueprintStep) -> None:
    changes = {'slug': venv_step.slug, 'title_de': 'venv anlegen', 'codes-TOTAL_FORMS': 0}
    url = reverse('admin:app_content_blueprintstep_change', args=[venv_step.pk])
    response = admin_client.post(url, step_data(venv_step.blueprint, **changes))
    venv_step.refresh_from_db()
    assert response.status_code == 302
    assert (venv_step.title_de, venv_step.codes.count()) == ('venv anlegen', 1)


def test_admin_deletes_step_but_keeps_blueprint(
    admin_client: Client, venv_step: BlueprintStep
) -> None:
    url = reverse('admin:app_content_blueprintstep_delete', args=[venv_step.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert list(venv_step.blueprint.steps.values_list('slug', flat=True)) == ['ordner-anlegen']


def test_admin_deletes_blueprint_with_steps_and_codes(
    admin_client: Client, blueprint: Blueprint
) -> None:
    url = reverse('admin:app_content_blueprint_delete', args=[blueprint.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not Blueprint.objects.exists()
    assert not BlueprintCode.objects.exists()


def test_admin_keeps_topic_with_blueprints(admin_client: Client, blueprint: Blueprint) -> None:
    url = reverse('admin:app_content_topic_delete', args=[blueprint.topic.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.context['protected']
    assert Topic.objects.filter(pk=blueprint.topic.pk).exists()


@pytest.mark.parametrize(('model', 'fixture'), BLUEPRINT_ADMINS.items())
def test_blueprint_lists_save_position(
    admin_client: Client, request: pytest.FixtureRequest, model: str, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 1,
        'form-0-id': obj.pk,
        'form-0-position': 8,
        '_save': 'Save',
    }
    response = admin_client.post(reverse(f'admin:app_content_{model}_changelist'), data)
    obj.refresh_from_db()
    assert response.status_code == 302
    assert obj.position == 8


@pytest.mark.parametrize(('model', 'fixture'), BLUEPRINT_ADMINS.items())
def test_staff_with_view_permission_cannot_change_blueprint_parts(
    staff_client: Client,
    staff_user: User,
    request: pytest.FixtureRequest,
    model: str,
    fixture: str,
) -> None:
    obj = request.getfixturevalue(fixture)
    staff_user.user_permissions.add(Permission.objects.get(codename=f'view_{model}'))
    url = reverse(f'admin:app_content_{model}_change', args=[obj.pk])
    assert staff_client.get(url).status_code == 200
    assert staff_client.post(url, {'slug': 'neu'}).status_code == 403
    assert type(obj).objects.get(pk=obj.pk).slug == obj.slug


def test_blueprint_list_filters_and_searches(
    admin_client: Client, group: Group, blueprint: Blueprint
) -> None:
    git = Topic.objects.create(group=group, slug='git', name_de='Git')
    Blueprint.objects.create(topic=git, slug='repo', title_de='Repository anlegen')
    url = reverse('admin:app_content_blueprint_changelist')
    by_topic = admin_client.get(url, {'topic__id__exact': blueprint.topic.pk})
    by_search = admin_client.get(url, {'q': 'django-projekt'})
    assert list(by_topic.context['cl'].result_list) == [blueprint]
    assert list(by_search.context['cl'].result_list) == [blueprint]


def test_step_list_shows_blueprint_and_filters(
    admin_client: Client, blueprint: Blueprint, venv_step: BlueprintStep
) -> None:
    other = Blueprint.objects.create(topic=blueprint.topic, slug='andere', title_de='Andere')
    other.steps.create(slug='umgebung', title_de='Umgebung')
    url = reverse('admin:app_content_blueprintstep_changelist')
    by_blueprint = admin_client.get(url, {'blueprint__id__exact': blueprint.pk})
    by_search = admin_client.get(url, {'q': 'virtuelle'})
    assert 'Neues Django-Projekt anlegen' in by_blueprint.content.decode()
    assert len(by_blueprint.context['cl'].result_list) == 2
    assert list(by_search.context['cl'].result_list) == [venv_step]


@pytest.mark.parametrize('model', BLUEPRINT_ADMINS)
def test_blueprint_lists_escape_html_in_title(
    admin_client: Client, blueprint: Blueprint, model: str
) -> None:
    Blueprint.objects.filter(pk=blueprint.pk).update(title_de=SCRIPT)
    blueprint.steps.update(title_de=SCRIPT)
    content = admin_client.get(reverse(f'admin:app_content_{model}_changelist')).content.decode()
    assert SCRIPT not in content
    assert ESCAPED in content


def test_step_change_page_escapes_html_in_code(
    admin_client: Client, venv_step: BlueprintStep
) -> None:
    venv_step.codes.update(code_de=SCRIPT)
    url = reverse('admin:app_content_blueprintstep_change', args=[venv_step.pk])
    content = admin_client.get(url).content.decode()
    assert SCRIPT not in content
    assert ESCAPED in content


def test_admin_deletes_single_step_code(admin_client: Client, blueprint: Blueprint) -> None:
    step = blueprint.steps.get(slug='ordner-anlegen')
    data = {'slug': step.slug, 'codes-TOTAL_FORMS': 2, 'codes-INITIAL_FORMS': 2}
    for index, code in enumerate(step.codes.all()):
        prefix = f'codes-{index}-'
        data |= {f'{prefix}id': code.pk, f'{prefix}step': step.pk, f'{prefix}language': 'terminal'}
        data |= {f'{prefix}code_de': code.code_de, f'{prefix}position': code.position}
    data['codes-0-DELETE'] = 'on'
    url = reverse('admin:app_content_blueprintstep_change', args=[step.pk])
    response = admin_client.post(url, step_data(blueprint, **data))
    assert response.status_code == 302
    assert [code.code for code in step.codes.all()] == ['cd {{project}}']
    assert blueprint.steps.get(slug='virtuelle-umgebung').codes.count() == 1


def test_admin_deletes_single_step_in_blueprint(admin_client: Client, blueprint: Blueprint) -> None:
    data = {'slug': blueprint.slug, 'steps-TOTAL_FORMS': 2, 'steps-INITIAL_FORMS': 2}
    for index, step in enumerate(blueprint.steps.all()):
        prefix = f'steps-{index}-'
        data |= {f'{prefix}id': step.pk, f'{prefix}blueprint': blueprint.pk}
        data |= {f'{prefix}slug': step.slug, f'{prefix}title_de': step.title_de}
        data |= {f'{prefix}why_de': step.why_de, f'{prefix}position': step.position}
    data['steps-0-DELETE'] = 'on'
    url = reverse('admin:app_content_blueprint_change', args=[blueprint.pk])
    response = admin_client.post(url, blueprint_data(blueprint.topic, **data))
    assert response.status_code == 302
    assert list(blueprint.steps.values_list('slug', flat=True)) == ['virtuelle-umgebung']
    assert list(BlueprintCode.objects.values_list('step__slug', flat=True)) == [
        'virtuelle-umgebung'
    ]


def test_admin_rejects_moving_step_to_blueprint_with_same_slug(
    admin_client: Client, blueprint: Blueprint, venv_step: BlueprintStep
) -> None:
    other = Blueprint.objects.create(topic=blueprint.topic, slug='andere', title_de='Andere')
    other.steps.create(slug='virtuelle-umgebung', title_de='Umgebung')
    changes = {'slug': venv_step.slug, 'codes-TOTAL_FORMS': 0}
    url = reverse('admin:app_content_blueprintstep_change', args=[venv_step.pk])
    response = admin_client.post(url, step_data(other, **changes))
    venv_step.refresh_from_db()
    assert form_error_codes(response, '__all__') == ['unique_together']
    assert venv_step.blueprint == blueprint


# Glossary
@pytest.fixture
def git_topic(group: Group) -> Topic:
    return Topic.objects.create(group=group, slug='git', name_de='Git', position=-1)


def term_data(**changes: object) -> dict:
    data = {
        'slug': 'merge',
        'term_de': 'Merge',
        'term_en': '',
        'definition_de': 'Führt zwei Branches zusammen.',
        'definition_en': '',
        'concept': '',
        'aliases-TOTAL_FORMS': 2,
        'aliases-INITIAL_FORMS': 0,
        'aliases-0-language': 'de',
        'aliases-0-name': 'mergen',
        'aliases-1-language': 'en',
        'aliases-1-name': 'merging',
    }
    return data | changes


def add_term(admin_client: Client, **changes: object) -> HttpResponse:
    return admin_client.post(reverse('admin:app_content_glossaryterm_add'), term_data(**changes))


def test_admin_adds_term_with_aliases(admin_client: Client, concept: Concept) -> None:
    response = add_term(admin_client, concept=concept.pk)
    term = GlossaryTerm.objects.get(slug='merge')
    assert response.status_code == 302
    assert term.concept == concept
    assert list(term.aliases.values_list('language', 'name')) == [
        ('de', 'mergen'),
        ('en', 'merging'),
    ]


def test_admin_adds_term_without_concept_and_aliases(admin_client: Client, db: None) -> None:
    response = add_term(admin_client, **{'aliases-TOTAL_FORMS': 0})
    term = GlossaryTerm.objects.get(slug='merge')
    assert response.status_code == 302
    assert (term.concept, term.aliases.count()) == (None, 0)


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Merge_Branch', 'invalid'),
        ('term_de', '', 'required'),
        ('term_de', 'x' * 61, 'max_length'),
        ('definition_de', '', 'required'),
        ('concept', '999999', 'invalid_choice'),
    ],
)
def test_admin_rejects_invalid_term_values(
    admin_client: Client, db: None, field: str, value: str, code: str
) -> None:
    response = add_term(admin_client, **{field: value})
    assert form_error_codes(response, field) == [code]
    assert not GlossaryTerm.objects.exists()


def test_admin_rejects_duplicate_term_slug(
    admin_client: Client, glossary_term: GlossaryTerm
) -> None:
    response = add_term(admin_client, slug='schleife')
    assert form_error_codes(response, 'slug') == ['unique']
    assert GlossaryTerm.objects.count() == 1


@pytest.mark.parametrize('name', ['mergen', 'MERGEN'])
def test_admin_rejects_same_alias_twice_in_form(admin_client: Client, db: None, name: str) -> None:
    response = add_term(admin_client, **{'aliases-1-language': 'de', 'aliases-1-name': name})
    formset = response.context['inline_admin_formsets'][0].formset
    assert response.status_code == 200
    assert [error.code for error in formset.non_form_errors().as_data()] == ['duplicate']
    assert not GlossaryTerm.objects.exists()


def test_admin_allows_same_alias_in_two_languages(admin_client: Client, db: None) -> None:
    response = add_term(admin_client, **{'aliases-1-name': 'mergen'})
    assert response.status_code == 302
    assert GlossaryTerm.objects.get(slug='merge').aliases.count() == 2


def test_admin_rejects_alias_of_other_term(
    admin_client: Client, glossary_term: GlossaryTerm
) -> None:
    response = add_term(admin_client, **{'aliases-0-name': 'SCHLEIFEN'})
    form = response.context['inline_admin_formsets'][0].formset.forms[0]
    assert response.status_code == 200
    assert form.errors
    assert GlossaryTerm.objects.count() == 1


def test_admin_rejects_alias_with_unknown_language(admin_client: Client, db: None) -> None:
    response = add_term(admin_client, **{'aliases-0-language': 'fr'})
    assert step_error_codes(response, 'language') == ['invalid_choice']
    assert not GlossaryTerm.objects.exists()


def test_admin_changes_term_and_deletes_single_alias(
    admin_client: Client, glossary_term: GlossaryTerm
) -> None:
    data = term_data(slug='schleife', term_de='Schleife', **{'aliases-INITIAL_FORMS': 2})
    for index, alias in enumerate(glossary_term.aliases.all()):
        prefix = f'aliases-{index}-'
        data |= {f'{prefix}id': alias.pk, f'{prefix}term': glossary_term.pk}
        data |= {f'{prefix}language': alias.language, f'{prefix}name': alias.name}
    data['aliases-0-DELETE'] = 'on'
    data['definition_de'] = 'Wiederholt Code, bis eine Bedingung endet.'
    url = reverse('admin:app_content_glossaryterm_change', args=[glossary_term.pk])
    response = admin_client.post(url, data)
    glossary_term.refresh_from_db()
    assert response.status_code == 302
    assert glossary_term.definition_de == 'Wiederholt Code, bis eine Bedingung endet.'
    assert [alias.name for alias in glossary_term.aliases.all()] == ['Schleifen']


def test_admin_deletes_term_with_aliases(admin_client: Client, glossary_term: GlossaryTerm) -> None:
    url = reverse('admin:app_content_glossaryterm_delete', args=[glossary_term.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not GlossaryAlias.objects.exists()
    assert Concept.objects.exists()


def test_admin_deletes_concept_but_keeps_term(
    admin_client: Client, glossary_term: GlossaryTerm
) -> None:
    url = reverse('admin:app_content_concept_delete', args=[glossary_term.concept.pk])
    response = admin_client.post(url, {'post': 'yes'})
    glossary_term.refresh_from_db()
    assert response.status_code == 302
    assert glossary_term.concept is None


def test_term_concept_uses_autocomplete(admin_client: Client, glossary_term: GlossaryTerm) -> None:
    params = {
        'app_label': 'app_content',
        'model_name': 'glossaryterm',
        'field_name': 'concept',
        'term': 'for-schleife',
    }
    response = admin_client.get(reverse('admin:autocomplete'), params)
    assert response.status_code == 200
    assert [item['text'] for item in response.json()['results']] == ['Die for-Schleife']


def test_term_list_searches_term_and_alias(
    admin_client: Client, glossary_term: GlossaryTerm
) -> None:
    GlossaryTerm.objects.create(slug='api', term_de='API')
    url = reverse('admin:app_content_glossaryterm_changelist')
    for query in ('schleife', 'loops'):
        response = admin_client.get(url, {'q': query})
        assert list(response.context['cl'].result_list) == [glossary_term]


def test_term_list_escapes_html(admin_client: Client, db: None) -> None:
    GlossaryTerm.objects.create(slug='xss', term_de=SCRIPT)
    content = admin_client.get(reverse('admin:app_content_glossaryterm_changelist')).content
    assert SCRIPT not in content.decode()
    assert ESCAPED in content.decode()


# News
def news_data(topic: Topic, subtopic: Subtopic | None, /, **changes: object) -> dict:
    data = {
        'date': '2026-10-28',
        'title_de': 'Python: Schleifen',
        'title_en': '',
        'area': 'befehle',
        'topic': topic.pk,
        'subtopic': subtopic.pk if subtopic else '',
    }
    return data | changes


def add_news(
    admin_client: Client, topic: Topic, subtopic: Subtopic | None, /, **changes: object
) -> HttpResponse:
    url = reverse('admin:app_content_news_add')
    return admin_client.post(url, news_data(topic, subtopic, **changes))


def test_admin_adds_news_with_subtopic(admin_client: Client, subtopic: Subtopic) -> None:
    response = add_news(admin_client, subtopic.topic, subtopic)
    news = News.objects.get()
    assert response.status_code == 302
    assert news.link == ['/befehle', 'python', 'schleifen']


def test_admin_adds_news_without_subtopic(admin_client: Client, topic: Topic) -> None:
    response = add_news(admin_client, topic, None, area='fehler')
    assert response.status_code == 302
    assert News.objects.get().link == ['/fehler', 'python']


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('date', '2026-13-45', 'invalid'),
        ('date', '', 'required'),
        ('title_de', '', 'required'),
        ('title_de', 'x' * 121, 'max_length'),
        ('area', 'blog', 'invalid_choice'),
        ('topic', '999999', 'invalid_choice'),
        ('subtopic', '999999', 'invalid_choice'),
    ],
)
def test_admin_rejects_invalid_news_values(
    admin_client: Client, subtopic: Subtopic, field: str, value: str, code: str
) -> None:
    response = add_news(admin_client, subtopic.topic, subtopic, **{field: value})
    assert code in form_error_codes(response, field)
    assert not News.objects.exists()


def test_admin_rejects_subtopic_of_other_topic(
    admin_client: Client, subtopic: Subtopic, git_topic: Topic
) -> None:
    response = add_news(admin_client, git_topic, subtopic)
    assert form_error_codes(response, 'subtopic') == ['invalid']
    assert not News.objects.exists()


@pytest.mark.parametrize('area', ['anleitungen', 'fehler'])
def test_admin_rejects_subtopic_for_area_without_subtopics(
    admin_client: Client, subtopic: Subtopic, area: str
) -> None:
    response = add_news(admin_client, subtopic.topic, subtopic, area=area)
    assert form_error_codes(response, 'subtopic') == ['invalid']
    assert not News.objects.exists()


def test_news_subtopic_choices_name_topic(
    admin_client: Client, subtopic: Subtopic, git_topic: Topic
) -> None:
    Subtopic.objects.create(topic=git_topic, slug='alltag', name_de='Alltag')
    response = admin_client.get(reverse('admin:app_content_news_add'))
    choices = response.context['adminform'].form.fields['subtopic'].choices
    assert [label for value, label in choices if value] == ['Git – Alltag', 'Python – Schleifen']


def test_admin_changes_news(admin_client: Client, news: News) -> None:
    url = reverse('admin:app_content_news_change', args=[news.pk])
    response = admin_client.post(
        url, news_data(news.topic, None, title_de='Neu', area='grundlagen')
    )
    news.refresh_from_db()
    assert response.status_code == 302
    assert (news.title_de, news.link) == ('Neu', ['/grundlagen', 'python'])


def test_admin_deletes_news(admin_client: Client, news: News) -> None:
    url = reverse('admin:app_content_news_delete', args=[news.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not News.objects.exists()
    assert Subtopic.objects.exists()


def test_admin_keeps_subtopic_with_news(admin_client: Client, group: Group, news: News) -> None:
    url = reverse('admin:app_content_topic_delete', args=[news.topic.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.context['protected']
    assert Subtopic.objects.filter(pk=news.subtopic.pk).exists()


def test_news_list_filters_and_searches(admin_client: Client, news: News, git_topic: Topic) -> None:
    other = News.objects.create(
        date=news.date, title_de='Git: Stash', area='fehler', topic=git_topic
    )
    url = reverse('admin:app_content_news_changelist')
    by_area = admin_client.get(url, {'area__exact': 'fehler'})
    by_topic = admin_client.get(url, {'topic__id__exact': news.topic.pk})
    by_search = admin_client.get(url, {'q': 'stash'})
    assert list(by_area.context['cl'].result_list) == [other]
    assert list(by_topic.context['cl'].result_list) == [news]
    assert list(by_search.context['cl'].result_list) == [other]


def test_news_list_escapes_html(admin_client: Client, news: News) -> None:
    News.objects.filter(pk=news.pk).update(title_de=SCRIPT)
    content = admin_client.get(reverse('admin:app_content_news_changelist')).content.decode()
    assert SCRIPT not in content
    assert ESCAPED in content


@pytest.mark.parametrize(
    ('model', 'fixture'), [('glossaryterm', 'glossary_term'), ('news', 'news')]
)
def test_staff_with_view_permission_cannot_change_glossary_or_news(
    staff_client: Client,
    staff_user: User,
    request: pytest.FixtureRequest,
    model: str,
    fixture: str,
) -> None:
    obj = request.getfixturevalue(fixture)
    staff_user.user_permissions.add(Permission.objects.get(codename=f'view_{model}'))
    url = reverse(f'admin:app_content_{model}_change', args=[obj.pk])
    before = model_to_dict(type(obj).objects.get(pk=obj.pk))
    assert staff_client.get(url).status_code == 200
    assert staff_client.post(url, {'title_de': 'Neu', 'term_de': 'Neu'}).status_code == 403
    assert model_to_dict(type(obj).objects.get(pk=obj.pk)) == before
