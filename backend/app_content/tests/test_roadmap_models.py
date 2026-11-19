import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Model, ProtectedError
from django.utils import translation

from app_content.models import (
    Concept,
    ErrorMessage,
    RoadmapBlock,
    RoadmapCode,
    RoadmapPath,
    RoadmapPhase,
    RoadmapPhaseCondition,
    RoadmapStep,
    RoadmapStepCondition,
    Topic,
)

pytestmark = pytest.mark.django_db

Blocks = dict[str, RoadmapBlock]

VALID_PATHS = [
    'backend/',
    '.env',
    '.gitignore',
    'backend/.venv/',
    'docker-compose.yml',
    'frontend/src/app/app.config.ts',
    'backend/app_recipes/migrations/__init__.py',
    'frontend/src/environments/environment.development.ts',
    'nginx/server/rezeptbuch.conf',
]
INVALID_PATHS = [
    '/backend/',
    './backend/',
    '../backend/',
    'backend/../core/',
    'backend//core/',
    'backend\\core\\',
    'C:/backend/',
    'mein ordner/',
    'backend/core/\n',
    '{{project}}/backend/',
]


def all_error_codes(obj: Model) -> dict[str, list[str]]:
    with pytest.raises(ValidationError) as error:
        obj.full_clean()
    return {field: [item.code for item in items] for field, items in error.value.error_dict.items()}


def error_codes(obj: Model, field: str) -> list[str]:
    return all_error_codes(obj)[field]


@pytest.fixture
def command(roadmap_step: RoadmapStep) -> RoadmapCode:
    return roadmap_step.codes.get(kind='command')


@pytest.fixture
def new_path(roadmap_step: RoadmapStep) -> RoadmapPath:
    return roadmap_step.paths.get(change='new')


# Names and translations
def test_roadmap_parts_str(
    blocks: Blocks, roadmap_step: RoadmapStep, command: RoadmapCode, new_path: RoadmapPath
) -> None:
    phase = roadmap_step.phase
    condition = phase.conditions.get()
    assert [str(blocks['django']), str(phase), str(roadmap_step)] == [
        'Django',
        'Backend anlegen',
        'Django-App anlegen',
    ]
    assert [str(condition), str(command), str(new_path)] == [
        'Django: muss gewählt sein',
        'Terminal',
        'backend/app_recipes/',
    ]


def test_roadmap_texts_follow_active_language(
    roadmap_step: RoadmapStep, command: RoadmapCode, new_path: RoadmapPath
) -> None:
    with translation.override('en'):
        assert [roadmap_step.phase.title, roadmap_step.phase.summary] == [
            'Set up the backend',
            'From an empty folder to a running server.',
        ]
        assert [roadmap_step.title, roadmap_step.why, roadmap_step.context] == [
            'Create a Django app',
            'Each task gets its own app.',
            'Environment active',
        ]
        assert roadmap_step.verification == 'app_recipes/ sits next to core/.'
        assert new_path.explanation == 'The app for everything about recipes.'


def test_roadmap_texts_fall_back_to_german(blocks: Blocks, roadmap_step: RoadmapStep) -> None:
    changed = roadmap_step.paths.get(change='changed')
    with translation.override('en'):
        assert blocks['django'].name == 'Django'
        assert roadmap_step.note == 'Das Präfix app_ macht eigene Apps erkennbar.'
        assert changed.explanation == 'Kennt jetzt die neue App.'


def test_roadmap_parts_are_valid(blocks: Blocks, roadmap_step: RoadmapStep) -> None:
    parts = [
        *blocks.values(),
        roadmap_step.phase,
        *roadmap_step.phase.conditions.all(),
        roadmap_step,
        *roadmap_step.conditions.all(),
        *roadmap_step.codes.all(),
        *roadmap_step.paths.all(),
    ]
    for part in parts:
        part.full_clean()


# Required fields
def test_block_requires_slug_name_and_kind(db: None) -> None:
    assert set(all_error_codes(RoadmapBlock(requirement='any'))) == {'slug', 'name', 'kind'}


def test_block_defaults_to_available_without_requirement(db: None) -> None:
    block = RoadmapBlock(slug='vue', name_de='Vue', kind='frontend')
    block.full_clean()
    assert (block.requirement, block.available, block.topic) == ('any', True, None)


def test_phase_requires_slug_title_and_summary(db: None) -> None:
    assert set(all_error_codes(RoadmapPhase())) == {'slug', 'title', 'summary'}


def test_step_requires_slug_title_why_and_check(roadmap_phase: RoadmapPhase) -> None:
    step = RoadmapStep(phase=roadmap_phase)
    assert set(all_error_codes(step)) == {'slug', 'title', 'why', 'verification'}


def test_step_without_folder_context_and_note_is_valid(roadmap_step: RoadmapStep) -> None:
    roadmap_step.folder = ''
    roadmap_step.context_de = ''
    roadmap_step.note_de = ''
    roadmap_step.full_clean()


def test_code_requires_kind_language_and_code(roadmap_step: RoadmapStep) -> None:
    code = RoadmapCode(step=roadmap_step)
    assert set(all_error_codes(code)) == {'kind', 'language', 'code'}


def test_path_requires_path_change_and_explanation(roadmap_step: RoadmapStep) -> None:
    path = RoadmapPath(step=roadmap_step)
    assert set(all_error_codes(path)) == {'path', 'change', 'explanation'}


def test_path_is_tracked_by_default(roadmap_step: RoadmapStep) -> None:
    assert RoadmapPath(step=roadmap_step).tracked is True


def test_condition_requires_block_and_rule(roadmap_phase: RoadmapPhase) -> None:
    condition = RoadmapPhaseCondition(phase=roadmap_phase)
    assert set(all_error_codes(condition)) == {'block', 'rule'}


# Limits
@pytest.mark.parametrize(
    ('fixture', 'field', 'limit'),
    [
        ('roadmap_phase', 'slug', 80),
        ('roadmap_phase', 'title_de', 120),
        ('roadmap_step', 'slug', 80),
        ('roadmap_step', 'title_de', 120),
        ('roadmap_step', 'context_de', 120),
    ],
)
def test_roadmap_text_is_limited(
    request: pytest.FixtureRequest, fixture: str, field: str, limit: int
) -> None:
    obj = request.getfixturevalue(fixture)
    setattr(obj, field, 'x' * (limit + 1))
    assert error_codes(obj, field) == ['max_length']


@pytest.mark.parametrize(('field', 'limit'), [('slug', 40), ('name_de', 60)])
def test_block_text_is_limited(blocks: Blocks, field: str, limit: int) -> None:
    block = blocks['django']
    setattr(block, field, 'x' * (limit + 1))
    assert error_codes(block, field) == ['max_length']


def test_path_and_folder_are_limited(roadmap_step: RoadmapStep, new_path: RoadmapPath) -> None:
    long_folder = 'a/' * 101
    roadmap_step.folder = long_folder
    new_path.path = long_folder
    assert error_codes(roadmap_step, 'folder') == ['max_length']
    assert error_codes(new_path, 'path') == ['max_length']


# Slugs
@pytest.mark.parametrize('slug', ['Django', 'django_rest', 'django-', 'django rest', '-django'])
def test_roadmap_slugs_are_checked(blocks: Blocks, roadmap_step: RoadmapStep, slug: str) -> None:
    for obj in (blocks['django'], roadmap_step.phase, roadmap_step):
        obj.slug = slug
        assert 'invalid' in error_codes(obj, 'slug')


@pytest.mark.parametrize('slug', ['', 'Django', 'django_rest', 'django-', 'a/b'])
def test_block_slug_is_checked_in_database(db: None, slug: str) -> None:
    with pytest.raises(IntegrityError):
        RoadmapBlock.objects.create(slug=slug, name_de='x', kind='extra')


@pytest.mark.parametrize('slug', ['', 'Backend', 'backend_anlegen', 'backend-', 'a/b'])
def test_phase_slug_is_checked_in_database(db: None, slug: str) -> None:
    with pytest.raises(IntegrityError):
        RoadmapPhase.objects.create(slug=slug, title_de='x', summary_de='x')


@pytest.mark.parametrize('slug', ['', 'App', 'app_anlegen', 'app-', 'a/b'])
def test_step_slug_is_checked_in_database(roadmap_phase: RoadmapPhase, slug: str) -> None:
    with pytest.raises(IntegrityError):
        roadmap_phase.steps.create(slug=slug, title_de='x', why_de='x', verification_de='x')


@pytest.mark.parametrize('slug', ['neu', 'ordnerstruktur'])
def test_reserved_phase_slug_is_rejected(roadmap_phase: RoadmapPhase, slug: str) -> None:
    roadmap_phase.slug = slug
    assert error_codes(roadmap_phase, 'slug') == ['reserved']


@pytest.mark.parametrize('slug', ['neu', 'ordnerstruktur'])
def test_reserved_phase_slug_is_rejected_in_database(db: None, slug: str) -> None:
    with pytest.raises(IntegrityError):
        RoadmapPhase.objects.create(slug=slug, title_de='x', summary_de='x')


@pytest.mark.parametrize('slug', ['neues-projekt', 'ordnerstruktur-anlegen'])
def test_phase_slug_may_contain_reserved_word(roadmap_phase: RoadmapPhase, slug: str) -> None:
    roadmap_phase.slug = slug
    roadmap_phase.full_clean()


@pytest.mark.parametrize('slug', ['neu', 'ordnerstruktur'])
def test_step_may_use_reserved_phase_slug(roadmap_phase: RoadmapPhase, slug: str) -> None:
    assert roadmap_phase.steps.create(slug=slug, title_de='x', why_de='x', verification_de='x').pk


# Uniqueness
def test_block_slug_is_unique(blocks: Blocks) -> None:
    with pytest.raises(IntegrityError):
        RoadmapBlock.objects.create(slug='django', name_de='Django', kind='backend')


def test_phase_slug_is_unique(roadmap_phase: RoadmapPhase) -> None:
    with pytest.raises(IntegrityError):
        RoadmapPhase.objects.create(slug='backend-anlegen', title_de='x', summary_de='x')


def test_step_slug_is_unique_per_phase(roadmap_step: RoadmapStep) -> None:
    with pytest.raises(IntegrityError):
        roadmap_step.phase.steps.create(
            slug='app-anlegen', title_de='x', why_de='x', verification_de='x'
        )


def test_step_slug_is_checked_by_full_clean(roadmap_step: RoadmapStep) -> None:
    step = RoadmapStep(
        phase=roadmap_step.phase, slug='app-anlegen', title_de='x', why_de='x', verification_de='x'
    )
    assert error_codes(step, '__all__') == ['unique_together']


def test_other_phase_may_reuse_step_slug(roadmap_step: RoadmapStep) -> None:
    other = RoadmapPhase.objects.create(slug='frontend-anlegen', title_de='x', summary_de='x')
    assert other.steps.create(slug='app-anlegen', title_de='x', why_de='x', verification_de='x').pk


def test_path_is_unique_per_step(roadmap_step: RoadmapStep) -> None:
    with pytest.raises(IntegrityError):
        roadmap_step.paths.create(path='backend/app_recipes/', change='changed', explanation_de='x')


def test_path_is_checked_by_full_clean(roadmap_step: RoadmapStep) -> None:
    path = RoadmapPath(
        step=roadmap_step, path='backend/app_recipes/', change='changed', explanation_de='x'
    )
    assert error_codes(path, '__all__') == ['unique_together']


def test_other_step_may_reuse_path(roadmap_step: RoadmapStep) -> None:
    other = roadmap_step.phase.steps.create(
        slug='tests', title_de='x', why_de='x', verification_de='x'
    )
    assert other.paths.create(path='backend/app_recipes/', change='changed').pk


@pytest.mark.parametrize('rule', ['requires', 'excludes'])
def test_block_is_used_once_per_phase(
    roadmap_phase: RoadmapPhase, blocks: Blocks, rule: str
) -> None:
    with pytest.raises(IntegrityError):
        roadmap_phase.conditions.create(block=blocks['django'], rule=rule)


@pytest.mark.parametrize('rule', ['requires', 'excludes'])
def test_block_is_used_once_per_step(roadmap_step: RoadmapStep, blocks: Blocks, rule: str) -> None:
    with pytest.raises(IntegrityError):
        roadmap_step.conditions.create(block=blocks['docker'], rule=rule)


def test_phase_condition_is_checked_by_full_clean(
    roadmap_phase: RoadmapPhase, blocks: Blocks
) -> None:
    condition = RoadmapPhaseCondition(phase=roadmap_phase, block=blocks['django'], rule='excludes')
    assert error_codes(condition, '__all__') == ['unique_together']


def test_other_phase_and_step_may_use_same_block(roadmap_step: RoadmapStep, blocks: Blocks) -> None:
    other = RoadmapPhase.objects.create(slug='verbinden', title_de='x', summary_de='x')
    assert other.conditions.create(block=blocks['django'], rule='requires').pk
    assert roadmap_step.conditions.create(block=blocks['django'], rule='requires').pk


# Choices
@pytest.mark.parametrize(
    ('fixture', 'field'),
    [
        ('django_block', 'kind'),
        ('django_block', 'requirement'),
        ('command', 'kind'),
        ('command', 'language'),
        ('new_path', 'change'),
        ('phase_condition', 'rule'),
    ],
)
def test_unknown_choice_is_rejected(
    request: pytest.FixtureRequest, fixture: str, field: str
) -> None:
    obj = request.getfixturevalue(fixture)
    setattr(obj, field, 'cobol')
    assert error_codes(obj, field) == ['invalid_choice']


@pytest.fixture
def django_block(blocks: Blocks) -> RoadmapBlock:
    return blocks['django']


@pytest.fixture
def phase_condition(roadmap_phase: RoadmapPhase) -> RoadmapPhaseCondition:
    return roadmap_phase.conditions.get()


@pytest.mark.parametrize('value', ['', 'cobol', 'Frontend'])
def test_block_kind_is_checked_in_database(db: None, value: str) -> None:
    with pytest.raises(IntegrityError):
        RoadmapBlock.objects.create(slug='vue', name_de='Vue', kind=value)


@pytest.mark.parametrize('value', ['', 'cobol', 'Backend'])
def test_block_requirement_is_checked_in_database(db: None, value: str) -> None:
    with pytest.raises(IntegrityError):
        RoadmapBlock.objects.create(slug='vue', name_de='Vue', kind='frontend', requirement=value)


@pytest.mark.parametrize('value', ['', 'cobol', 'Requires'])
def test_condition_rule_is_checked_in_database(
    roadmap_phase: RoadmapPhase, blocks: Blocks, value: str
) -> None:
    with pytest.raises(IntegrityError):
        roadmap_phase.conditions.create(block=blocks['docker'], rule=value)


@pytest.mark.parametrize(
    ('field', 'value'),
    [('kind', ''), ('kind', 'Command'), ('language', ''), ('language', 'cobol')],
)
def test_code_choices_are_checked_in_database(
    roadmap_step: RoadmapStep, field: str, value: str
) -> None:
    data = {'kind': 'command', 'language': 'terminal', 'code_de': 'ls'} | {field: value}
    with pytest.raises(IntegrityError):
        roadmap_step.codes.create(**data)


@pytest.mark.parametrize('value', ['', 'cobol', 'New'])
def test_path_change_is_checked_in_database(roadmap_step: RoadmapStep, value: str) -> None:
    with pytest.raises(IntegrityError):
        roadmap_step.paths.create(path='README.md', change=value)


@pytest.mark.parametrize('language', ['json', 'yaml', 'dockerfile', 'nginx', 'env'])
def test_code_accepts_config_languages(command: RoadmapCode, language: str) -> None:
    command.language = language
    command.full_clean()


# Paths
@pytest.mark.parametrize('value', VALID_PATHS)
def test_valid_paths_are_accepted(new_path: RoadmapPath, value: str) -> None:
    new_path.path = value
    new_path.full_clean()


@pytest.mark.parametrize('value', INVALID_PATHS)
def test_invalid_paths_are_rejected(new_path: RoadmapPath, value: str) -> None:
    new_path.path = value
    assert error_codes(new_path, 'path') == ['invalid']


@pytest.mark.parametrize('value', INVALID_PATHS)
def test_invalid_paths_are_rejected_in_database(roadmap_step: RoadmapStep, value: str) -> None:
    with pytest.raises(IntegrityError):
        roadmap_step.paths.create(path=value, change='new')


@pytest.mark.parametrize('value', ['backend/', 'frontend/src/app/', '.github/workflows/'])
def test_folder_accepts_folders(roadmap_step: RoadmapStep, value: str) -> None:
    roadmap_step.folder = value
    roadmap_step.full_clean()


@pytest.mark.parametrize('value', [*INVALID_PATHS, 'backend', 'docker-compose.yml'])
def test_folder_rejects_files_and_invalid_paths(roadmap_step: RoadmapStep, value: str) -> None:
    roadmap_step.folder = value
    assert error_codes(roadmap_step, 'folder') == ['invalid']


@pytest.mark.parametrize('value', [*INVALID_PATHS, 'backend'])
def test_folder_is_checked_in_database(roadmap_phase: RoadmapPhase, value: str) -> None:
    with pytest.raises(IntegrityError):
        roadmap_phase.steps.create(
            slug='x', title_de='x', why_de='x', verification_de='x', folder=value
        )


@pytest.mark.parametrize('value', INVALID_PATHS)
def test_code_path_is_checked(roadmap_step: RoadmapStep, value: str) -> None:
    code = roadmap_step.codes.get(kind='change')
    code.path = value
    assert error_codes(code, 'path') == ['invalid']


@pytest.mark.parametrize('value', ['backend/core/', 'frontend/src/'])
def test_file_code_rejects_folder(roadmap_step: RoadmapStep, value: str) -> None:
    code = roadmap_step.codes.get(kind='change')
    code.path = value
    assert error_codes(code, 'path') == ['folder']


# Code kinds
@pytest.mark.parametrize('kind', ['create', 'change'])
def test_file_code_requires_path(command: RoadmapCode, kind: str) -> None:
    command.kind = kind
    assert error_codes(command, 'path') == ['required']


def test_command_rejects_path(command: RoadmapCode) -> None:
    command.path = 'backend/manage.py'
    assert error_codes(command, 'path') == ['not-allowed']


@pytest.mark.parametrize(
    ('kind', 'path'),
    [('create', ''), ('change', ''), ('command', 'backend/manage.py'), ('create', 'backend/')],
)
def test_code_path_rule_is_checked_in_database(
    roadmap_step: RoadmapStep, kind: str, path: str
) -> None:
    with pytest.raises(IntegrityError):
        roadmap_step.codes.create(kind=kind, path=path, language='python', code_de='pass')


def test_create_code_with_path_is_valid(roadmap_step: RoadmapStep) -> None:
    code = roadmap_step.codes.create(
        kind='create', path='backend/.env', language='env', code_de='DEBUG=True'
    )
    code.full_clean()


# Unix code
def test_code_is_split_by_operating_system(command: RoadmapCode) -> None:
    assert command.os_code == {
        'win': 'python manage.py startapp app_recipes',
        'unix': 'python3 manage.py startapp app_recipes',
    }


def test_code_without_unix_code_is_text(roadmap_step: RoadmapStep) -> None:
    assert roadmap_step.codes.get(kind='change').os_code == "INSTALLED_APPS += ['app_recipes']"


def test_unix_code_in_english_needs_german(command: RoadmapCode) -> None:
    command.code_unix_de = ''
    command.code_unix_en = 'ls'
    assert error_codes(command, 'code_unix_de') == ['required']


# Conditions
@pytest.mark.parametrize(
    ('chosen', 'applies'),
    [
        ({'django'}, True),
        ({'django', 'angular', 'postgresql'}, True),
        ({'angular'}, True),
        (set(), True),
        ({'django', 'docker'}, False),
        ({'docker'}, False),
    ],
)
def test_step_applies_by_its_conditions(
    roadmap_step: RoadmapStep, chosen: set[str], applies: bool
) -> None:
    assert roadmap_step.applies_to(chosen) is applies


@pytest.mark.parametrize(
    ('chosen', 'applies'),
    [({'django'}, True), ({'django', 'docker'}, True), ({'angular'}, False)],
)
def test_phase_applies_by_its_conditions(
    roadmap_phase: RoadmapPhase, chosen: set[str], applies: bool
) -> None:
    assert roadmap_phase.applies_to(chosen) is applies


def test_item_without_conditions_applies_to_every_plan(roadmap_phase: RoadmapPhase) -> None:
    roadmap_phase.conditions.all().delete()
    assert roadmap_phase.applies_to(set())
    assert roadmap_phase.applies_to({'react', 'django', 'docker'})


def test_step_applies_with_requires_and_excludes(roadmap_step: RoadmapStep, blocks: Blocks) -> None:
    roadmap_step.conditions.create(block=blocks['angular'], rule='requires')
    assert roadmap_step.applies_to({'angular'})
    assert not roadmap_step.applies_to({'angular', 'docker'})
    assert not roadmap_step.applies_to({'django'})


# Order
def test_blocks_are_ordered_by_position(blocks: Blocks) -> None:
    same = RoadmapBlock.objects.create(slug='vue', name_de='Vue', kind='frontend', position=0)
    early = RoadmapBlock.objects.create(slug='git', name_de='Git', kind='extra', position=-1)
    slugs = [block.slug for block in RoadmapBlock.objects.all()]
    assert slugs[:3] == [early.slug, 'angular', same.slug]


def test_phases_are_ordered_by_position(roadmap_phase: RoadmapPhase) -> None:
    same = RoadmapPhase.objects.create(slug='zwei', title_de='x', summary_de='x', position=2)
    early = RoadmapPhase.objects.create(slug='eins', title_de='x', summary_de='x', position=1)
    assert list(RoadmapPhase.objects.all()) == [early, roadmap_phase, same]


def test_steps_codes_and_paths_are_ordered_by_position(roadmap_step: RoadmapStep) -> None:
    phase = roadmap_step.phase
    same = phase.steps.create(
        slug='gleich', title_de='x', why_de='x', verification_de='x', position=9
    )
    early = phase.steps.create(
        slug='frueh', title_de='x', why_de='x', verification_de='x', position=1
    )
    late_code = roadmap_step.codes.create(kind='command', language='terminal', code_de='ls')
    early_path = roadmap_step.paths.create(path='README.md', change='new', position=-1)
    assert list(phase.steps.all()) == [early, roadmap_step, same]
    assert [code.kind for code in roadmap_step.codes.all()] == ['command', 'command', 'change']
    assert roadmap_step.codes.first() == late_code
    assert roadmap_step.paths.first() == early_path


# Links
def test_step_links_errors_and_concepts(
    roadmap_step: RoadmapStep, error_message: ErrorMessage, concept: Concept
) -> None:
    assert list(roadmap_step.errors.all()) == [error_message]
    assert list(roadmap_step.concepts.all()) == [concept]


def test_deleting_linked_error_and_concept_keeps_step(
    roadmap_step: RoadmapStep, error_message: ErrorMessage, concept: Concept
) -> None:
    error_message.delete()
    concept.delete()
    assert RoadmapStep.objects.get(pk=roadmap_step.pk).errors.count() == 0
    assert not roadmap_step.concepts.exists()


# Delete
def test_deleting_phase_deletes_all_its_parts(roadmap_step: RoadmapStep) -> None:
    roadmap_step.phase.delete()
    for model in (RoadmapStep, RoadmapCode, RoadmapPath):
        assert not model.objects.exists()
    assert not RoadmapPhaseCondition.objects.exists()
    assert not RoadmapStepCondition.objects.exists()
    assert RoadmapBlock.objects.count() == 6


def test_deleting_step_deletes_only_its_parts(roadmap_step: RoadmapStep) -> None:
    other = roadmap_step.phase.steps.create(
        slug='tests', title_de='x', why_de='x', verification_de='x'
    )
    other.paths.create(path='backend/app_recipes/tests/', change='new')
    roadmap_step.delete()
    assert list(RoadmapPath.objects.values_list('step__slug', flat=True)) == ['tests']
    assert not RoadmapCode.objects.exists()
    assert not RoadmapStepCondition.objects.exists()
    assert RoadmapPhaseCondition.objects.count() == 1


@pytest.mark.parametrize('block', ['django', 'docker'])
def test_block_used_in_condition_cannot_be_deleted(
    roadmap_step: RoadmapStep, blocks: Blocks, block: str
) -> None:
    with pytest.raises(ProtectedError):
        blocks[block].delete()


def test_unused_block_can_be_deleted(roadmap_step: RoadmapStep, blocks: Blocks) -> None:
    blocks['react'].delete()
    assert not RoadmapBlock.objects.filter(slug='react').exists()


def test_topic_of_block_cannot_be_deleted(blocks: Blocks, topic: Topic) -> None:
    blocks['django'].topic = topic
    blocks['django'].save()
    with pytest.raises(ProtectedError):
        blocks['django'].topic.delete()
