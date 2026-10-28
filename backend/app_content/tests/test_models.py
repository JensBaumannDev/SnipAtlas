import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Model, ProtectedError
from django.utils import translation

from app_content.models import (
    Blueprint,
    BlueprintCode,
    BlueprintStep,
    CodeLanguage,
    Concept,
    DebugGuide,
    DebugGuideStep,
    Entry,
    ErrorMessage,
    ErrorStep,
    Group,
    Subtopic,
    Topic,
)

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


# Errors
def test_error_str_returns_message(error_message: ErrorMessage) -> None:
    assert str(error_message) == "ModuleNotFoundError: No module named 'django'"


def test_steps_str_return_text_and_title(error_message: ErrorMessage, step: DebugGuideStep) -> None:
    assert [str(error_message.steps.first()), str(step)] == [
        'Umgebung aktivieren.',
        'Änderungen ansehen',
    ]


def test_error_texts_follow_active_language(error_message: ErrorMessage) -> None:
    with translation.override('en'):
        assert [error_message.meaning, error_message.cause] == [
            'Python cannot find the package.',
            'The virtual environment is not active.',
        ]
        assert error_message.code == 'pip install django'


def test_error_message_is_not_translated() -> None:
    fields = {field.name for field in ErrorMessage._meta.get_fields()}
    assert 'message' in fields
    assert 'message_en' not in fields


def test_error_requires_all_fields_except_solution(db: None) -> None:
    errors = all_error_codes(ErrorMessage())
    assert set(errors) == {'topic', 'slug', 'message', 'meaning', 'cause'}


def test_error_without_solution_is_valid(error_message: ErrorMessage) -> None:
    error_message.language = ''
    error_message.code_de = ''
    error_message.full_clean()


def test_error_message_is_limited(error_message: ErrorMessage) -> None:
    error_message.message = 'x' * 301
    assert error_codes(error_message, 'message') == ['max_length']


def test_error_slug_is_unique(error_message: ErrorMessage) -> None:
    with pytest.raises(IntegrityError):
        ErrorMessage.objects.create(topic=error_message.topic, slug='module-not-found')


def test_error_steps_are_ordered_by_position(error_message: ErrorMessage) -> None:
    texts = [step.text for step in error_message.steps.all()]
    assert texts == ['Umgebung aktivieren.', 'Paket installieren.']


def test_error_step_text_follows_active_language(error_message: ErrorMessage) -> None:
    with translation.override('en'):
        texts = [step.text for step in error_message.steps.all()]
    assert texts == ['Activate the environment.', 'Paket installieren.']


def test_error_step_requires_text(error_message: ErrorMessage) -> None:
    assert set(all_error_codes(ErrorStep(error=error_message))) == {'text'}


def test_deleting_error_deletes_steps(error_message: ErrorMessage) -> None:
    error_message.delete()
    assert not ErrorStep.objects.exists()


def test_topic_with_errors_cannot_be_deleted(error_message: ErrorMessage) -> None:
    with pytest.raises(ProtectedError):
        error_message.topic.delete()


def test_errors_are_ordered_by_topic_and_position(group: Group, topic: Topic) -> None:
    git = Topic.objects.create(group=group, slug='git', name_de='Git', position=-1)
    late = ErrorMessage.objects.create(topic=topic, slug='spaet', position=2)
    early = ErrorMessage.objects.create(topic=topic, slug='frueh', position=1)
    git_error = ErrorMessage.objects.create(topic=git, slug='push', position=9)
    assert list(ErrorMessage.objects.all()) == [git_error, early, late]


# Debug guides
def test_debug_guide_str_returns_title(debug_guide: DebugGuide) -> None:
    assert str(debug_guide) == 'Der Ablauf bei jedem Fehler'


def test_debug_guide_texts_follow_active_language(debug_guide: DebugGuide) -> None:
    with translation.override('en'):
        assert [debug_guide.label, debug_guide.title] == ['Approach', 'The process for every error']
        assert debug_guide.steps.first().title == 'Die Meldung lesen'


def test_general_debug_guide_is_valid(debug_guide: DebugGuide) -> None:
    debug_guide.full_clean()


def test_topic_debug_guide_is_valid(topic_guide: DebugGuide) -> None:
    topic_guide.full_clean()


def test_debug_guide_requires_slug_title_summary_and_label(db: None) -> None:
    errors = all_error_codes(DebugGuide())
    assert set(errors) == {'slug', 'title', 'summary', 'label_de'}


def test_general_debug_guide_requires_label(debug_guide: DebugGuide) -> None:
    debug_guide.label_de = ''
    assert error_codes(debug_guide, 'label_de') == ['required']


@pytest.mark.parametrize('field', ['label_de', 'label_en'])
def test_topic_debug_guide_rejects_label(topic_guide: DebugGuide, field: str) -> None:
    setattr(topic_guide, field, 'Python')
    assert error_codes(topic_guide, field) == ['invalid']


def test_debug_guide_label_is_limited(debug_guide: DebugGuide) -> None:
    debug_guide.label_de = 'x' * 31
    assert error_codes(debug_guide, 'label_de') == ['max_length']


def test_debug_guide_slug_is_unique(debug_guide: DebugGuide) -> None:
    with pytest.raises(IntegrityError):
        DebugGuide.objects.create(slug='vorgehen', title_de='Doppelt')


def test_debug_guides_start_with_general_ones(
    group: Group, topic: Topic, topic_guide: DebugGuide, debug_guide: DebugGuide
) -> None:
    git = Topic.objects.create(group=group, slug='git', name_de='Git', position=-1)
    git_guide = DebugGuide.objects.create(topic=git, slug='git-debuggen', position=9)
    first = DebugGuide.objects.create(slug='browser', label_de='Browser', position=-1)
    assert list(DebugGuide.objects.all()) == [first, debug_guide, git_guide, topic_guide]


def test_topic_with_debug_guides_cannot_be_deleted(topic_guide: DebugGuide) -> None:
    with pytest.raises(ProtectedError):
        topic_guide.topic.delete()


def test_deleting_debug_guide_deletes_steps(debug_guide: DebugGuide) -> None:
    debug_guide.delete()
    assert not DebugGuideStep.objects.exists()


# Debug guide steps
def guide_step(guide: DebugGuide, **fields: str) -> DebugGuideStep:
    return DebugGuideStep(guide=guide, **({'title_de': 'Schritt', 'text_de': 'Text'} | fields))


def test_debug_guide_steps_are_ordered_by_position(debug_guide: DebugGuide) -> None:
    titles = [step.title for step in debug_guide.steps.all()]
    assert titles == ['Die Meldung lesen', 'Änderungen ansehen']


def test_debug_guide_step_requires_title_and_text(debug_guide: DebugGuide) -> None:
    errors = all_error_codes(DebugGuideStep(guide=debug_guide))
    assert set(errors) == {'title', 'text'}


def test_debug_guide_step_title_is_limited(debug_guide: DebugGuide) -> None:
    step = guide_step(debug_guide, title_de='x' * 121)
    assert error_codes(step, 'title_de') == ['max_length']


def test_debug_guide_step_without_code_is_valid(debug_guide: DebugGuide) -> None:
    guide_step(debug_guide).full_clean()


def test_debug_guide_step_code_is_text_without_unix_code(debug_guide: DebugGuide) -> None:
    assert debug_guide.steps.last().os_code == 'git diff'


def test_debug_guide_step_code_is_split_by_os(topic_guide: DebugGuide) -> None:
    assert topic_guide.steps.get().os_code == {
        'win': 'python manage.py test',
        'unix': 'python3 manage.py test',
    }


def test_debug_guide_step_unix_code_needs_code(debug_guide: DebugGuide) -> None:
    step = guide_step(debug_guide, code_unix_de='ls')
    assert error_codes(step, 'code_de') == ['required']


def test_debug_guide_step_unix_code_in_english_needs_german(debug_guide: DebugGuide) -> None:
    step = guide_step(debug_guide, language='terminal', code_de='dir', code_unix_en='ls')
    assert error_codes(step, 'code_unix_de') == ['required']


# Optional code
OPTIONAL_CODE = ['error_message', 'step']


@pytest.fixture
def step(debug_guide: DebugGuide) -> DebugGuideStep:
    return debug_guide.steps.last()


@pytest.mark.parametrize('fixture', OPTIONAL_CODE)
def test_code_without_language_is_rejected(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    obj.language = ''
    assert error_codes(obj, 'language') == ['required']


@pytest.mark.parametrize('fixture', OPTIONAL_CODE)
def test_language_without_code_is_rejected(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    obj.code_de = ''
    assert error_codes(obj, 'code_de') == ['required']


@pytest.mark.parametrize('fixture', OPTIONAL_CODE)
def test_english_code_without_german_code_is_rejected(
    request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    obj.language, obj.code_de, obj.code_en = '', '', 'ls'
    assert error_codes(obj, 'code_de') == ['required']


@pytest.mark.parametrize('fixture', OPTIONAL_CODE)
def test_optional_code_rejects_unknown_language(
    request: pytest.FixtureRequest, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    obj.language = 'cobol'
    assert error_codes(obj, 'language') == ['invalid_choice']


@pytest.mark.parametrize('language', ['cobol', 'Python'])
def test_error_language_is_checked_in_database(topic: Topic, language: str) -> None:
    with pytest.raises(IntegrityError):
        ErrorMessage.objects.create(topic=topic, slug='neu', language=language)


@pytest.mark.parametrize('language', ['cobol', 'Python'])
def test_debug_step_language_is_checked_in_database(debug_guide: DebugGuide, language: str) -> None:
    with pytest.raises(IntegrityError):
        debug_guide.steps.create(title_de='Neu', language=language)


@pytest.mark.parametrize('model', [ErrorMessage, DebugGuide])
@pytest.mark.parametrize('slug', ['', 'Git', 'git_push', 'git-', 'git\n', 'a/b'])
def test_error_and_guide_slug_is_checked_in_database(
    topic: Topic, model: type[Model], slug: str
) -> None:
    with pytest.raises(IntegrityError):
        model.objects.create(topic=topic, slug=slug)


@pytest.mark.parametrize('model', [ErrorMessage, DebugGuide])
def test_error_and_guide_with_valid_values_pass_database_checks(
    topic: Topic, model: type[Model]
) -> None:
    assert model.objects.create(topic=topic, slug='git-push-2').pk


# Limits and order
@pytest.mark.parametrize('fixture', ['error_message', 'debug_guide'])
def test_error_and_guide_slug_is_limited(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    obj.slug = 'x' * 81
    assert error_codes(obj, 'slug') == ['max_length']


def test_steps_with_same_position_keep_creation_order(
    error_message: ErrorMessage, debug_guide: DebugGuide
) -> None:
    first = error_message.steps.create(text_de='Erster', position=5)
    second = error_message.steps.create(text_de='Zweiter', position=5)
    step_first = debug_guide.steps.create(title_de='Erster', position=5)
    step_second = debug_guide.steps.create(title_de='Zweiter', position=5)
    assert list(error_message.steps.all())[-2:] == [first, second]
    assert list(debug_guide.steps.all())[-2:] == [step_first, step_second]


# Blueprints
@pytest.fixture
def venv_code(venv_step: BlueprintStep) -> BlueprintCode:
    return venv_step.codes.get()


def test_blueprint_parts_str(
    blueprint: Blueprint, venv_step: BlueprintStep, venv_code: BlueprintCode
) -> None:
    assert [str(blueprint), str(venv_step), str(venv_code)] == [
        'Neues Django-Projekt anlegen',
        'Virtuelle Umgebung einrichten',
        'Terminal',
    ]


def test_blueprint_texts_follow_active_language(
    blueprint: Blueprint, venv_step: BlueprintStep, venv_code: BlueprintCode
) -> None:
    with translation.override('en'):
        assert [blueprint.title, blueprint.summary] == [
            'Create a new Django project',
            'From an empty folder to the first model.',
        ]
        assert [venv_step.title, venv_step.why, venv_step.note] == [
            'Set up a virtual environment',
            'Jedes Projekt bekommt eigene Pakete.',
            'Danach steht (env) vor der Eingabezeile.',
        ]
        assert venv_code.os_code == {'win': 'python -m venv env', 'unix': 'python3 -m venv env'}


def test_blueprint_parts_are_valid(
    blueprint: Blueprint, venv_step: BlueprintStep, venv_code: BlueprintCode
) -> None:
    for obj in (blueprint, venv_step, venv_code):
        obj.full_clean()


def test_blueprint_requires_all_fields(db: None) -> None:
    assert set(all_error_codes(Blueprint())) == {'topic', 'slug', 'title', 'summary'}


def test_blueprint_step_requires_all_fields_except_note(blueprint: Blueprint) -> None:
    assert set(all_error_codes(BlueprintStep(blueprint=blueprint))) == {'slug', 'title', 'why'}


def test_blueprint_step_without_note_is_valid(venv_step: BlueprintStep) -> None:
    venv_step.note_de = ''
    venv_step.full_clean()


def test_blueprint_code_requires_language_and_code(venv_step: BlueprintStep) -> None:
    assert set(all_error_codes(BlueprintCode(step=venv_step))) == {'language', 'code'}


@pytest.mark.parametrize('fixture', ['blueprint', 'venv_step'])
def test_blueprint_and_step_title_is_limited(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    obj.title_de = 'x' * 121
    assert error_codes(obj, 'title_de') == ['max_length']


@pytest.mark.parametrize('fixture', ['blueprint', 'venv_step'])
def test_blueprint_and_step_slug_is_limited(request: pytest.FixtureRequest, fixture: str) -> None:
    obj = request.getfixturevalue(fixture)
    obj.slug = 'x' * 81
    assert error_codes(obj, 'slug') == ['max_length']


@pytest.mark.parametrize('fixture', ['blueprint', 'venv_step'])
@pytest.mark.parametrize('slug', ['Ordner', 'ordner_anlegen', 'ordner-', 'ordner anlegen'])
def test_blueprint_and_step_reject_invalid_slug(
    request: pytest.FixtureRequest, fixture: str, slug: str
) -> None:
    obj = request.getfixturevalue(fixture)
    obj.slug = slug
    assert 'invalid' in error_codes(obj, 'slug')


def test_blueprint_code_rejects_unknown_language(venv_code: BlueprintCode) -> None:
    venv_code.language = 'cobol'
    assert error_codes(venv_code, 'language') == ['invalid_choice']


def test_blueprint_slug_is_unique(blueprint: Blueprint) -> None:
    with pytest.raises(IntegrityError):
        Blueprint.objects.create(topic=blueprint.topic, slug='django-projekt-anlegen')


def test_blueprint_step_slug_is_unique_per_blueprint(blueprint: Blueprint) -> None:
    with pytest.raises(IntegrityError):
        blueprint.steps.create(slug='ordner-anlegen', title_de='Doppelt')


def test_blueprint_step_slug_is_checked_by_full_clean(blueprint: Blueprint) -> None:
    step = BlueprintStep(blueprint=blueprint, slug='ordner-anlegen', title_de='x', why_de='x')
    assert error_codes(step, '__all__') == ['unique_together']


def test_other_blueprint_may_reuse_step_slug(blueprint: Blueprint) -> None:
    other = Blueprint.objects.create(topic=blueprint.topic, slug='angular-projekt')
    assert other.steps.create(slug='ordner-anlegen', title_de='Ordner').pk


@pytest.mark.parametrize('slug', ['', 'Ordner', 'ordner_anlegen', 'ordner-', 'ordner\n', 'a/b'])
def test_blueprint_step_slug_is_checked_in_database(blueprint: Blueprint, slug: str) -> None:
    with pytest.raises(IntegrityError):
        blueprint.steps.create(slug=slug, title_de='Neu')


@pytest.mark.parametrize('slug', ['', 'Django', 'django_projekt', 'a/b'])
def test_blueprint_slug_is_checked_in_database(topic: Topic, slug: str) -> None:
    with pytest.raises(IntegrityError):
        Blueprint.objects.create(topic=topic, slug=slug)


@pytest.mark.parametrize('language', ['', 'cobol', 'Python'])
def test_blueprint_code_language_is_checked_in_database(
    venv_step: BlueprintStep, language: str
) -> None:
    with pytest.raises(IntegrityError):
        venv_step.codes.create(language=language, code_de='ls')


def test_blueprint_code_is_text_without_unix_code(blueprint: Blueprint) -> None:
    codes = BlueprintCode.objects.filter(step__slug='ordner-anlegen')
    assert [code.os_code for code in codes] == ['mkdir {{project}}', 'cd {{project}}']


def test_blueprint_unix_code_in_english_needs_german(venv_code: BlueprintCode) -> None:
    venv_code.code_unix_de = ''
    venv_code.code_unix_en = 'ls'
    assert error_codes(venv_code, 'code_unix_de') == ['required']


def test_blueprints_are_ordered_by_topic_and_position(group: Group, topic: Topic) -> None:
    git = Topic.objects.create(group=group, slug='git', name_de='Git', position=-1)
    late = Blueprint.objects.create(topic=topic, slug='spaet', position=2)
    early = Blueprint.objects.create(topic=topic, slug='frueh', position=1)
    same = Blueprint.objects.create(topic=topic, slug='gleich', position=1)
    git_blueprint = Blueprint.objects.create(topic=git, slug='repo', position=9)
    assert list(Blueprint.objects.all()) == [git_blueprint, early, same, late]


def test_blueprint_steps_are_ordered_by_position(blueprint: Blueprint) -> None:
    same = blueprint.steps.create(slug='gleich', title_de='Gleich', position=1)
    slugs = [step.slug for step in blueprint.steps.all()]
    assert slugs == ['ordner-anlegen', 'virtuelle-umgebung', same.slug]


def test_blueprint_codes_are_ordered_by_position(venv_step: BlueprintStep) -> None:
    first = venv_step.codes.get()
    second = venv_step.codes.create(language='python', code_de='pass')
    early = venv_step.codes.create(language='python', code_de='pass', position=-1)
    assert list(venv_step.codes.all()) == [early, first, second]


def test_deleting_blueprint_deletes_steps_and_codes(blueprint: Blueprint) -> None:
    blueprint.delete()
    assert not BlueprintStep.objects.exists()
    assert not BlueprintCode.objects.exists()


def test_deleting_step_deletes_only_its_codes(venv_step: BlueprintStep) -> None:
    venv_step.delete()
    assert list(BlueprintCode.objects.values_list('step__slug', flat=True)) == [
        'ordner-anlegen',
        'ordner-anlegen',
    ]


def test_topic_with_blueprints_cannot_be_deleted(blueprint: Blueprint) -> None:
    with pytest.raises(ProtectedError):
        blueprint.topic.delete()
