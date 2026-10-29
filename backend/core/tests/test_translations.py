from pathlib import Path

import pytest
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import translation
from modeltranslation.fields import TranslationField

from app_accounts.models import Accent, Language, OperatingSystem, Theme
from app_content.models import Entry, News, NewsArea, Topic, validate_topic_slug
from app_feedback.models import BugType, EntryArea, ImprovementArea, Kind, Status

CATALOG = Path(settings.LOCALE_PATHS[0]) / 'de' / 'LC_MESSAGES' / 'django.po'
OWN_APPS = ('app_accounts', 'app_content', 'app_feedback')
DJANGO_USER_FIELDS = {
    'id',
    'password',
    'last_login',
    'is_superuser',
    'groups',
    'user_permissions',
    'is_staff',
    'is_active',
    'date_joined',
}

FIELD_NAMES = [
    ('app_accounts.user', 'email', 'E-Mail-Adresse', 'email address'),
    ('app_accounts.user', 'notify_by_mail', 'Benachrichtigung per E-Mail', 'notify by mail'),
    ('app_accounts.user', 'accent', 'Akzentfarbe', 'accent color'),
    ('app_accounts.user', 'os', 'Betriebssystem', 'operating system'),
    ('app_accounts.user', 'theme', 'Farbschema', 'theme'),
    ('app_accounts.user', 'language', 'Sprache', 'language'),
    ('app_accounts.user', 'project_name', 'Projektname', 'project name'),
    ('app_accounts.user', 'project_github_user', 'GitHub-Nutzer', 'GitHub user'),
    ('app_accounts.user', 'project_repo', 'Repository', 'repository'),
    ('app_accounts.user', 'project_domain', 'Domain', 'domain'),
    ('app_accounts.user', 'project_server_user', 'Server-Nutzer', 'server user'),
    ('app_accounts.user', 'project_server_ip', 'Server-IP', 'server IP'),
    ('app_accounts.favorite', 'user', 'Nutzer', 'user'),
    ('app_accounts.favorite', 'entry', 'Befehl', 'command'),
    ('app_accounts.favorite', 'created_at', 'Erstellt am', 'created at'),
    ('app_accounts.completedstep', 'user', 'Nutzer', 'user'),
    ('app_accounts.completedstep', 'step', 'Anleitungsschritt', 'guide step'),
    ('app_accounts.completedstep', 'created_at', 'Erstellt am', 'created at'),
    ('app_content.group', 'slug', 'Slug', 'slug'),
    ('app_content.group', 'name', 'Name', 'name'),
    ('app_content.group', 'position', 'Position', 'position'),
    ('app_content.topic', 'group', 'Themengruppe', 'topic group'),
    ('app_content.topic', 'slug', 'Slug', 'slug'),
    ('app_content.topic', 'name', 'Name', 'name'),
    ('app_content.topic', 'color', 'Farbe', 'color'),
    ('app_content.topic', 'position', 'Position', 'position'),
    ('app_content.subtopic', 'topic', 'Thema', 'topic'),
    ('app_content.subtopic', 'slug', 'Slug', 'slug'),
    ('app_content.subtopic', 'name', 'Name', 'name'),
    ('app_content.subtopic', 'position', 'Position', 'position'),
    ('app_content.entry', 'subtopic', 'Unterordner', 'subtopic'),
    ('app_content.entry', 'slug', 'Slug', 'slug'),
    ('app_content.entry', 'title', 'Titel', 'title'),
    ('app_content.entry', 'language', 'Code-Sprache', 'code language'),
    ('app_content.entry', 'code', 'Code', 'code'),
    ('app_content.entry', 'position', 'Position', 'position'),
    ('app_content.entry', 'description', 'Beschreibung', 'description'),
    ('app_content.entry', 'code_unix', 'Code für macOS/Linux', 'code for macOS/Linux'),
    ('app_content.concept', 'subtopic', 'Unterordner', 'subtopic'),
    ('app_content.concept', 'slug', 'Slug', 'slug'),
    ('app_content.concept', 'title', 'Titel', 'title'),
    ('app_content.concept', 'language', 'Code-Sprache', 'code language'),
    ('app_content.concept', 'code', 'Code', 'code'),
    ('app_content.concept', 'position', 'Position', 'position'),
    ('app_content.concept', 'summary', 'Zusammenfassung', 'summary'),
    ('app_content.concept', 'explanation', 'Erklärung', 'explanation'),
    ('app_content.concept', 'note', 'Hinweis', 'note'),
    ('app_content.errormessage', 'language', 'Code-Sprache', 'code language'),
    ('app_content.errormessage', 'code', 'Code', 'code'),
    ('app_content.errormessage', 'topic', 'Thema', 'topic'),
    ('app_content.errormessage', 'slug', 'Slug', 'slug'),
    ('app_content.errormessage', 'message', 'Meldung', 'message'),
    ('app_content.errormessage', 'meaning', 'Bedeutung', 'meaning'),
    ('app_content.errormessage', 'cause', 'Ursache', 'cause'),
    ('app_content.errormessage', 'position', 'Position', 'position'),
    ('app_content.errorstep', 'error', 'Fehlermeldung', 'error message'),
    ('app_content.errorstep', 'text', 'Text', 'text'),
    ('app_content.errorstep', 'position', 'Position', 'position'),
    ('app_content.debugguide', 'topic', 'Thema', 'topic'),
    ('app_content.debugguide', 'slug', 'Slug', 'slug'),
    ('app_content.debugguide', 'label', 'Name in der Seitenleiste', 'sidebar label'),
    ('app_content.debugguide', 'title', 'Titel', 'title'),
    ('app_content.debugguide', 'summary', 'Zusammenfassung', 'summary'),
    ('app_content.debugguide', 'position', 'Position', 'position'),
    ('app_content.debugguidestep', 'language', 'Code-Sprache', 'code language'),
    ('app_content.debugguidestep', 'code', 'Code', 'code'),
    ('app_content.debugguidestep', 'guide', 'Debug-Anleitung', 'debug guide'),
    ('app_content.debugguidestep', 'title', 'Titel', 'title'),
    ('app_content.debugguidestep', 'text', 'Text', 'text'),
    ('app_content.debugguidestep', 'code_unix', 'Code für macOS/Linux', 'code for macOS/Linux'),
    ('app_content.debugguidestep', 'position', 'Position', 'position'),
    ('app_content.blueprint', 'topic', 'Thema', 'topic'),
    ('app_content.blueprint', 'slug', 'Slug', 'slug'),
    ('app_content.blueprint', 'title', 'Titel', 'title'),
    ('app_content.blueprint', 'summary', 'Zusammenfassung', 'summary'),
    ('app_content.blueprint', 'position', 'Position', 'position'),
    ('app_content.blueprintstep', 'blueprint', 'Anleitung', 'guide'),
    ('app_content.blueprintstep', 'slug', 'Slug', 'slug'),
    ('app_content.blueprintstep', 'title', 'Titel', 'title'),
    ('app_content.blueprintstep', 'why', 'Warum', 'why'),
    ('app_content.blueprintstep', 'note', 'Hinweis', 'note'),
    ('app_content.blueprintstep', 'position', 'Position', 'position'),
    ('app_content.blueprintcode', 'step', 'Anleitungsschritt', 'guide step'),
    ('app_content.blueprintcode', 'language', 'Code-Sprache', 'code language'),
    ('app_content.blueprintcode', 'code', 'Code', 'code'),
    ('app_content.blueprintcode', 'code_unix', 'Code für macOS/Linux', 'code for macOS/Linux'),
    ('app_content.blueprintcode', 'position', 'Position', 'position'),
    ('app_content.glossaryterm', 'slug', 'Slug', 'slug'),
    ('app_content.glossaryterm', 'term', 'Begriff', 'term'),
    ('app_content.glossaryterm', 'definition', 'Definition', 'definition'),
    ('app_content.glossaryterm', 'concept', 'Grundlage', 'concept'),
    ('app_content.glossaryalias', 'term', 'Begriff', 'term'),
    ('app_content.glossaryalias', 'language', 'Sprache', 'language'),
    ('app_content.glossaryalias', 'name', 'Name', 'name'),
    ('app_content.news', 'date', 'Datum', 'date'),
    ('app_content.news', 'title', 'Titel', 'title'),
    ('app_content.news', 'area', 'Bereich', 'area'),
    ('app_content.news', 'topic', 'Thema', 'topic'),
    ('app_content.news', 'subtopic', 'Unterordner', 'subtopic'),
    ('app_feedback.suggestion', 'kind', 'Art', 'kind'),
    ('app_feedback.suggestion', 'user', 'Nutzer', 'user'),
    ('app_feedback.suggestion', 'email', 'E-Mail', 'email'),
    ('app_feedback.suggestion', 'status', 'Status', 'status'),
    ('app_feedback.suggestion', 'answer', 'Antwort', 'answer'),
    ('app_feedback.suggestion', 'created_at', 'Eingegangen am', 'received at'),
    ('app_feedback.suggestion', 'answered_at', 'Beantwortet am', 'answered at'),
    ('app_feedback.suggestion', 'area', 'Bereich', 'area'),
    ('app_feedback.suggestion', 'topic', 'Thema', 'topic'),
    ('app_feedback.suggestion', 'title', 'Titel', 'title'),
    ('app_feedback.suggestion', 'reason', 'Begründung', 'reason'),
    ('app_feedback.suggestion', 'example', 'Beispiel', 'example'),
    ('app_feedback.suggestion', 'source', 'Quelle', 'source'),
    ('app_feedback.suggestion', 'idea', 'Idee', 'idea'),
    ('app_feedback.suggestion', 'benefit', 'Nutzen', 'benefit'),
    ('app_feedback.suggestion', 'bug_type', 'Fehlerart', 'bug type'),
    ('app_feedback.suggestion', 'location', 'Fundstelle', 'location'),
    ('app_feedback.suggestion', 'problem', 'Problem', 'problem'),
    ('app_feedback.suggestion', 'correction', 'Korrektur', 'correction'),
    ('app_feedback.suggestion', 'environment', 'Umgebung', 'environment'),
]

CHOICE_LABELS = [
    (Accent.BLUE, 'Blau', 'Blue'),
    (Accent.TEAL, 'Petrol', 'Teal'),
    (Accent.RASPBERRY, 'Himbeere', 'Raspberry'),
    (Accent.FUCHSIA, 'Fuchsia', 'Fuchsia'),
    (OperatingSystem.WIN, 'Windows', 'Windows'),
    (OperatingSystem.UNIX, 'macOS/Linux', 'macOS/Linux'),
    (Theme.LIGHT, 'Hell', 'Light'),
    (Theme.DARK, 'Dunkel', 'Dark'),
    (Theme.SYSTEM, 'System', 'System'),
    (Language.AUTO, 'Automatisch', 'Automatic'),
    (Language.DE, 'Deutsch', 'Deutsch'),
    (Language.EN, 'English', 'English'),
    (NewsArea.COMMANDS, 'Befehle', 'Commands'),
    (NewsArea.CONCEPTS, 'Grundlagen', 'Concepts'),
    (NewsArea.BLUEPRINTS, 'Anleitungen', 'Guides'),
    (NewsArea.ERRORS, 'Fehler', 'Errors'),
    (Kind.ENTRY, 'Ergänzung', 'New entry'),
    (Kind.IMPROVEMENT, 'Verbesserung', 'Improvement'),
    (Kind.BUG, 'Fehler', 'Bug'),
    (Status.OPEN, 'Offen', 'Open'),
    (Status.DONE, 'Erledigt', 'Done'),
    (EntryArea.COMMAND, 'Befehl', 'Command'),
    (EntryArea.CONCEPT, 'Grundlage', 'Concept'),
    (EntryArea.ERROR, 'Fehlermeldung', 'Error message'),
    (ImprovementArea.CONTENT, 'Inhalte', 'Content'),
    (ImprovementArea.USABILITY, 'Bedienung', 'Usability'),
    (ImprovementArea.DESIGN, 'Design', 'Design'),
    (ImprovementArea.FEATURE, 'Funktion', 'Feature'),
    (ImprovementArea.OTHER, 'Sonstiges', 'Other'),
    (BugType.WRONG, 'Falsch', 'Wrong'),
    (BugType.OUTDATED, 'Veraltet', 'Outdated'),
    (BugType.BROKEN, 'Funktioniert nicht', 'Broken'),
    (BugType.TYPO, 'Tippfehler', 'Typo'),
]


def own_fields() -> set[tuple[str, str]]:
    fields = set()
    for app in OWN_APPS:
        for model in apps.get_app_config(app).get_models():
            for field in model._meta.concrete_fields:
                if isinstance(field, TranslationField) or field.name in DJANGO_USER_FIELDS:
                    continue
                fields.add((model._meta.label_lower, field.name))
    return fields


def own_choices() -> set[models.TextChoices]:
    return {label for label, _, _ in CHOICE_LABELS}


def read_catalog() -> list[tuple[str, str, bool]]:
    entries = []
    for block in CATALOG.read_text(encoding='utf-8').split('\n\n'):
        parts = {'msgid': '', 'msgstr': ''}
        current = None
        for line in block.splitlines():
            if line.startswith(('msgid ', 'msgstr ')):
                current, _, line = line.partition(' ')
            if current and line.startswith('"'):
                parts[current] += line[1:-1].replace('\\"', '"')
        entries.append((parts['msgid'], parts['msgstr'], '#, fuzzy' in block))
    return [entry for entry in entries if entry[0]]


def field_name(label: str, name: str) -> str:
    return str(apps.get_model(label)._meta.get_field(name).verbose_name)


# Fields
@pytest.mark.parametrize(('label', 'name', 'german', 'english'), FIELD_NAMES)
def test_field_name_is_german_and_english(label: str, name: str, german: str, english: str) -> None:
    with translation.override('de'):
        assert field_name(label, name) == german
    with translation.override('en'):
        assert field_name(label, name) == english


def test_every_own_field_has_a_name() -> None:
    assert own_fields() == {(label, name) for label, name, _, _ in FIELD_NAMES}


def test_translation_fields_carry_the_language() -> None:
    with translation.override('de'):
        assert field_name('app_content.entry', 'title_de') == 'Titel [de]'
    with translation.override('en'):
        assert field_name('app_content.entry', 'title_en') == 'title [en]'


# Choices
@pytest.mark.parametrize(('choice', 'german', 'english'), CHOICE_LABELS)
def test_choice_label_is_german_and_english(
    choice: models.TextChoices, german: str, english: str
) -> None:
    with translation.override('de'):
        assert str(choice.label) == german
    with translation.override('en'):
        assert str(choice.label) == english


def test_every_own_choice_has_a_label() -> None:
    enums = (Accent, OperatingSystem, Theme, Language, NewsArea, Kind, Status)
    enums += (EntryArea, ImprovementArea, BugType)
    assert {choice for enum in enums for choice in enum} == own_choices()


# Messages
@pytest.mark.parametrize(
    ('language', 'message'),
    [('de', 'Dieser Slug ist reserviert.'), ('en', 'This slug is reserved.')],
)
def test_reserved_slug_message_is_translated(language: str, message: str) -> None:
    with translation.override(language):
        with pytest.raises(ValidationError) as error:
            validate_topic_slug('debuggen')
        assert error.value.messages == [message]


@pytest.mark.parametrize(
    ('language', 'message'),
    [('de', 'Erst den deutschen Text eintragen.'), ('en', 'Add the German text first.')],
)
def test_german_first_message_is_translated(entry: Entry, language: str, message: str) -> None:
    entry.code_unix_en = 'ls'
    with translation.override(language):
        with pytest.raises(ValidationError) as error:
            entry.clean()
        assert error.value.message_dict == {'code_unix_de': [message]}


@pytest.mark.parametrize(
    ('language', 'message'),
    [
        ('de', 'Der Unterordner gehört zu einem anderen Thema.'),
        ('en', 'The subtopic belongs to another topic.'),
    ],
)
def test_news_message_is_translated(news: News, language: str, message: str) -> None:
    news.topic = Topic.objects.create(
        group=news.topic.group, slug='npm', name='npm', color='#000000'
    )
    with translation.override(language):
        with pytest.raises(ValidationError) as error:
            news.clean()
        assert error.value.message_dict == {'subtopic': [message]}


# Catalog
def test_catalog_has_no_missing_or_fuzzy_translation() -> None:
    entries = read_catalog()
    assert entries
    assert [msgid for msgid, msgstr, fuzzy in entries if not msgstr or fuzzy] == []


def test_compiled_catalog_matches_source() -> None:
    with translation.override('de'):
        wrong = [
            msgid for msgid, msgstr, _ in read_catalog() if translation.gettext(msgid) != msgstr
        ]
    assert wrong == []
