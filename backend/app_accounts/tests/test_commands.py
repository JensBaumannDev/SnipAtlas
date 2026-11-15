from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from app_accounts.models import Favorite, User
from app_content.models import Entry

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'


def add_user(email: str, *, days: float, confirmed: bool = False, **extra: object) -> User:
    user = User.objects.create_user(email, PASSWORD, email_confirmed=confirmed, **extra)
    joined = timezone.now() - timedelta(days=days)
    User.objects.filter(pk=user.pk).update(date_joined=joined)
    return user


def run() -> str:
    out = StringIO()
    call_command('delete_unconfirmed_accounts', stdout=out)
    return out.getvalue()


def test_command_deletes_old_unconfirmed_accounts() -> None:
    add_user('a@example.com', days=7.1)
    add_user('b@example.com', days=30)
    assert run() == 'Deleted 2 unconfirmed accounts.\n'
    assert not User.objects.exists()


@pytest.mark.parametrize('days', [6.9, 1, 0])
def test_command_keeps_recent_unconfirmed_accounts(days: float) -> None:
    user = add_user('a@example.com', days=days)
    assert run() == 'Deleted 0 unconfirmed accounts.\n'
    assert list(User.objects.all()) == [user]


def test_command_keeps_old_confirmed_accounts() -> None:
    user = add_user('a@example.com', days=400, confirmed=True)
    run()
    assert list(User.objects.all()) == [user]


def test_command_keeps_old_unconfirmed_staff() -> None:
    staff = add_user('staff@example.com', days=400, is_staff=True)
    run()
    assert list(User.objects.all()) == [staff]


def test_command_keeps_pending_email_of_confirmed_account() -> None:
    user = add_user('a@example.com', days=400, confirmed=True)
    user.pending_email = 'new@example.com'
    user.save()
    run()
    user.refresh_from_db()
    assert user.pending_email == 'new@example.com'


def test_command_counts_only_accounts_not_their_data(entry: Entry) -> None:
    user = add_user('a@example.com', days=30)
    Favorite.objects.create(user=user, entry=entry)
    assert run() == 'Deleted 1 unconfirmed accounts.\n'
    assert not Favorite.objects.exists()


def test_command_deletes_only_matching_accounts() -> None:
    add_user('old@example.com', days=30)
    kept = [
        add_user('new@example.com', days=1),
        add_user('done@example.com', days=30, confirmed=True),
        add_user('staff@example.com', days=30, is_staff=True),
    ]
    assert run() == 'Deleted 1 unconfirmed accounts.\n'
    assert set(User.objects.all()) == set(kept)
