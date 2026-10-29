from collections.abc import Iterator
from smtplib import SMTPException

import pytest
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import reverse

from app_accounts.models import User
from app_feedback.models import Suggestion

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('reply_to')]

ANSWER = 'Danke, ist erledigt.'


@pytest.fixture
def reply_to() -> Iterator[None]:
    with override_settings(REPLY_TO_EMAIL='reply@example.com'):
        yield


def answer(client: Client, suggestion: Suggestion, **changes: str) -> HttpResponse:
    url = reverse('admin:app_feedback_suggestion_change', args=[suggestion.pk])
    data = {'status': suggestion.status, 'answer': ANSWER}
    return client.post(url, data | changes)


# Recipient
def test_guest_gets_answer_mail(admin_client: Client, entry_suggestion: Suggestion) -> None:
    answer(admin_client, entry_suggestion)
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ['guest@example.com']
    assert message.from_email == 'noreply@snipatlas.jensbaumann.com'
    assert message.reply_to == ['reply@example.com']
    assert message.subject == 'Antwort auf deine Anfrage bei SnipAtlas'


def test_user_gets_answer_mail_at_account_email(
    admin_client: Client, bug_suggestion: Suggestion, user: User
) -> None:
    User.objects.filter(pk=user.pk).update(email='ada.neu@example.com')
    answer(admin_client, bug_suggestion)
    assert mail.outbox[0].to == ['ada.neu@example.com']


def test_user_without_notify_gets_no_mail(
    admin_client: Client, bug_suggestion: Suggestion, user: User
) -> None:
    User.objects.filter(pk=user.pk).update(notify_by_mail=False)
    answer(admin_client, bug_suggestion)
    bug_suggestion.refresh_from_db()
    assert mail.outbox == []
    assert bug_suggestion.status == 'done'


# Content
def test_answer_mail_contains_subject_and_answer(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    answer(admin_client, entry_suggestion)
    body = mail.outbox[0].body
    assert 'git rebase -i erklären' in body
    assert ANSWER in body
    assert 'Profil' not in body


def test_answer_mail_for_user_points_to_profile(
    admin_client: Client, bug_suggestion: Suggestion
) -> None:
    answer(admin_client, bug_suggestion)
    assert 'Profil' in mail.outbox[0].body


def test_answer_mail_is_plain_text(admin_client: Client, entry_suggestion: Suggestion) -> None:
    entry_suggestion.title = '<b>git</b> & "rebase"'
    entry_suggestion.save()
    answer(admin_client, entry_suggestion, answer='<script>alert(1)</script>')
    message = mail.outbox[0]
    assert message.content_subtype == 'plain'
    assert not getattr(message, 'alternatives', [])
    assert '<script>alert(1)</script>' in message.body
    assert '<b>git</b> & "rebase"' in message.body
    assert '&lt;' not in message.body


def test_answer_mail_subject_ignores_line_breaks_in_request(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    entry_suggestion.title = 'git\nBcc: evil@example.com'
    entry_suggestion.save()
    answer(admin_client, entry_suggestion)
    assert mail.outbox[0].subject == 'Antwort auf deine Anfrage bei SnipAtlas'
    assert mail.outbox[0].bcc == []


# Only the first answer
def test_changing_answer_sends_no_second_mail(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    answer(admin_client, entry_suggestion)
    entry_suggestion.refresh_from_db()
    answer(admin_client, entry_suggestion, answer='Nachtrag: ist online.')
    assert len(mail.outbox) == 1


def test_reopened_answered_suggestion_sends_no_mail(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    answer(admin_client, entry_suggestion)
    answer(admin_client, entry_suggestion, status='open', answer='Doch noch offen.')
    assert len(mail.outbox) == 1


def test_saving_without_answer_sends_no_mail(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    answer(admin_client, entry_suggestion, status='done', answer='')
    assert mail.outbox == []


def test_answer_after_closing_without_answer_sends_mail(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    answer(admin_client, entry_suggestion, status='done', answer='')
    entry_suggestion.refresh_from_db()
    answer(admin_client, entry_suggestion)
    assert len(mail.outbox) == 1


def test_mark_done_action_sends_no_mail(admin_client: Client, entry_suggestion: Suggestion) -> None:
    url = reverse('admin:app_feedback_suggestion_changelist')
    admin_client.post(url, {'action': 'mark_done', '_selected_action': [entry_suggestion.pk]})
    assert mail.outbox == []


def test_saving_answer_outside_admin_sends_no_mail(entry_suggestion: Suggestion) -> None:
    entry_suggestion.answer = ANSWER
    entry_suggestion.save()
    assert mail.outbox == []


# Errors and rights
def test_invalid_admin_form_sends_no_mail(
    admin_client: Client, entry_suggestion: Suggestion
) -> None:
    answer(admin_client, entry_suggestion, status='closed')
    assert mail.outbox == []


def test_staff_with_view_permission_sends_no_mail(
    staff_client: Client, staff_user: User, entry_suggestion: Suggestion
) -> None:
    staff_user.user_permissions.add(Permission.objects.get(codename='view_suggestion'))
    answer(staff_client, entry_suggestion)
    assert mail.outbox == []


def test_failed_mail_keeps_suggestion_unanswered(
    admin_client: Client, entry_suggestion: Suggestion, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(self: EmailMessage, fail_silently: bool = False) -> int:
        raise SMTPException

    monkeypatch.setattr(EmailMessage, 'send', fail)
    with pytest.raises(SMTPException):
        answer(admin_client, entry_suggestion)
    entry_suggestion.refresh_from_db()
    assert entry_suggestion.answer == ''
    assert entry_suggestion.status == 'open'
