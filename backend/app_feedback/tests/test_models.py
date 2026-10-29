import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from app_accounts.models import User
from app_content.models import Topic
from app_feedback.models import Suggestion

pytestmark = pytest.mark.django_db

IDEA = 'Eine Suche über alle Bereiche, die auch Aliase findet und Tippfehler verzeiht.'


def improvement(**changes: object) -> Suggestion:
    data = {'kind': 'improvement', 'email': 'guest@example.com', 'area': 'feature', 'idea': IDEA}
    return Suggestion(**(data | changes))


def error_codes(error: ValidationError, field: str) -> list[str]:
    return [item.code for item in error.error_dict[field]]


# Defaults
def test_suggestion_starts_open_without_answer(entry_suggestion: Suggestion) -> None:
    assert entry_suggestion.status == 'open'
    assert entry_suggestion.answer == ''
    assert entry_suggestion.answered_at is None
    assert entry_suggestion.created_at is not None


def test_suggestions_are_ordered_newest_first(
    entry_suggestion: Suggestion, bug_suggestion: Suggestion
) -> None:
    assert list(Suggestion.objects.all()) == [bug_suggestion, entry_suggestion]


# Subject
def test_entry_subject_is_title(entry_suggestion: Suggestion) -> None:
    assert entry_suggestion.subject == 'git rebase -i erklären'
    assert str(entry_suggestion) == 'git rebase -i erklären'


def test_bug_subject_is_location(bug_suggestion: Suggestion) -> None:
    assert bug_suggestion.subject == 'Virtuelle Umgebung anlegen'


def test_improvement_subject_is_start_of_idea() -> None:
    assert improvement().subject == 'Eine Suche über alle Bereiche, die auch Aliase findet und…'


def test_short_improvement_subject_is_whole_idea() -> None:
    assert improvement(idea='Eine Suche über alle Bereiche.').subject == (
        'Eine Suche über alle Bereiche.'
    )


# Contact
def test_guest_contact_email_is_given_email(entry_suggestion: Suggestion) -> None:
    assert entry_suggestion.contact_email == 'guest@example.com'


def test_user_contact_email_is_account_email(bug_suggestion: Suggestion) -> None:
    assert bug_suggestion.contact_email == 'ada@example.com'


# Answer
def test_saving_answer_marks_suggestion_done(entry_suggestion: Suggestion) -> None:
    entry_suggestion.answer = 'Kommt nächste Woche.'
    entry_suggestion.save()
    entry_suggestion.refresh_from_db()
    assert entry_suggestion.status == 'done'
    assert entry_suggestion.answered_at is not None


def test_changing_answer_keeps_first_answer_date(entry_suggestion: Suggestion) -> None:
    entry_suggestion.answer = 'Kommt nächste Woche.'
    entry_suggestion.save()
    answered_at = entry_suggestion.answered_at
    entry_suggestion.answer = 'Ist online.'
    entry_suggestion.save()
    assert entry_suggestion.answered_at == answered_at


def test_reopened_answered_suggestion_stays_open(entry_suggestion: Suggestion) -> None:
    entry_suggestion.answer = 'Kommt nächste Woche.'
    entry_suggestion.save()
    entry_suggestion.status = 'open'
    entry_suggestion.save()
    entry_suggestion.refresh_from_db()
    assert entry_suggestion.status == 'open'


def test_saving_without_answer_keeps_suggestion_open(entry_suggestion: Suggestion) -> None:
    entry_suggestion.save()
    assert entry_suggestion.status == 'open'
    assert entry_suggestion.answered_at is None


# Validation
def test_valid_suggestion_passes_full_clean() -> None:
    improvement().full_clean()


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('kind', 'question', 'invalid_choice'),
        ('status', 'closed', 'invalid_choice'),
        ('area', 'video', 'invalid_choice'),
        ('bug_type', 'ugly', 'invalid_choice'),
        ('email', 'no-mail', 'invalid'),
        ('idea', 'Zu kurz.', 'min_length'),
        ('idea', 'x' * 2001, 'max_length'),
        ('benefit', 'x' * 1001, 'max_length'),
    ],
)
def test_full_clean_rejects_bad_field(field: str, value: str, code: str) -> None:
    with pytest.raises(ValidationError) as error:
        improvement(**{field: value}).full_clean()
    assert code in error_codes(error.value, field)


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('title', 'x' * 121, 'max_length'),
        ('reason', 'x' * 19, 'min_length'),
        ('reason', 'x' * 1001, 'max_length'),
        ('example', 'x' * 2001, 'max_length'),
        ('source', 'x' * 290 + 'https://a.de', 'max_length'),
        ('source', 'ftp://example.com/file', 'invalid'),
        ('source', 'javascript:alert(1)', 'invalid'),
        ('location', 'x' * 201, 'max_length'),
        ('problem', 'x' * 19, 'min_length'),
        ('correction', 'x' * 1001, 'max_length'),
        ('environment', 'x' * 201, 'max_length'),
    ],
)
def test_full_clean_rejects_bad_entry_or_bug_field(
    entry_suggestion: Suggestion, field: str, value: str, code: str
) -> None:
    setattr(entry_suggestion, field, value)
    with pytest.raises(ValidationError) as error:
        entry_suggestion.full_clean()
    assert code in error_codes(error.value, field)


def test_full_clean_accepts_http_source(entry_suggestion: Suggestion) -> None:
    entry_suggestion.source = 'http://example.com/docs'
    entry_suggestion.full_clean()


# Database constraints
def create_fails(**changes: object) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        improvement(**changes).save()


@pytest.mark.parametrize(
    'changes',
    [
        {'kind': 'question'},
        {'status': 'closed'},
        {'email': ''},
        {'area': ''},
        {'area': 'command'},
        {'idea': ''},
    ],
)
def test_database_rejects_invalid_improvement(changes: dict[str, str]) -> None:
    create_fails(**changes)


@pytest.mark.parametrize(
    'changes',
    [
        {'area': 'feature'},
        {'topic': None},
        {'title': ''},
        {'reason': ''},
    ],
)
def test_database_rejects_invalid_entry(topic: Topic, changes: dict[str, object]) -> None:
    data = {'kind': 'entry', 'area': 'command', 'topic': topic, 'title': 'T', 'reason': 'R'}
    create_fails(**(data | {'idea': ''} | changes))


@pytest.mark.parametrize(
    'changes',
    [{'bug_type': ''}, {'bug_type': 'ugly'}, {'location': ''}, {'problem': ''}],
)
def test_database_rejects_invalid_bug(changes: dict[str, str]) -> None:
    data = {'kind': 'bug', 'area': '', 'idea': '', 'bug_type': 'typo'}
    create_fails(**(data | {'location': 'Seite', 'problem': 'Fehler'} | changes))


def test_database_accepts_user_without_email(user: User) -> None:
    improvement(email='', user=user).save()
    assert Suggestion.objects.get().user == user


# Relations
def test_deleting_user_deletes_their_suggestions(
    bug_suggestion: Suggestion, entry_suggestion: Suggestion
) -> None:
    bug_suggestion.user.delete()
    assert list(Suggestion.objects.all()) == [entry_suggestion]


def test_topic_with_suggestions_cannot_be_deleted(entry_suggestion: Suggestion) -> None:
    with pytest.raises(ProtectedError):
        entry_suggestion.topic.delete()
