import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Model, ProtectedError
from django.utils import translation

from app_content.models import CodeLanguage, Concept, Entry, Group, Subtopic, Topic

pytestmark = pytest.mark.django_db


def all_error_codes(obj: Model) -> dict[str, list[str]]:
    with pytest.raises(ValidationError) as error:
        obj.full_clean()
    return {field: [item.code for item in items] for field, items in error.value.error_dict.items()}


def error_codes(obj: Model, field: str) -> list[str]:
    return all_error_codes(obj)[field]


# Names
def test_str_returns_name(group: Group, topic: Topic, subtopic: Subtopic) -> None:
    assert [str(group), str(topic), str(subtopic)] == ['Backend', 'Python', 'Schleifen']


def test_name_follows_active_language(subtopic: Subtopic) -> None:
    with translation.override('en'):
        assert subtopic.name == 'Loops'


def test_name_falls_back_to_german(group: Group) -> None:
    tools = Group.objects.create(slug='tools', name_de='Werkzeuge')
    with translation.override('en'):
        assert tools.name == 'Werkzeuge'


# Order
def test_groups_are_ordered_by_position(group: Group) -> None:
    frontend = Group.objects.create(slug='frontend', name_de='Frontend', position=-1)
    assert list(Group.objects.all()) == [frontend, group]


def test_topics_are_ordered_by_position(group: Group, topic: Topic) -> None:
    django = Topic.objects.create(group=group, slug='django', name_de='Django', position=-1)
    assert list(group.topics.all()) == [django, topic]


def test_subtopics_are_ordered_by_position(topic: Topic, subtopic: Subtopic) -> None:
    first = Subtopic.objects.create(topic=topic, slug='umgebung', name_de='Umgebung', position=-1)
    assert list(topic.subtopics.all()) == [first, subtopic]


# Slugs
def test_group_slug_is_unique(group: Group) -> None:
    with pytest.raises(IntegrityError):
        Group.objects.create(slug='backend', name_de='Doppelt')


def test_topic_slug_is_unique(group: Group, topic: Topic) -> None:
    with pytest.raises(IntegrityError):
        Topic.objects.create(group=group, slug='python', name_de='Doppelt')


def test_topic_slug_debuggen_is_rejected(group: Group) -> None:
    topic = Topic(group=group, slug='debuggen', name_de='Debuggen', color='#000000')
    assert error_codes(topic, 'slug') == ['reserved']


@pytest.mark.parametrize('slug', ['debuggen', 'Debuggen'])
def test_topic_slug_debuggen_is_blocked_in_database(group: Group, slug: str) -> None:
    with pytest.raises(IntegrityError):
        Topic.objects.create(group=group, slug=slug, name_de='Debuggen')


@pytest.mark.parametrize('slug', ['Python', 'node_npm', 'git-', '-git', 'git--hub', 'git\n'])
@pytest.mark.parametrize('fixture', ['group', 'topic', 'subtopic', 'entry', 'concept'])
def test_slug_must_be_lowercase_with_hyphens(
    request: pytest.FixtureRequest, fixture: str, slug: str
) -> None:
    obj = request.getfixturevalue(fixture)
    obj.slug = slug
    assert error_codes(obj, 'slug') == ['invalid']


@pytest.mark.parametrize('slug', ['node-npm', 'css3', 'git-und-github'])
def test_slug_accepts_lowercase_with_hyphens(topic: Topic, slug: str) -> None:
    topic.slug = slug
    topic.full_clean()


def test_subtopic_slug_is_unique_per_topic(topic: Topic, subtopic: Subtopic) -> None:
    with pytest.raises(IntegrityError):
        Subtopic.objects.create(topic=topic, slug='schleifen', name_de='Doppelt')


def test_subtopic_slug_repeats_in_other_topic(group: Group, subtopic: Subtopic) -> None:
    javascript = Topic.objects.create(group=group, slug='javascript', name_de='JavaScript')
    loops = Subtopic.objects.create(topic=javascript, slug='schleifen', name_de='Schleifen')
    assert loops.pk


# Color
@pytest.mark.parametrize('color', ['#3776ab', '#3776AB'])
def test_topic_accepts_hex_color(topic: Topic, color: str) -> None:
    topic.color = color
    topic.full_clean()


@pytest.mark.parametrize('color', ['3776ab', '#37a', 'blue', '#3776zz'])
def test_topic_rejects_invalid_color(topic: Topic, color: str) -> None:
    topic.color = color
    assert error_codes(topic, 'color') == ['invalid']


def test_topic_rejects_color_with_line_break(topic: Topic) -> None:
    topic.color = '#3776ab\n'
    assert 'color' in all_error_codes(topic)


# Delete
def test_group_with_topics_cannot_be_deleted(group: Group, topic: Topic) -> None:
    with pytest.raises(ProtectedError):
        group.delete()


def test_deleting_topic_deletes_subtopics(topic: Topic, subtopic: Subtopic) -> None:
    topic.delete()
    assert not Subtopic.objects.exists()


# Entries and concepts
CONTENT_MODELS = [Entry, Concept]


def test_entry_and_concept_str_return_title(entry: Entry, concept: Concept) -> None:
    assert [str(entry), str(concept)] == ['For-Schleife', 'Die for-Schleife']


def test_entry_texts_follow_active_language(entry: Entry) -> None:
    with translation.override('en'):
        assert [entry.title, entry.description] == ['For loop', 'Repeats code for each item.']


def test_entry_texts_fall_back_to_german(os_entry: Entry) -> None:
    with translation.override('en'):
        assert os_entry.title == 'venv aktivieren'
        assert os_entry.code_unix == 'source .venv/bin/activate'


def test_concept_texts_follow_active_language(concept: Concept) -> None:
    with translation.override('en'):
        assert [concept.title, concept.summary] == ['The for loop', 'Runs over all items.']
        assert concept.note == 'Nicht die Liste in der Schleife ändern.'


def test_code_languages_match_frontend() -> None:
    expected = ['terminal', 'python', 'javascript', 'typescript', 'html', 'css', 'gitignore', 'env']
    assert CodeLanguage.values == expected


@pytest.mark.parametrize('fixture', ['entry', 'concept'])
def test_content_rejects_unknown_language(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    obj.language = 'cobol'
    assert error_codes(obj, 'language') == ['invalid_choice']


def test_entry_requires_all_fields_except_unix_code(db: None) -> None:
    errors = all_error_codes(Entry())
    assert set(errors) == {'subtopic', 'slug', 'title', 'description', 'language', 'code'}


def test_concept_requires_all_fields_except_note(db: None) -> None:
    errors = all_error_codes(Concept())
    expected = {'subtopic', 'slug', 'title', 'summary', 'explanation', 'language', 'code'}
    assert set(errors) == expected


def test_entry_without_unix_code_is_valid(entry: Entry) -> None:
    entry.full_clean()


def test_concept_without_note_is_valid(concept: Concept) -> None:
    concept.note_de = ''
    concept.full_clean()


@pytest.mark.parametrize('fixture', ['entry', 'concept'])
def test_content_title_is_limited(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    obj.title_de = 'x' * 121
    assert error_codes(obj, 'title_de') == ['max_length']


@pytest.mark.parametrize('fixture', ['entry', 'concept'])
def test_content_slug_is_limited(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    obj.slug = 'x' * 81
    assert error_codes(obj, 'slug') == ['max_length']


@pytest.mark.parametrize('model', CONTENT_MODELS)
def test_content_slug_is_unique(entry: Entry, concept: Concept, model: type[Model]) -> None:
    with pytest.raises(IntegrityError):
        model.objects.create(
            subtopic=entry.subtopic, language='python', slug='for-schleife', title_de='Doppelt'
        )


def test_entry_and_concept_may_share_slug(entry: Entry, concept: Concept) -> None:
    assert entry.slug == concept.slug


# Code
def test_entry_code_is_text_without_unix_code(entry: Entry) -> None:
    assert entry.os_code == 'for item in items: print(item)'


def test_entry_code_is_split_by_os_with_unix_code(os_entry: Entry) -> None:
    assert os_entry.os_code == {
        'win': r'.venv\Scripts\activate',
        'unix': 'source .venv/bin/activate',
    }


def test_entry_code_follows_active_language(os_entry: Entry) -> None:
    os_entry.code_en = r'.venv\Scripts\Activate.ps1'
    with translation.override('en'):
        assert os_entry.os_code == {
            'win': r'.venv\Scripts\Activate.ps1',
            'unix': 'source .venv/bin/activate',
        }


# Content order
@pytest.mark.parametrize('model', CONTENT_MODELS)
def test_content_is_ordered_by_topic_subtopic_and_position(
    group: Group, topic: Topic, subtopic: Subtopic, model: type[Model]
) -> None:
    git = Topic.objects.create(group=group, slug='git', name_de='Git', position=-1)
    alltag = Subtopic.objects.create(topic=git, slug='alltag', name_de='Alltag')
    first = Subtopic.objects.create(topic=topic, slug='umgebung', name_de='Umgebung', position=-1)
    late = model.objects.create(
        subtopic=subtopic, language='python', slug='spaet', title_de='Spät', position=-5
    )
    early = model.objects.create(
        subtopic=subtopic, language='python', slug='frueh', title_de='Früh', position=-9
    )
    python_first = model.objects.create(
        subtopic=first, language='python', slug='venv', title_de='venv', position=9
    )
    git_item = model.objects.create(
        subtopic=alltag, language='python', slug='status', title_de='Status', position=9
    )
    assert list(model.objects.all()) == [git_item, python_first, early, late]


# Content delete
@pytest.mark.parametrize('fixture', ['entry', 'concept'])
def test_subtopic_with_content_cannot_be_deleted(
    request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    with pytest.raises(ProtectedError):
        obj.subtopic.delete()


@pytest.mark.parametrize('fixture', ['entry', 'concept'])
def test_topic_with_content_cannot_be_deleted(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    with pytest.raises(ProtectedError):
        obj.subtopic.topic.delete()
    assert Subtopic.objects.filter(pk=obj.subtopic.pk).exists()


@pytest.mark.parametrize('model', CONTENT_MODELS)
def test_content_with_same_position_keeps_creation_order(
    subtopic: Subtopic, model: type[Model]
) -> None:
    first = model.objects.create(
        subtopic=subtopic, language='python', slug='erster', title_de='Erster'
    )
    second = model.objects.create(
        subtopic=subtopic, language='python', slug='zweiter', title_de='Zweiter'
    )
    assert list(model.objects.all()) == [first, second]


# Content database rules
@pytest.mark.parametrize('model', CONTENT_MODELS)
@pytest.mark.parametrize('language', ['cobol', '', 'Python'])
def test_content_language_is_checked_in_database(
    subtopic: Subtopic, model: type[Model], language: str
) -> None:
    with pytest.raises(IntegrityError):
        model.objects.create(subtopic=subtopic, slug='neu', title_de='Neu', language=language)


@pytest.mark.parametrize('model', CONTENT_MODELS)
@pytest.mark.parametrize('slug', ['', 'Git', 'git_status', 'git-', 'git--status', 'git\n', 'a/b'])
def test_content_slug_is_checked_in_database(
    subtopic: Subtopic, model: type[Model], slug: str
) -> None:
    with pytest.raises(IntegrityError):
        model.objects.create(subtopic=subtopic, slug=slug, title_de='Neu', language='python')


@pytest.mark.parametrize('model', CONTENT_MODELS)
def test_content_with_valid_values_passes_database_checks(
    subtopic: Subtopic, model: type[Model]
) -> None:
    obj = model.objects.create(
        subtopic=subtopic, slug='git-status-2', title_de='Neu', language='env'
    )
    assert obj.pk


# Unix code per language
def test_entry_unix_code_in_english_needs_german_unix_code(entry: Entry) -> None:
    entry.code_unix_en = 'ls'
    assert error_codes(entry, 'code_unix_de') == ['required']


def test_entry_unix_code_in_both_languages_is_valid(os_entry: Entry) -> None:
    os_entry.code_unix_en = 'ls'
    os_entry.full_clean()


def test_entry_unix_code_only_in_german_is_valid(os_entry: Entry) -> None:
    os_entry.full_clean()
