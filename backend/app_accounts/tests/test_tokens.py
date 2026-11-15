from datetime import timedelta

import pytest
from django.utils import timezone

from app_accounts.models import User
from app_accounts.tokens import ACTIVATION, EMAIL_CHANGE, check_link_token, make_link_token

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'


def tamper(token: str) -> str:
    return ('1' if token[0] == '0' else '0') + token[1:]


def token_at(user: User, purpose: str, monkeypatch: pytest.MonkeyPatch, hours: float) -> str:
    moment = timezone.now() - timedelta(hours=hours)
    monkeypatch.setattr('django.core.signing.time.time', moment.timestamp)
    token = make_link_token(user, purpose)
    monkeypatch.undo()
    return token


@pytest.mark.parametrize('purpose', [ACTIVATION, EMAIL_CHANGE])
def test_new_token_is_valid(user: User, purpose: str) -> None:
    assert check_link_token(user, make_link_token(user, purpose), purpose)


@pytest.mark.parametrize('purpose', [ACTIVATION, EMAIL_CHANGE])
def test_token_is_valid_for_almost_a_day(
    user: User, purpose: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert check_link_token(user, token_at(user, purpose, monkeypatch, 23.9), purpose)


@pytest.mark.parametrize('purpose', [ACTIVATION, EMAIL_CHANGE])
def test_token_expires_after_a_day(
    user: User, purpose: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert not check_link_token(user, token_at(user, purpose, monkeypatch, 24.1), purpose)


def test_token_does_not_work_for_other_purpose(user: User) -> None:
    assert not check_link_token(user, make_link_token(user, ACTIVATION), EMAIL_CHANGE)


def test_token_does_not_work_for_other_user(user: User) -> None:
    other = User.objects.create_user('grace@example.com', PASSWORD)
    assert not check_link_token(other, make_link_token(user, ACTIVATION), ACTIVATION)


@pytest.mark.parametrize('token', ['', 'broken', 'a:b:c', 'x' * 500])
def test_broken_token_is_rejected(user: User, token: str) -> None:
    assert not check_link_token(user, token, ACTIVATION)


def test_tampered_token_is_rejected(user: User) -> None:
    token = make_link_token(user, ACTIVATION)
    assert not check_link_token(user, tamper(token), ACTIVATION)


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('email_confirmed', False),
        ('pending_email', 'new@example.com'),
        ('email', 'ada.new@example.com'),
    ],
)
def test_token_becomes_invalid_when_user_changes(user: User, field: str, value: object) -> None:
    token = make_link_token(user, ACTIVATION)
    setattr(user, field, value)
    user.save()
    assert not check_link_token(user, token, ACTIVATION)


def test_token_becomes_invalid_after_new_password(user: User) -> None:
    token = make_link_token(user, EMAIL_CHANGE)
    user.set_password('Andere-Tasse-2026!')
    user.save()
    assert not check_link_token(user, token, EMAIL_CHANGE)


def test_token_does_not_contain_password_hash(user: User) -> None:
    token = make_link_token(user, ACTIVATION)
    assert user.password not in token
    assert user.password.split('$')[-1] not in token
