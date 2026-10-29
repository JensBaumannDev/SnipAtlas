from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from app_accounts.models import User
from app_feedback.models import Suggestion

pytestmark = pytest.mark.django_db


def add_ticket(user: User | None = None, *, days: int, status: str = 'done') -> Suggestion:
    contact = {'user': user} if user else {'email': 'guest@example.com'}
    suggestion = Suggestion.objects.create(
        kind='improvement', area='feature', idea='x' * 30, status=status, **contact
    )
    created_at = timezone.now() - timedelta(days=days)
    Suggestion.objects.filter(pk=suggestion.pk).update(created_at=created_at)
    return suggestion


def run() -> str:
    out = StringIO()
    call_command('delete_old_suggestions', stdout=out)
    return out.getvalue()


def test_command_deletes_old_done_guest_tickets() -> None:
    add_ticket(days=184)
    add_ticket(days=400)
    assert run() == 'Deleted 2 old guest tickets.\n'
    assert not Suggestion.objects.exists()


@pytest.mark.parametrize(('days', 'status'), [(184, 'open'), (182, 'done'), (0, 'done')])
def test_command_keeps_open_or_recent_guest_tickets(days: int, status: str) -> None:
    ticket = add_ticket(days=days, status=status)
    assert run() == 'Deleted 0 old guest tickets.\n'
    assert list(Suggestion.objects.all()) == [ticket]


def test_command_keeps_old_tickets_of_users(user: User) -> None:
    ticket = add_ticket(user, days=400)
    run()
    assert list(Suggestion.objects.all()) == [ticket]


def test_command_deletes_only_matching_tickets(user: User) -> None:
    add_ticket(days=400)
    kept = [add_ticket(days=400, status='open'), add_ticket(user, days=400), add_ticket(days=10)]
    assert run() == 'Deleted 1 old guest tickets.\n'
    assert set(Suggestion.objects.all()) == set(kept)


def test_command_deletes_answered_guest_ticket(entry_suggestion: Suggestion) -> None:
    entry_suggestion.answer = 'Erledigt.'
    entry_suggestion.save()
    created_at = timezone.now() - timedelta(days=200)
    Suggestion.objects.filter(pk=entry_suggestion.pk).update(created_at=created_at)
    run()
    assert not Suggestion.objects.exists()


def test_command_without_tickets_deletes_nothing() -> None:
    assert run() == 'Deleted 0 old guest tickets.\n'


def test_delete_old_guest_tickets_returns_count() -> None:
    add_ticket(days=200)
    assert Suggestion.delete_old_guest_tickets() == 1
