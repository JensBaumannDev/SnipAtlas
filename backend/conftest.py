import pytest
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client
from rest_framework.test import APIClient

from app_accounts.models import User
from app_content.models import Concept, Entry, Group, Subtopic, Topic


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


@pytest.fixture
def entry(subtopic: Subtopic) -> Entry:
    return Entry.objects.create(
        subtopic=subtopic,
        slug='for-schleife',
        title_de='For-Schleife',
        title_en='For loop',
        description_de='Wiederholt Code für jedes Element.',
        description_en='Repeats code for each item.',
        language='python',
        code_de='for item in items: print(item)',
    )


@pytest.fixture
def os_entry(subtopic: Subtopic) -> Entry:
    return Entry.objects.create(
        subtopic=subtopic,
        slug='venv-aktivieren',
        title_de='venv aktivieren',
        description_de='Schaltet die virtuelle Umgebung ein.',
        language='terminal',
        code_de=r'.venv\Scripts\activate',
        code_unix_de='source .venv/bin/activate',
    )


@pytest.fixture
def concept(subtopic: Subtopic) -> Concept:
    return Concept.objects.create(
        subtopic=subtopic,
        slug='for-schleife',
        title_de='Die for-Schleife',
        title_en='The for loop',
        summary_de='Läuft über alle Elemente.',
        summary_en='Runs over all items.',
        explanation_de='Python nimmt nacheinander jedes Element.',
        explanation_en='Python takes each item in turn.',
        language='python',
        code_de='for item in items: print(item)',
        note_de='Nicht die Liste in der Schleife ändern.',
    )
