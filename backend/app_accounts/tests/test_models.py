from datetime import UTC, date, datetime

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, transaction

from app_accounts.models import CompletedStep, Favorite
from app_content.models import Blueprint, BlueprintStep, Entry

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


def test_new_user_gets_default_settings(user: User) -> None:
    assert (user.os, user.theme, user.language) == ('win', 'system', 'auto')


@pytest.mark.parametrize(
    ('field', 'value'),
    [('accent', 'orange'), ('os', 'mac'), ('theme', 'blue'), ('language', 'fr')],
)
def test_setting_outside_choices_is_rejected(user: User, field: str, value: str) -> None:
    setattr(user, field, value)
    assert error_codes(user, field) == ['invalid_choice']


@pytest.mark.parametrize('field', ['accent', 'os', 'theme', 'language'])
def test_empty_setting_is_rejected(user: User, field: str) -> None:
    setattr(user, field, '')
    assert error_codes(user, field) == ['blank']


@pytest.mark.parametrize(
    ('field', 'value'),
    [('accent', 'orange'), ('os', 'mac'), ('os', 'WIN'), ('theme', 'blue'), ('language', '')],
)
def test_database_rejects_setting_outside_choices(user: User, field: str, value: str) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=user.pk).update(**{field: value})


@pytest.mark.parametrize(
    ('field', 'value'),
    [('os', 'unix'), ('theme', 'light'), ('theme', 'dark'), ('language', 'de'), ('language', 'en')],
)
def test_setting_inside_choices_is_saved(user: User, field: str, value: str) -> None:
    setattr(user, field, value)
    user.full_clean()
    user.save()
    user.refresh_from_db()
    assert getattr(user, field) == value


# Project values
PROJECT_FIELDS = [
    'project_name',
    'project_github_user',
    'project_repo',
    'project_domain',
    'project_server_user',
    'project_server_ip',
]


def test_new_user_has_empty_project_values(user: User) -> None:
    assert [getattr(user, field) for field in PROJECT_FIELDS] == [''] * 6
    user.full_clean()


@pytest.mark.parametrize('field', PROJECT_FIELDS)
def test_database_rejects_missing_project_value(user: User, field: str) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=user.pk).update(**{field: None})


@pytest.mark.parametrize('field', PROJECT_FIELDS)
def test_project_value_with_100_characters_is_accepted(user: User, field: str) -> None:
    setattr(user, field, 'a' * 100)
    user.full_clean()


@pytest.mark.parametrize('field', PROJECT_FIELDS)
def test_too_long_project_value_is_rejected(user: User, field: str) -> None:
    setattr(user, field, 'a' * 101)
    assert error_codes(user, field) == ['max_length']


@pytest.mark.parametrize('field', PROJECT_FIELDS)
def test_database_rejects_too_long_project_value(user: User, field: str) -> None:
    with pytest.raises(DataError), transaction.atomic():
        User.objects.filter(pk=user.pk).update(**{field: 'a' * 101})


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


# Favorites
@pytest.fixture
def other_user() -> User:
    return User.objects.create_user('grace@example.com', PASSWORD)


def unique_codes(item: Favorite | CompletedStep) -> list[str]:
    with pytest.raises(ValidationError) as error:
        item.full_clean()
    return [item.code for item in error.value.error_dict['__all__']]


def test_favorite_links_user_and_entry(user: User, entry: Entry) -> None:
    favorite = Favorite.objects.create(user=user, entry=entry)
    assert list(user.favorites.all()) == [favorite]
    assert favorite.created_at is not None


def test_favorite_str_names_user_and_entry(user: User, entry: Entry) -> None:
    favorite = Favorite.objects.create(user=user, entry=entry)
    assert str(favorite) == 'ada@example.com: For-Schleife'


def test_same_favorite_twice_is_rejected(user: User, entry: Entry) -> None:
    Favorite.objects.create(user=user, entry=entry)
    with pytest.raises(IntegrityError):
        Favorite.objects.create(user=user, entry=entry)


def test_same_favorite_twice_fails_validation(user: User, entry: Entry) -> None:
    Favorite.objects.create(user=user, entry=entry)
    assert unique_codes(Favorite(user=user, entry=entry)) == ['unique_together']


def test_same_entry_for_other_user_is_allowed(user: User, other_user: User, entry: Entry) -> None:
    Favorite.objects.create(user=user, entry=entry)
    Favorite.objects.create(user=other_user, entry=entry)
    assert Favorite.objects.count() == 2


def test_favorites_are_ordered_oldest_first(user: User, entry: Entry, os_entry: Entry) -> None:
    newer = Favorite.objects.create(user=user, entry=entry)
    older = Favorite.objects.create(user=user, entry=os_entry)
    Favorite.objects.filter(pk=older.pk).update(created_at=datetime(2026, 1, 1, tzinfo=UTC))
    assert list(user.favorites.all()) == [older, newer]


def test_favorites_with_same_time_keep_creation_order(
    user: User, entry: Entry, os_entry: Entry
) -> None:
    first = Favorite.objects.create(user=user, entry=os_entry)
    second = Favorite.objects.create(user=user, entry=entry)
    Favorite.objects.update(created_at=datetime(2026, 1, 1, tzinfo=UTC))
    assert list(user.favorites.all()) == [first, second]


def test_deleting_entry_deletes_its_favorites(user: User, entry: Entry, os_entry: Entry) -> None:
    Favorite.objects.create(user=user, entry=entry)
    kept = Favorite.objects.create(user=user, entry=os_entry)
    entry.delete()
    assert list(Favorite.objects.all()) == [kept]


def test_deleting_user_deletes_only_own_favorites(
    user: User, other_user: User, entry: Entry
) -> None:
    Favorite.objects.create(user=user, entry=entry)
    kept = Favorite.objects.create(user=other_user, entry=entry)
    user.delete()
    assert list(Favorite.objects.all()) == [kept]
    assert Entry.objects.filter(pk=entry.pk).exists()


# Completed steps
def test_completed_step_links_user_and_step(user: User, venv_step: BlueprintStep) -> None:
    done = CompletedStep.objects.create(user=user, step=venv_step)
    assert list(user.completed_steps.all()) == [done]
    assert done.created_at is not None


def test_completed_step_str_names_user_and_step(user: User, venv_step: BlueprintStep) -> None:
    done = CompletedStep.objects.create(user=user, step=venv_step)
    assert str(done) == 'ada@example.com: Virtuelle Umgebung einrichten'


def test_same_completed_step_twice_is_rejected(user: User, venv_step: BlueprintStep) -> None:
    CompletedStep.objects.create(user=user, step=venv_step)
    with pytest.raises(IntegrityError):
        CompletedStep.objects.create(user=user, step=venv_step)


def test_same_completed_step_twice_fails_validation(user: User, venv_step: BlueprintStep) -> None:
    CompletedStep.objects.create(user=user, step=venv_step)
    assert unique_codes(CompletedStep(user=user, step=venv_step)) == ['unique_together']


def test_same_step_for_other_user_is_allowed(
    user: User, other_user: User, venv_step: BlueprintStep
) -> None:
    CompletedStep.objects.create(user=user, step=venv_step)
    CompletedStep.objects.create(user=other_user, step=venv_step)
    assert CompletedStep.objects.count() == 2


def test_completed_steps_follow_step_order(user: User, blueprint: Blueprint) -> None:
    first_step, second_step = blueprint.steps.all()
    second = CompletedStep.objects.create(user=user, step=second_step)
    first = CompletedStep.objects.create(user=user, step=first_step)
    assert list(user.completed_steps.all()) == [first, second]


def test_completed_steps_with_same_position_keep_step_order(
    user: User, blueprint: Blueprint
) -> None:
    blueprint.steps.update(position=3)
    first_step, second_step = blueprint.steps.all()
    second = CompletedStep.objects.create(user=user, step=second_step)
    first = CompletedStep.objects.create(user=user, step=first_step)
    assert list(user.completed_steps.all()) == [first, second]


def test_completed_steps_stay_grouped_by_blueprint(user: User, blueprint: Blueprint) -> None:
    other = Blueprint.objects.create(
        topic=blueprint.topic, slug='git-einrichten', title_de='Git', summary_de='Git.'
    )
    other_step = other.steps.create(slug='installieren', title_de='Installieren', why_de='Nötig.')
    first_step, second_step = blueprint.steps.all()
    for step in (second_step, other_step, first_step):
        CompletedStep.objects.create(user=user, step=step)
    steps = [done.step for done in user.completed_steps.all()]
    assert steps == [first_step, second_step, other_step]


def test_completed_step_survives_renamed_step_slug(user: User, venv_step: BlueprintStep) -> None:
    done = CompletedStep.objects.create(user=user, step=venv_step)
    venv_step.slug = 'venv-einrichten'
    venv_step.save()
    done.refresh_from_db()
    assert done.step.slug == 'venv-einrichten'


def test_deleting_step_deletes_its_progress(user: User, blueprint: Blueprint) -> None:
    first_step, second_step = blueprint.steps.all()
    CompletedStep.objects.create(user=user, step=first_step)
    kept = CompletedStep.objects.create(user=user, step=second_step)
    first_step.delete()
    assert list(CompletedStep.objects.all()) == [kept]


def test_deleting_blueprint_deletes_its_progress(user: User, venv_step: BlueprintStep) -> None:
    CompletedStep.objects.create(user=user, step=venv_step)
    venv_step.blueprint.delete()
    assert not CompletedStep.objects.exists()


def test_deleting_user_deletes_only_own_progress(
    user: User, other_user: User, venv_step: BlueprintStep
) -> None:
    CompletedStep.objects.create(user=user, step=venv_step)
    kept = CompletedStep.objects.create(user=other_user, step=venv_step)
    user.delete()
    assert list(CompletedStep.objects.all()) == [kept]
    assert BlueprintStep.objects.filter(pk=venv_step.pk).exists()
