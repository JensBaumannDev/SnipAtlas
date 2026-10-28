from datetime import UTC, date, datetime

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'


def error_codes(user: User, field: str) -> list[str]:
    with pytest.raises(ValidationError) as error:
        user.full_clean()
    return [item.code for item in error.value.error_dict[field]]


# Login field
def test_user_logs_in_with_email() -> None:
    assert User.USERNAME_FIELD == 'email'
    assert User.REQUIRED_FIELDS == []


def test_user_has_no_username_or_names() -> None:
    field_names = {field.name for field in User._meta.get_fields()}
    assert {'username', 'first_name', 'last_name'}.isdisjoint(field_names)


# Create user
def test_create_user_stores_hashed_password(user: User) -> None:
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)


def test_create_user_without_password_has_unusable_password() -> None:
    user = User.objects.create_user('grace@example.com')
    assert not user.has_usable_password()


def test_create_user_lowercases_and_trims_email() -> None:
    user = User.objects.create_user('  Ada.Lovelace@Example.COM ', PASSWORD)
    assert user.email == 'ada.lovelace@example.com'


@pytest.mark.parametrize('email', ['', None, '   '])
def test_create_user_without_email_is_rejected(email: str | None) -> None:
    with pytest.raises(ValueError, match='Email is required.'):
        User.objects.create_user(email, PASSWORD)


def test_create_user_with_taken_email_in_other_case_is_rejected(user: User) -> None:
    with pytest.raises(IntegrityError):
        User.objects.create_user('ADA@example.com', PASSWORD)


def test_create_user_applies_extra_fields() -> None:
    user = User.objects.create_user('grace@example.com', PASSWORD, accent='teal')
    assert user.accent == 'teal'


def test_new_user_is_active_without_admin_rights(user: User) -> None:
    assert user.is_active
    assert not user.is_staff
    assert not user.is_superuser


# Create superuser
def test_create_superuser_has_admin_rights() -> None:
    admin = User.objects.create_superuser('admin@example.com', PASSWORD)
    assert admin.is_staff
    assert admin.is_superuser


@pytest.mark.parametrize('field', ['is_staff', 'is_superuser'])
def test_create_superuser_without_admin_right_is_rejected(field: str) -> None:
    with pytest.raises(ValueError, match=f'Superuser must have {field}=True.'):
        User.objects.create_superuser('admin@example.com', PASSWORD, **{field: False})


# Save
def test_save_lowercases_email_outside_manager() -> None:
    user = User.objects.create(email=' Grace@Example.com ')
    assert user.email == 'grace@example.com'


def test_save_with_taken_email_in_other_case_is_rejected(user: User) -> None:
    with pytest.raises(IntegrityError):
        User.objects.create(email='ADA@example.com')


# Settings
def test_new_user_gets_mail_notification_and_blue_accent(user: User) -> None:
    assert user.notify_by_mail
    assert user.accent == 'blue'
    assert user.date_joined is not None


def test_accent_outside_choices_is_rejected(user: User) -> None:
    user.accent = 'orange'
    assert error_codes(user, 'accent') == ['invalid_choice']


# Validation
def test_clean_lowercases_and_trims_email(user: User) -> None:
    user.email = ' ADA@Example.com '
    user.clean()
    assert user.email == 'ada@example.com'


def test_empty_email_is_rejected(user: User) -> None:
    user.email = ''
    assert error_codes(user, 'email') == ['blank']


def test_invalid_email_is_rejected(user: User) -> None:
    user.email = 'no-mail'
    assert error_codes(user, 'email') == ['invalid']


def test_too_long_email_is_rejected(user: User) -> None:
    user.email = f'{"a" * 250}@example.com'
    assert 'max_length' in error_codes(user, 'email')


def test_taken_email_in_other_case_is_rejected_as_unique(user: User) -> None:
    other = User(email='ADA@example.com', password=PASSWORD)
    assert error_codes(other, 'email') == ['unique']


def test_str_returns_email(user: User) -> None:
    assert str(user) == 'ada@example.com'


# Unicode
def test_create_user_lowercases_unicode_domain() -> None:
    user = User.objects.create_user('Ada@MÜNCHEN.de', PASSWORD)
    assert user.email == 'ada@münchen.de'


@pytest.mark.parametrize('lookalike', ['ada@examıple.com', 'ADA@EXAMPLE.İO'])
def test_lookalike_email_does_not_match_user(user: User, lookalike: str) -> None:
    with pytest.raises(User.DoesNotExist):
        User.objects.get_by_natural_key(lookalike)


# Password hashing
def test_password_is_hashed_with_argon2(user: User) -> None:
    assert user.password.startswith('argon2$')


def test_old_pbkdf2_hash_is_upgraded_on_login(user: User) -> None:
    user.password = make_password(PASSWORD, hasher='pbkdf2_sha256')
    user.save()
    assert authenticate(email='ada@example.com', password=PASSWORD) == user
    user.refresh_from_db()
    assert user.password.startswith('argon2$')


# Authentication
def test_authenticate_ignores_case_and_spaces(user: User) -> None:
    assert authenticate(email=' ADA@Example.com ', password=PASSWORD) == user


def test_authenticate_with_wrong_password_fails(user: User) -> None:
    assert authenticate(email='ada@example.com', password='wrong') is None


def test_authenticate_with_unknown_email_fails(user: User) -> None:
    assert authenticate(email='grace@example.com', password=PASSWORD) is None


def test_authenticate_inactive_user_fails(user: User) -> None:
    user.is_active = False
    user.save()
    assert authenticate(email='ada@example.com', password=PASSWORD) is None


# Since
def test_since_is_join_date_in_local_time(user: User) -> None:
    user.date_joined = datetime(2026, 10, 27, 23, 30, tzinfo=UTC)
    assert user.since == date(2026, 10, 28)
