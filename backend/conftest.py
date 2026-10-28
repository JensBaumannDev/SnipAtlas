import pytest
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client
from rest_framework.test import APIClient

from app_accounts.models import User
from app_content.models import Concept, DebugGuide, Entry, ErrorMessage, Group, Subtopic, Topic


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


@pytest.fixture
def error_message(topic: Topic) -> ErrorMessage:
    error = ErrorMessage.objects.create(
        topic=topic,
        slug='module-not-found',
        message="ModuleNotFoundError: No module named 'django'",
        meaning_de='Python findet das Paket nicht.',
        meaning_en='Python cannot find the package.',
        cause_de='Die virtuelle Umgebung ist nicht aktiv.',
        cause_en='The virtual environment is not active.',
        language='terminal',
        code_de='pip install django',
    )
    error.steps.create(text_de='Paket installieren.', position=1)
    error.steps.create(text_de='Umgebung aktivieren.', text_en='Activate the environment.')
    return error


@pytest.fixture
def debug_guide(db: None) -> DebugGuide:
    guide = DebugGuide.objects.create(
        slug='vorgehen',
        label_de='Vorgehen',
        label_en='Approach',
        title_de='Der Ablauf bei jedem Fehler',
        title_en='The process for every error',
        summary_de='Vier Schritte für jeden Fehler.',
        summary_en='Four steps for every error.',
    )
    guide.steps.create(
        title_de='Änderungen ansehen',
        text_de='git diff zeigt sie.',
        language='terminal',
        code_de='git diff',
        position=1,
    )
    guide.steps.create(title_de='Die Meldung lesen', text_de='Die wichtige Zeile steht unten.')
    return guide


@pytest.fixture
def topic_guide(topic: Topic) -> DebugGuide:
    guide = DebugGuide.objects.create(
        topic=topic,
        slug='python-debuggen',
        title_de='Python debuggen',
        summary_de='Mit Tests und Ausgaben.',
    )
    guide.steps.create(
        title_de='Tests starten',
        text_de='Startet alle Tests.',
        language='terminal',
        code_de='python manage.py test',
        code_unix_de='python3 manage.py test',
    )
    return guide
