import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.http import HttpResponse
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from app_accounts.models import CompletedStep, Favorite
from app_content.models import Blueprint, BlueprintStep, Entry

User = get_user_model()

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'
INLINE_FORMS = {
    f'{prefix}-{field}': 0
    for prefix in ('favorites', 'completed_steps')
    for field in ('TOTAL_FORMS', 'INITIAL_FORMS')
}


def add_user(admin_client: Client, **changes: str) -> HttpResponse:
    data = {'email': 'grace@example.com', 'usable_password': 'true'}
    data |= {'password1': PASSWORD, 'password2': PASSWORD} | changes
    return admin_client.post(reverse('admin:app_accounts_user_add'), data)


def change_user(admin_client: Client, user: User, **changes: str) -> HttpResponse:
    url = reverse('admin:app_accounts_user_change', args=[user.pk])
    settings = {'accent': user.accent, 'os': user.os, 'theme': user.theme}
    data = {'email': user.email, 'is_active': 'on', 'language': user.language} | settings
    return admin_client.post(url, data | INLINE_FORMS | changes)


def change_page(admin_client: Client, user: User) -> HttpResponse:
    return admin_client.get(reverse('admin:app_accounts_user_change', args=[user.pk]))


def inline_rows(response: HttpResponse, model: str) -> list[object]:
    formsets = response.context['inline_admin_formsets']
    formset = next(item.formset for item in formsets if item.formset.model.__name__ == model)
    return [form.instance for form in formset.forms]


def form_error_codes(response: HttpResponse, field: str) -> list[str]:
    form = response.context['adminform'].form
    return [error.code for error in form.errors.as_data()[field]]


# Access
def test_user_list_redirects_guest_to_login(client: Client) -> None:
    response = client.get(reverse('admin:app_accounts_user_changelist'))
    assert response.status_code == 302
    assert response.url.startswith(reverse('admin:login'))


def test_user_list_redirects_user_without_staff_to_login(client: Client, user: User) -> None:
    client.force_login(user)
    response = client.get(reverse('admin:app_accounts_user_changelist'))
    assert response.status_code == 302
    assert response.url.startswith(reverse('admin:login'))


# List
def test_user_list_loads(admin_client: Client, user: User) -> None:
    response = admin_client.get(reverse('admin:app_accounts_user_changelist'))
    assert response.status_code == 200
    assert 'ada@example.com' in response.content.decode()


def test_user_list_searches_by_email(admin_client: Client, user: User) -> None:
    url = reverse('admin:app_accounts_user_changelist')
    response = admin_client.get(url, {'q': 'ada@'})
    assert list(response.context['cl'].result_list) == [user]


def test_user_list_shows_newest_first(admin_client: Client, user: User) -> None:
    newer = User.objects.create_user('grace@example.com', PASSWORD)
    response = admin_client.get(reverse('admin:app_accounts_user_changelist'))
    assert list(response.context['cl'].result_list)[:2] == [newer, user]


# Add
def test_add_page_loads(admin_client: Client) -> None:
    response = admin_client.get(reverse('admin:app_accounts_user_add'))
    assert response.status_code == 200


def test_admin_adds_user_with_email_and_password(admin_client: Client) -> None:
    response = add_user(admin_client, email=' Grace@Example.com ')
    user = User.objects.get(email='grace@example.com')
    assert response.status_code == 302
    assert user.check_password(PASSWORD)


def test_add_page_shows_no_user_data(admin_client: Client) -> None:
    response = admin_client.get(reverse('admin:app_accounts_user_add'))
    assert response.context['inline_admin_formsets'] == []


def test_admin_adds_user_without_usable_password(admin_client: Client) -> None:
    add_user(admin_client, usable_password='false', password1='', password2='')
    user = User.objects.get(email='grace@example.com')
    assert not user.has_usable_password()


@pytest.mark.parametrize(
    ('email', 'code'),
    [('', 'required'), ('no-mail', 'invalid'), ('ADA@example.com', 'unique')],
)
def test_admin_add_rejects_bad_email(
    admin_client: Client, user: User, email: str, code: str
) -> None:
    response = add_user(admin_client, email=email)
    assert response.status_code == 200
    assert form_error_codes(response, 'email') == [code]
    assert User.objects.count() == 2


def test_admin_add_rejects_different_passwords(admin_client: Client) -> None:
    response = add_user(admin_client, password2='Andere-Tasse-2026!')
    assert form_error_codes(response, 'password2') == ['password_mismatch']
    assert not User.objects.filter(email='grace@example.com').exists()


def test_admin_add_rejects_weak_password(admin_client: Client) -> None:
    response = add_user(admin_client, password1='123', password2='123')
    codes = set(form_error_codes(response, 'password2'))
    assert {'password_too_short', 'password_too_common', 'password_entirely_numeric'} <= codes
    assert not User.objects.filter(email='grace@example.com').exists()


# Change
def test_user_change_page_loads(admin_client: Client, user: User) -> None:
    response = admin_client.get(reverse('admin:app_accounts_user_change', args=[user.pk]))
    assert response.status_code == 200


def test_user_change_saves_settings(admin_client: Client, user: User) -> None:
    response = change_user(admin_client, user, accent='teal')
    user.refresh_from_db()
    assert response.status_code == 302
    assert user.accent == 'teal'
    assert not user.notify_by_mail


def test_user_change_lowercases_email(admin_client: Client, user: User) -> None:
    change_user(admin_client, user, email=' Ada.L@Example.com ')
    user.refresh_from_db()
    assert user.email == 'ada.l@example.com'


def test_user_change_rejects_taken_email(admin_client: Client, user: User) -> None:
    response = change_user(admin_client, user, email='ADMIN@example.com')
    user.refresh_from_db()
    assert form_error_codes(response, 'email') == ['unique']
    assert user.email == 'ada@example.com'


def test_user_change_rejects_unknown_accent(admin_client: Client, user: User) -> None:
    response = change_user(admin_client, user, accent='orange')
    assert form_error_codes(response, 'accent') == ['invalid_choice']


def test_user_change_saves_os_theme_and_language(admin_client: Client, user: User) -> None:
    response = change_user(admin_client, user, os='unix', theme='dark', language='en')
    user.refresh_from_db()
    assert response.status_code == 302
    assert (user.os, user.theme, user.language) == ('unix', 'dark', 'en')


@pytest.mark.parametrize(('field', 'value'), [('os', 'mac'), ('theme', 'blue'), ('language', '')])
def test_user_change_rejects_unknown_setting(
    admin_client: Client, user: User, field: str, value: str
) -> None:
    response = change_user(admin_client, user, **{field: value})
    expected = 'required' if value == '' else 'invalid_choice'
    assert form_error_codes(response, field) == [expected]


def test_user_change_saves_project_values(admin_client: Client, user: User) -> None:
    response = change_user(
        admin_client, user, project_name='snipatlas', project_server_ip='1.2.3.4'
    )
    user.refresh_from_db()
    assert response.status_code == 302
    assert (user.project_name, user.project_server_ip) == ('snipatlas', '1.2.3.4')


def test_user_change_rejects_too_long_project_value(admin_client: Client, user: User) -> None:
    response = change_user(admin_client, user, project_repo='a' * 101)
    assert form_error_codes(response, 'project_repo') == ['max_length']


def test_user_change_rejects_null_character_in_project_value(
    admin_client: Client, user: User
) -> None:
    response = change_user(admin_client, user, project_domain='a\x00b')
    assert form_error_codes(response, 'project_domain') == ['null_characters_not_allowed']


def test_user_change_escapes_project_value(admin_client: Client, user: User) -> None:
    user.project_name = '<script>alert(1)</script>'
    user.save()
    content = change_page(admin_client, user).content.decode()
    assert '<script>alert(1)</script>' not in content
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in content


def test_date_joined_is_read_only(admin_client: Client, user: User) -> None:
    joined = user.date_joined
    change_user(admin_client, user, date_joined_0='2000-01-01', date_joined_1='00:00:00')
    user.refresh_from_db()
    assert user.date_joined == joined


# Password
def test_admin_changes_password(admin_client: Client, user: User) -> None:
    url = reverse('admin:auth_user_password_change', args=[user.pk])
    new_password = 'Neue-Tasse-2026!'
    data = {'usable_password': 'true', 'password1': new_password, 'password2': new_password}
    response = admin_client.post(url, data)
    user.refresh_from_db()
    assert response.status_code == 302
    assert user.check_password(new_password)


# Delete
def test_admin_deletes_user(admin_client: Client, user: User) -> None:
    url = reverse('admin:app_accounts_user_delete', args=[user.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not User.objects.filter(pk=user.pk).exists()


# Rights
def test_superuser_grants_admin_rights(admin_client: Client, user: User) -> None:
    change_user(admin_client, user, is_staff='on', is_superuser='on')
    user.refresh_from_db()
    assert user.is_staff
    assert user.is_superuser


@pytest.mark.parametrize('field', ['is_staff', 'is_superuser', 'groups', 'user_permissions'])
def test_staff_cannot_edit_right_fields(staff_client: Client, user: User, field: str) -> None:
    response = staff_client.get(reverse('admin:app_accounts_user_change', args=[user.pk]))
    assert response.status_code == 200
    assert field not in response.context['adminform'].form.fields


def test_staff_cannot_grant_admin_rights_to_self(staff_client: Client, staff_user: User) -> None:
    response = change_user(staff_client, staff_user, is_superuser='on')
    staff_user.refresh_from_db()
    assert response.status_code == 302
    assert not staff_user.is_superuser


def test_staff_edits_settings_of_normal_user(staff_client: Client, user: User) -> None:
    response = change_user(staff_client, user, accent='teal')
    user.refresh_from_db()
    assert response.status_code == 302
    assert user.accent == 'teal'


def test_staff_cannot_change_superuser(staff_client: Client, admin_user: User) -> None:
    response = change_user(staff_client, admin_user, email='staff-owned@example.com')
    admin_user.refresh_from_db()
    assert response.status_code == 403
    assert admin_user.email == 'admin@example.com'


def test_staff_cannot_change_password_of_superuser(staff_client: Client, admin_user: User) -> None:
    url = reverse('admin:auth_user_password_change', args=[admin_user.pk])
    data = {'usable_password': 'true', 'password1': PASSWORD, 'password2': PASSWORD}
    response = staff_client.post(url, data)
    admin_user.refresh_from_db()
    assert response.status_code == 403
    assert not admin_user.check_password(PASSWORD)


def test_staff_cannot_delete_superuser(staff_client: Client, admin_user: User) -> None:
    url = reverse('admin:app_accounts_user_delete', args=[admin_user.pk])
    response = staff_client.post(url, {'post': 'yes'})
    assert response.status_code == 403
    assert User.objects.filter(pk=admin_user.pk).exists()


# User data
@pytest.fixture
def user_data(user: User, entry: Entry, venv_step: BlueprintStep) -> User:
    Favorite.objects.create(user=user, entry=entry)
    CompletedStep.objects.create(user=user, step=venv_step)
    return user


@pytest.fixture
def other_data(entry: Entry, venv_step: BlueprintStep) -> User:
    other = User.objects.create_user('grace@example.com', PASSWORD)
    Favorite.objects.create(user=other, entry=entry)
    CompletedStep.objects.create(user=other, step=venv_step)
    return other


@pytest.mark.parametrize('model', ['Favorite', 'CompletedStep'])
def test_user_page_shows_only_own_data(
    admin_client: Client, user_data: User, other_data: User, model: str
) -> None:
    rows = inline_rows(change_page(admin_client, user_data), model)
    assert [row.user for row in rows] == [user_data]


@pytest.mark.parametrize('model', ['Favorite', 'CompletedStep'])
def test_user_data_is_read_only(admin_client: Client, user_data: User, model: str) -> None:
    formsets = change_page(admin_client, user_data).context['inline_admin_formsets']
    inline = next(item for item in formsets if item.formset.model.__name__ == model)
    assert not inline.has_add_permission
    assert not inline.has_change_permission
    assert not inline.has_delete_permission


def test_user_change_keeps_user_data(admin_client: Client, user_data: User) -> None:
    response = change_user(admin_client, user_data, accent='teal')
    assert response.status_code == 302
    assert user_data.favorites.count() == 1
    assert user_data.completed_steps.count() == 1


def test_user_page_escapes_favorite_title(
    admin_client: Client, user_data: User, entry: Entry
) -> None:
    entry.title_de = '<script>alert(1)</script>'
    entry.save()
    content = change_page(admin_client, user_data).content.decode()
    assert '<script>alert(1)</script>' not in content
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in content


def user_data_snapshot(user: User) -> list[tuple]:
    favorites = list(user.favorites.values_list('pk', 'entry'))
    return favorites + list(user.completed_steps.values_list('pk', 'step'))


def inline_post(prefix: str, field: str, value: int, existing: int | None = None) -> dict:
    data = {f'{prefix}-TOTAL_FORMS': 1, f'{prefix}-INITIAL_FORMS': int(existing is not None)}
    data |= {f'{prefix}-0-{field}': value, f'{prefix}-0-DELETE': 'on'}
    return data | ({f'{prefix}-0-id': existing} if existing else {})


@pytest.mark.parametrize('existing', [True, False])
def test_user_change_ignores_posted_favorite_rows(
    admin_client: Client, user_data: User, os_entry: Entry, existing: bool
) -> None:
    before = user_data_snapshot(user_data)
    favorite = user_data.favorites.get().pk if existing else None
    change_user(admin_client, user_data, **inline_post('favorites', 'entry', os_entry.pk, favorite))
    assert user_data_snapshot(user_data) == before


@pytest.mark.parametrize('existing', [True, False])
def test_user_change_ignores_posted_progress_rows(
    admin_client: Client, user_data: User, blueprint: Blueprint, existing: bool
) -> None:
    before = user_data_snapshot(user_data)
    other_step = blueprint.steps.get(slug='ordner-anlegen').pk
    done = user_data.completed_steps.get().pk if existing else None
    change_user(admin_client, user_data, **inline_post('completed_steps', 'step', other_step, done))
    assert user_data_snapshot(user_data) == before


def test_staff_without_rights_does_not_see_user_data(staff_client: Client, user_data: User) -> None:
    response = change_page(staff_client, user_data)
    assert response.status_code == 200
    assert response.context['inline_admin_formsets'] == []


def test_staff_with_view_right_sees_user_data_read_only(
    staff_client: Client, staff_user: User, user_data: User
) -> None:
    rights = Permission.objects.filter(codename__in=['view_favorite', 'view_completedstep'])
    staff_user.user_permissions.add(*rights)
    formsets = change_page(staff_client, user_data).context['inline_admin_formsets']
    assert len(formsets) == 2
    assert not any(item.has_add_permission or item.has_delete_permission for item in formsets)


def test_user_page_queries_do_not_grow_with_user_data(
    admin_client: Client, user_data: User, os_entry: Entry, blueprint: Blueprint
) -> None:
    with CaptureQueriesContext(connection) as few:
        change_page(admin_client, user_data)
    Favorite.objects.create(user=user_data, entry=os_entry)
    CompletedStep.objects.create(user=user_data, step=blueprint.steps.get(slug='ordner-anlegen'))
    with CaptureQueriesContext(connection) as more:
        change_page(admin_client, user_data)
    assert len(more) == len(few)


def test_admin_delete_removes_user_data(
    admin_client: Client, user_data: User, other_data: User
) -> None:
    url = reverse('admin:app_accounts_user_delete', args=[user_data.pk])
    admin_client.post(url, {'post': 'yes'})
    assert list(Favorite.objects.values_list('user', flat=True)) == [other_data.pk]
    assert list(CompletedStep.objects.values_list('user', flat=True)) == [other_data.pk]
