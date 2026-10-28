import pytest
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client

from app_accounts.models import User


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    cache.clear()


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create_user('ada@example.com', 'Kaffee-Tasse-2026!')


@pytest.fixture
def staff_user(db: None) -> User:
    staff = User.objects.create_user('staff@example.com', 'Kaffee-Tasse-2026!', is_staff=True)
    staff.user_permissions.set(Permission.objects.filter(content_type__model='user'))
    return staff


@pytest.fixture
def staff_client(client: Client, staff_user: User) -> Client:
    client.force_login(staff_user)
    return client
