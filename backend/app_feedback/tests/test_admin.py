import pytest
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from app_accounts.models import User
from app_feedback.models import Suggestion

pytestmark = pytest.mark.django_db

LIST_URL = reverse('admin:app_feedback_suggestion_changelist')
ESCAPED = '&lt;script&gt;alert(1)&lt;/script&gt;'


def change_url(suggestion: Suggestion) -> str:
    return reverse('admin:app_feedback_suggestion_change', args=[suggestion.pk])


def answer(client: Client, suggestion: Suggestion, **changes: str) -> HttpResponse:
    data = {'status': suggestion.status, 'answer': 'Danke, ist erledigt.'}
    return client.post(change_url(suggestion), data | changes)


def listed(client: Client, **params: str) -> list[Suggestion]:
    return list(client.get(LIST_URL, params).context['cl'].result_list)


def fieldset_fields(response: HttpResponse) -> list[str]:
    fieldsets = response.context['adminform'].fieldsets
    return [field for _, options in fieldsets for field in options['fields']]


def grant(user: User, *codenames: str) -> None:
    user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))


# Access
def test_suggestion_list_redirects_guest_to_login(client: Client) -> None:
    response = client.get(LIST_URL)
    assert response.status_code == 302
    assert response.url.startswith(reverse('admin:login'))


def test_suggestion_list_redirects_user_without_staff(client: Client, user: User) -> None:
    client.force_login(user)
    assert client.get(LIST_URL).status_code == 302


def test_staff_without_permission_cannot_open_suggestions(
    staff_client: Client, entry_suggestion: Suggestion
) -> None:
    assert staff_client.get(LIST_URL).status_code == 403
    assert staff_client.get(change_url(entry_suggestion)).status_code == 403


def test_staff_with_view_permission_cannot_answer(
    staff_client: Client, staff_user: User, entry_suggestion: Suggestion
) -> None:
    grant(staff_user, 'view_suggestion')
    assert staff_client.get(change_url(entry_suggestion)).status_code == 200
    assert answer(staff_client, entry_suggestion).status_code == 403
    entry_suggestion.refresh_from_db()
    assert entry_suggestion.answer == ''


def test_staff_with_change_permission_can_answer(
    staff_client: Client, staff_user: User, entry_suggestion: Suggestion
) -> None:
    grant(staff_user, 'view_suggestion', 'change_suggestion')
    assert answer(staff_client, entry_suggestion).status_code == 302


def test_nobody_can_add_suggestion_in_admin(admin_client: Client) -> None:
    url = reverse('admin:app_feedback_suggestion_add')
    assert admin_client.get(url).status_code == 403
    assert admin_client.post(url, {'kind': 'improvement'}).status_code == 403


# List
def test_suggestion_list_shows_subject_and_contact(
    admin_client: Client, entry_suggestion: Suggestion, bug_suggestion: Suggestion
) -> None:
    content = admin_client.get(LIST_URL).content.decode()
    assert 'git rebase -i erklären' in content
    assert 'guest@example.com' in content
    assert 'ada@example.com' in content


def test_suggestion_list_shows_open_first(
    admin_client: Client, entry_suggestion: Suggestion, bug_suggestion: Suggestion
) -> None:
    bug_suggestion.status = 'done'
    bug_suggestion.save()
    assert listed(admin_client) == [entry_suggestion, bug_suggestion]


def test_suggestion_list_filters_by_status_and_kind(
    admin_client: Client, entry_suggestion: Suggestion, bug_suggestion: Suggestion
) -> None:
    bug_suggestion.status = 'done'
    bug_suggestion.save()
    assert listed(admin_client, status__exact='open') == [entry_suggestion]
    assert listed(admin_client, kind__exact='bug') == [bug_suggestion]
    assert listed(admin_client, status__exact='open', kind__exact='bug') == []


@pytest.mark.parametrize(
    ('query', 'fixture'),
    [
        ('rebase', 'entry_suggestion'),
        ('interaktives', 'entry_suggestion'),
        ('guest@', 'entry_suggestion'),
        ('Buchstabe', 'bug_suggestion'),
        ('ada@', 'bug_suggestion'),
    ],
)
def test_suggestion_list_searches_subject_text_and_email(
    admin_client: Client,
    entry_suggestion: Suggestion,
    bug_suggestion: Suggestion,
    query: str,
    fixture: str,
) -> None:
    expected = {'entry_suggestion': entry_suggestion, 'bug_suggestion': bug_suggestion}
    assert listed(admin_client, q=query) == [expected[fixture]]


def test_suggestion_list_escapes_html(admin_client: Client, entry_suggestion: Suggestion) -> None:
    entry_suggestion.title = '<script>alert(1)</script>'
    entry_suggestion.save()
    content = admin_client.get(LIST_URL).content.decode()
    assert ESCAPED in content
    assert '<script>alert(1)' not in content


def test_action_marks_suggestions_done(
    admin_client: Client, entry_suggestion: Suggestion, bug_suggestion: Suggestion
) -> None:
    data = {'action': 'mark_done', '_selected_action': [entry_suggestion.pk]}
    admin_client.post(LIST_URL, data)
    entry_suggestion.refresh_from_db()
    bug_suggestion.refresh_from_db()
    assert entry_suggestion.status == 'done'
    assert bug_suggestion.status == 'open'


# Detail
def test_change_page_shows_only_fields_of_its_kind(
    admin_client: Client, entry_suggestion: Suggestion, bug_suggestion: Suggestion
) -> None:
    entry_fields = fieldset_fields(admin_client.get(change_url(entry_suggestion)))
    bug_fields = fieldset_fields(admin_client.get(change_url(bug_suggestion)))
    assert {'topic', 'title', 'reason', 'source'} <= set(entry_fields)
    assert not {'idea', 'bug_type', 'location'} & set(entry_fields)
    assert {'bug_type', 'location', 'problem', 'environment'} <= set(bug_fields)
    assert not {'title', 'idea'} & set(bug_fields)


def test_change_page_shows_improvement_fields(admin_client: Client, user: User) -> None:
    suggestion = Suggestion.objects.create(
        kind='improvement', user=user, area='feature', idea='x' * 30, benefit='Schneller'
    )
    fields = fieldset_fields(admin_client.get(change_url(suggestion)))
    assert {'area', 'idea', 'benefit'} <= set(fields)
    assert not {'title', 'location'} & set(fields)


def test_change_page_only_edits_status_and_answer(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    form = admin_client.get(change_url(entry_suggestion)).context['adminform'].form
    assert set(form.fields) == {'status', 'answer'}


def test_change_page_shows_source_as_text(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    entry_suggestion.source = 'https://evil.example.com/'
    entry_suggestion.save()
    content = admin_client.get(change_url(entry_suggestion)).content.decode()
    assert 'https://evil.example.com/' in content
    assert 'href="https://evil.example.com/"' not in content


def test_change_page_escapes_html(admin_client: Client, bug_suggestion: Suggestion) -> None:
    bug_suggestion.problem = '<script>alert(1)</script>'
    bug_suggestion.save()
    content = admin_client.get(change_url(bug_suggestion)).content.decode()
    assert ESCAPED in content
    assert '<script>alert(1)' not in content


# Answer
def test_admin_answer_marks_suggestion_done(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    response = answer(admin_client, entry_suggestion)
    entry_suggestion.refresh_from_db()
    assert response.status_code == 302
    assert entry_suggestion.answer == 'Danke, ist erledigt.'
    assert entry_suggestion.status == 'done'
    assert entry_suggestion.answered_at is not None


def test_admin_ignores_submitted_fields(admin_client: Client, entry_suggestion: Suggestion) -> None:
    answer(admin_client, entry_suggestion, title='Geändert', email='evil@example.com')
    entry_suggestion.refresh_from_db()
    assert entry_suggestion.title == 'git rebase -i erklären'
    assert entry_suggestion.email == 'guest@example.com'


def test_admin_rejects_invalid_status(admin_client: Client, entry_suggestion: Suggestion) -> None:
    response = answer(admin_client, entry_suggestion, status='closed')
    entry_suggestion.refresh_from_db()
    assert response.status_code == 200
    assert entry_suggestion.answer == ''


def test_admin_can_close_without_answer(admin_client: Client, entry_suggestion: Suggestion) -> None:
    answer(admin_client, entry_suggestion, status='done', answer='')
    entry_suggestion.refresh_from_db()
    assert entry_suggestion.status == 'done'
    assert entry_suggestion.answered_at is None


# Delete
def test_admin_deletes_suggestion(admin_client: Client, entry_suggestion: Suggestion) -> None:
    url = reverse('admin:app_feedback_suggestion_delete', args=[entry_suggestion.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not Suggestion.objects.exists()
