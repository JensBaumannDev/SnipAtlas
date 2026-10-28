import pytest
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client
from rest_framework.test import APIClient

from app_accounts.models import User
from app_content.models import Group, Subtopic, Topic


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


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


# Content
@pytest.fixture
def group(db: None) -> Group:
    return Group.objects.create(slug='backend', name_de='Backend', name_en='Backend')


@pytest.fixture
def topic(group: Group) -> Topic:
    return Topic.objects.create(
        group=group, slug='python', name_de='Python', name_en='Python', color='#3776ab'
    )


@pytest.fixture
def subtopic(topic: Topic) -> Subtopic:
    return Subtopic.objects.create(
        topic=topic, slug='schleifen', name_de='Schleifen', name_en='Loops'
    )
