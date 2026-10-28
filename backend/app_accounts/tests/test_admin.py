import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

User = get_user_model()

pytestmark = pytest.mark.django_db

PASSWORD = 'Kaffee-Tasse-2026!'


def add_user(admin_client: Client, **changes: str) -> HttpResponse:
    data = {'email': 'grace@example.com', 'usable_password': 'true'}
    data |= {'password1': PASSWORD, 'password2': PASSWORD} | changes
    return admin_client.post(reverse('admin:app_accounts_user_add'), data)


def change_user(admin_client: Client, user: User, **changes: str) -> HttpResponse:
    url = reverse('admin:app_accounts_user_change', args=[user.pk])
    data = {'email': user.email, 'accent': user.accent, 'is_active': 'on'} | changes
    return admin_client.post(url, data)


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
