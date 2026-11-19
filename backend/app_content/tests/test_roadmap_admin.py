import pytest
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from app_accounts.models import User
from app_content.models import (
    Concept,
    ErrorMessage,
    RoadmapBlock,
    RoadmapCode,
    RoadmapPath,
    RoadmapPhase,
    RoadmapStep,
    RoadmapStepCondition,
    Topic,
)

pytestmark = pytest.mark.django_db

Blocks = dict[str, RoadmapBlock]

SCRIPT = '<script>alert(1)</script>'
ESCAPED = '&lt;script&gt;alert(1)&lt;/script&gt;'
ROADMAP_ADMINS = {
    'roadmapblock': 'django_block',
    'roadmapphase': 'roadmap_phase',
    'roadmapstep': 'roadmap_step',
}


@pytest.fixture
def django_block(blocks: Blocks) -> RoadmapBlock:
    return blocks['django']


def form_error_codes(response: HttpResponse, field: str) -> list[str]:
    form = response.context['adminform'].form
    return [error.code for error in form.errors.as_data()[field]]


def inline(response: HttpResponse, prefix: str) -> object:
    formsets = response.context['inline_admin_formsets']
    return next(item.formset for item in formsets if item.formset.prefix == prefix)


def inline_error_codes(response: HttpResponse, prefix: str, field: str) -> list[str]:
    form = inline(response, prefix).forms[0]
    return [error.code for error in form.errors.as_data()[field]]


def empty_inlines(*prefixes: str) -> dict:
    data = {}
    for prefix in prefixes:
        data |= {f'{prefix}-TOTAL_FORMS': 0, f'{prefix}-INITIAL_FORMS': 0}
    return data


# Blocks
def block_data(**changes: str) -> dict:
    data = {
        'slug': 'vue',
        'name_de': 'Vue',
        'name_en': '',
        'kind': 'frontend',
        'requirement': 'any',
        'topic': '',
        'available': '',
        'position': 3,
    }
    return data | changes


def add_block(admin_client: Client, **changes: str) -> HttpResponse:
    return admin_client.post(reverse('admin:app_content_roadmapblock_add'), block_data(**changes))


def test_admin_adds_block(admin_client: Client, topic: Topic) -> None:
    response = add_block(admin_client, topic=topic.pk)
    block = RoadmapBlock.objects.get(slug='vue')
    assert response.status_code == 302
    assert (block.kind, block.available, block.topic) == ('frontend', False, topic)


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Vue_JS', 'invalid'),
        ('slug', 'x' * 41, 'max_length'),
        ('name_de', '', 'required'),
        ('kind', 'cobol', 'invalid_choice'),
        ('requirement', 'cobol', 'invalid_choice'),
        ('topic', '999999', 'invalid_choice'),
    ],
)
def test_admin_rejects_invalid_block_values(
    admin_client: Client, db: None, field: str, value: str, code: str
) -> None:
    response = add_block(admin_client, **{field: value})
    assert form_error_codes(response, field) == [code]
    assert not RoadmapBlock.objects.exists()


def test_admin_rejects_duplicate_block_slug(admin_client: Client, blocks: Blocks) -> None:
    response = add_block(admin_client, slug='django')
    assert form_error_codes(response, 'slug') == ['unique']
    assert RoadmapBlock.objects.count() == 6


def test_admin_changes_block(admin_client: Client, django_block: RoadmapBlock) -> None:
    url = reverse('admin:app_content_roadmapblock_change', args=[django_block.pk])
    data = block_data(slug='django', name_de='Django REST', kind='backend', available='on')
    response = admin_client.post(url, data)
    django_block.refresh_from_db()
    assert response.status_code == 302
    assert (django_block.name_de, django_block.available) == ('Django REST', True)


def test_admin_deletes_unused_block(admin_client: Client, blocks: Blocks) -> None:
    url = reverse('admin:app_content_roadmapblock_delete', args=[blocks['react'].pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert not RoadmapBlock.objects.filter(slug='react').exists()


def test_admin_keeps_block_used_in_conditions(
    admin_client: Client, roadmap_step: RoadmapStep, django_block: RoadmapBlock
) -> None:
    url = reverse('admin:app_content_roadmapblock_delete', args=[django_block.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.context['protected']
    assert RoadmapBlock.objects.filter(pk=django_block.pk).exists()


def test_block_list_filters_and_searches(admin_client: Client, blocks: Blocks) -> None:
    url = reverse('admin:app_content_roadmapblock_changelist')
    by_kind = admin_client.get(url, {'kind__exact': 'backend'})
    by_available = admin_client.get(url, {'available__exact': '0'})
    by_search = admin_client.get(url, {'q': 'netlify'})
    assert list(by_kind.context['cl'].result_list) == [blocks['django']]
    assert list(by_available.context['cl'].result_list) == [blocks['react']]
    assert list(by_search.context['cl'].result_list) == [blocks['static-hosting']]


def test_block_list_saves_availability_and_position(admin_client: Client, blocks: Blocks) -> None:
    react = blocks['react']
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 1,
        'form-0-id': react.pk,
        'form-0-available': 'on',
        'form-0-position': 8,
        '_save': 'Save',
    }
    response = admin_client.post(reverse('admin:app_content_roadmapblock_changelist'), data)
    react.refresh_from_db()
    assert response.status_code == 302
    assert (react.available, react.position) == (True, 8)


# Phases
def phase_data(blocks: Blocks, /, **changes: str) -> dict:
    data = {
        'slug': 'frontend-anlegen',
        'title_de': 'Frontend anlegen',
        'title_en': '',
        'summary_de': 'Vom leeren Ordner bis zur ersten Seite.',
        'summary_en': '',
        'position': 3,
        'conditions-TOTAL_FORMS': 2,
        'conditions-INITIAL_FORMS': 0,
        'conditions-0-block': blocks['angular'].pk,
        'conditions-0-rule': 'requires',
        'conditions-1-block': blocks['django'].pk,
        'conditions-1-rule': 'excludes',
        'steps-TOTAL_FORMS': 2,
        'steps-INITIAL_FORMS': 0,
    }
    for index, (slug, position) in enumerate([('cli-installieren', 1), ('projekt-anlegen', 0)]):
        prefix = f'steps-{index}-'
        data |= {f'{prefix}slug': slug, f'{prefix}title_de': slug, f'{prefix}title_en': ''}
        data |= {f'{prefix}why_de': 'Weil.', f'{prefix}why_en': ''}
        data |= {f'{prefix}verification_de': 'Läuft.', f'{prefix}verification_en': ''}
        data |= {f'{prefix}position': position}
    return data | changes


def add_phase(admin_client: Client, blocks: Blocks, /, **changes: str) -> HttpResponse:
    url = reverse('admin:app_content_roadmapphase_add')
    return admin_client.post(url, phase_data(blocks, **changes))


def test_admin_adds_phase_with_conditions_and_steps(admin_client: Client, blocks: Blocks) -> None:
    response = add_phase(admin_client, blocks)
    phase = RoadmapPhase.objects.get(slug='frontend-anlegen')
    assert response.status_code == 302
    assert [step.slug for step in phase.steps.all()] == ['projekt-anlegen', 'cli-installieren']
    assert phase.applies_to({'angular'})
    assert not phase.applies_to({'angular', 'django'})


def test_admin_adds_phase_without_conditions(admin_client: Client, blocks: Blocks) -> None:
    changes = {'conditions-0-block': '', 'conditions-0-rule': ''}
    changes |= {'conditions-1-block': '', 'conditions-1-rule': ''}
    response = add_phase(admin_client, blocks, **changes)
    assert response.status_code == 302
    assert RoadmapPhase.objects.get().applies_to(set())


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Frontend_Anlegen', 'invalid'),
        ('slug', 'neu', 'reserved'),
        ('slug', 'ordnerstruktur', 'reserved'),
        ('title_de', '', 'required'),
        ('title_de', 'x' * 121, 'max_length'),
        ('summary_de', '', 'required'),
    ],
)
def test_admin_rejects_invalid_phase_values(
    admin_client: Client, blocks: Blocks, field: str, value: str, code: str
) -> None:
    response = add_phase(admin_client, blocks, **{field: value})
    assert form_error_codes(response, field) == [code]
    assert not RoadmapPhase.objects.exists()


def test_admin_rejects_duplicate_phase_slug(
    admin_client: Client, roadmap_phase: RoadmapPhase, blocks: Blocks
) -> None:
    response = add_phase(admin_client, blocks, slug='backend-anlegen')
    assert form_error_codes(response, 'slug') == ['unique']
    assert RoadmapPhase.objects.count() == 1


@pytest.mark.parametrize('rule', ['requires', 'excludes'])
def test_admin_rejects_same_block_twice_in_phase(
    admin_client: Client, blocks: Blocks, rule: str
) -> None:
    changes = {'conditions-1-block': blocks['angular'].pk, 'conditions-1-rule': rule}
    response = add_phase(admin_client, blocks, **changes)
    assert inline(response, 'conditions').non_form_errors()
    assert not RoadmapPhase.objects.exists()


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('block', '999999', 'invalid_choice'),
        ('rule', 'cobol', 'invalid_choice'),
        ('rule', '', 'required'),
    ],
)
def test_admin_checks_phase_conditions(
    admin_client: Client, blocks: Blocks, field: str, value: str, code: str
) -> None:
    response = add_phase(admin_client, blocks, **{f'conditions-0-{field}': value})
    assert inline_error_codes(response, 'conditions', field) == [code]
    assert not RoadmapPhase.objects.exists()


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Projekt_Anlegen', 'invalid'),
        ('why_de', '', 'required'),
        ('verification_de', '', 'required'),
    ],
)
def test_admin_checks_phase_steps(
    admin_client: Client, blocks: Blocks, field: str, value: str, code: str
) -> None:
    response = add_phase(admin_client, blocks, **{f'steps-0-{field}': value})
    assert inline_error_codes(response, 'steps', field) == [code]
    assert not RoadmapPhase.objects.exists()


def test_admin_rejects_duplicate_step_slugs_in_phase(admin_client: Client, blocks: Blocks) -> None:
    response = add_phase(admin_client, blocks, **{'steps-1-slug': 'cli-installieren'})
    assert inline(response, 'steps').non_form_errors()
    assert not RoadmapPhase.objects.exists()


def test_phase_change_page_links_to_steps(admin_client: Client, roadmap_step: RoadmapStep) -> None:
    url = reverse('admin:app_content_roadmapphase_change', args=[roadmap_step.phase.pk])
    response = admin_client.get(url)
    step_url = reverse('admin:app_content_roadmapstep_change', args=[roadmap_step.pk])
    assert response.status_code == 200
    assert step_url in response.content.decode()


def test_admin_deletes_phase_with_all_parts(
    admin_client: Client, roadmap_step: RoadmapStep
) -> None:
    url = reverse('admin:app_content_roadmapphase_delete', args=[roadmap_step.phase.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    for model in (RoadmapPhase, RoadmapStep, RoadmapCode, RoadmapPath):
        assert not model.objects.exists()
    assert RoadmapBlock.objects.count() == 6


def test_admin_deletes_single_condition_in_phase(
    admin_client: Client, roadmap_phase: RoadmapPhase, blocks: Blocks
) -> None:
    roadmap_phase.conditions.create(block=blocks['docker'], rule='excludes')
    data = {'slug': roadmap_phase.slug, 'conditions-INITIAL_FORMS': 2, 'steps-TOTAL_FORMS': 0}
    for index, condition in enumerate(roadmap_phase.conditions.all()):
        prefix = f'conditions-{index}-'
        data |= {f'{prefix}id': condition.pk, f'{prefix}phase': roadmap_phase.pk}
        data |= {f'{prefix}block': condition.block_id, f'{prefix}rule': condition.rule}
    data['conditions-0-DELETE'] = 'on'
    url = reverse('admin:app_content_roadmapphase_change', args=[roadmap_phase.pk])
    response = admin_client.post(url, phase_data(blocks, **data))
    assert response.status_code == 302
    assert [c.block.slug for c in roadmap_phase.conditions.all()] == ['docker']


def test_phase_list_searches(admin_client: Client, roadmap_phase: RoadmapPhase) -> None:
    RoadmapPhase.objects.create(slug='online', title_de='Online bringen', summary_de='x')
    url = reverse('admin:app_content_roadmapphase_changelist')
    response = admin_client.get(url, {'q': 'backend'})
    assert list(response.context['cl'].result_list) == [roadmap_phase]


# Steps
def step_data(phase: RoadmapPhase, /, **changes: str) -> dict:
    data = {
        'phase': phase.pk,
        'slug': 'env-anlegen',
        'title_de': 'Geheimnisse auslagern',
        'title_en': '',
        'why_de': 'Passwörter gehören nicht ins Git.',
        'why_en': '',
        'folder': 'backend/',
        'context_de': 'Umgebung aktiv',
        'context_en': '',
        'verification_de': 'git status zeigt die .env nicht.',
        'verification_en': '',
        'note_de': '',
        'note_en': '',
        'position': 7,
        'errors': [],
        'concepts': [],
        'conditions-TOTAL_FORMS': 1,
        'conditions-INITIAL_FORMS': 0,
        'conditions-0-block': phase.conditions.get().block_id,
        'conditions-0-rule': 'requires',
        'codes-TOTAL_FORMS': 2,
        'codes-INITIAL_FORMS': 0,
        'codes-0-kind': 'create',
        'codes-0-path': 'backend/.env',
        'codes-0-language': 'env',
        'codes-0-code_de': 'DEBUG=True',
        'codes-0-code_en': '',
        'codes-0-code_unix_de': '',
        'codes-0-code_unix_en': '',
        'codes-0-position': 0,
        'codes-1-kind': 'command',
        'codes-1-path': '',
        'codes-1-language': 'terminal',
        'codes-1-code_de': 'git status',
        'codes-1-code_en': '',
        'codes-1-code_unix_de': '',
        'codes-1-code_unix_en': '',
        'codes-1-position': 1,
        'paths-TOTAL_FORMS': 2,
        'paths-INITIAL_FORMS': 0,
        'paths-0-path': 'backend/.env',
        'paths-0-change': 'new',
        'paths-0-tracked': '',
        'paths-0-explanation_de': 'Echte Werte, nur auf deinem Rechner.',
        'paths-0-explanation_en': '',
        'paths-0-position': 0,
        'paths-1-path': '.gitignore',
        'paths-1-change': 'changed',
        'paths-1-tracked': 'on',
        'paths-1-explanation_de': 'Ignoriert jetzt die .env.',
        'paths-1-explanation_en': '',
        'paths-1-position': 1,
    }
    return data | changes


def add_step(admin_client: Client, phase: RoadmapPhase, /, **changes: str) -> HttpResponse:
    url = reverse('admin:app_content_roadmapstep_add')
    return admin_client.post(url, step_data(phase, **changes))


def test_admin_adds_step_with_all_parts(
    admin_client: Client,
    roadmap_phase: RoadmapPhase,
    error_message: ErrorMessage,
    concept: Concept,
) -> None:
    links = {'errors': [error_message.pk], 'concepts': [concept.pk]}
    response = add_step(admin_client, roadmap_phase, **links)
    step = roadmap_phase.steps.get(slug='env-anlegen')
    assert response.status_code == 302
    assert (step.folder, step.context_de) == ('backend/', 'Umgebung aktiv')
    assert [(c.kind, c.path) for c in step.codes.all()] == [
        ('create', 'backend/.env'),
        ('command', ''),
    ]
    assert [(p.path, p.change, p.tracked) for p in step.paths.all()] == [
        ('backend/.env', 'new', False),
        ('.gitignore', 'changed', True),
    ]
    assert (list(step.errors.all()), list(step.concepts.all())) == ([error_message], [concept])
    assert step.applies_to({'django'})


def test_admin_adds_step_without_optional_parts(
    admin_client: Client, roadmap_phase: RoadmapPhase
) -> None:
    changes = {'folder': '', 'context_de': ''} | empty_inlines('conditions', 'codes', 'paths')
    response = add_step(admin_client, roadmap_phase, **changes)
    assert response.status_code == 302
    assert roadmap_phase.steps.get(slug='env-anlegen').applies_to(set())


@pytest.mark.parametrize(
    ('field', 'value', 'code'),
    [
        ('slug', 'Env_Anlegen', 'invalid'),
        ('phase', '999999', 'invalid_choice'),
        ('title_de', '', 'required'),
        ('why_de', '', 'required'),
        ('verification_de', '', 'required'),
        ('folder', 'backend', 'invalid'),
        ('folder', '../backend/', 'invalid'),
        ('context_de', 'x' * 121, 'max_length'),
        ('errors', ['999999'], 'invalid_choice'),
        ('concepts', ['999999'], 'invalid_choice'),
    ],
)
def test_admin_rejects_invalid_step_values(
    admin_client: Client, roadmap_phase: RoadmapPhase, field: str, value: str, code: str
) -> None:
    response = add_step(admin_client, roadmap_phase, **{field: value})
    assert form_error_codes(response, field) == [code]
    assert not roadmap_phase.steps.exists()


def test_admin_rejects_duplicate_step_slug(admin_client: Client, roadmap_step: RoadmapStep) -> None:
    response = add_step(admin_client, roadmap_step.phase, slug='app-anlegen')
    assert form_error_codes(response, '__all__') == ['unique_together']
    assert roadmap_step.phase.steps.count() == 1


@pytest.mark.parametrize(
    ('changes', 'field', 'code'),
    [
        ({'codes-0-path': ''}, 'path', 'required'),
        ({'codes-0-path': 'backend/'}, 'path', 'folder'),
        ({'codes-0-path': '/backend/.env'}, 'path', 'invalid'),
        ({'codes-0-kind': 'command'}, 'path', 'not-allowed'),
        ({'codes-0-kind': ''}, 'kind', 'required'),
        ({'codes-0-language': ''}, 'language', 'required'),
        ({'codes-0-code_de': ''}, 'code_de', 'required'),
        ({'codes-0-code_unix_en': 'ls'}, 'code_unix_de', 'required'),
    ],
)
def test_admin_checks_step_codes(
    admin_client: Client, roadmap_phase: RoadmapPhase, changes: dict, field: str, code: str
) -> None:
    response = add_step(admin_client, roadmap_phase, **changes)
    assert inline_error_codes(response, 'codes', field) == [code]
    assert not roadmap_phase.steps.exists()


@pytest.mark.parametrize(
    ('changes', 'field', 'code'),
    [
        ({'paths-0-path': ''}, 'path', 'required'),
        ({'paths-0-path': 'backend\\.env'}, 'path', 'invalid'),
        ({'paths-0-change': ''}, 'change', 'required'),
        ({'paths-0-change': 'cobol'}, 'change', 'invalid_choice'),
        ({'paths-0-explanation_de': ''}, 'explanation_de', 'required'),
    ],
)
def test_admin_checks_step_paths(
    admin_client: Client, roadmap_phase: RoadmapPhase, changes: dict, field: str, code: str
) -> None:
    response = add_step(admin_client, roadmap_phase, **changes)
    assert inline_error_codes(response, 'paths', field) == [code]
    assert not roadmap_phase.steps.exists()


def test_admin_rejects_same_path_twice_in_step(
    admin_client: Client, roadmap_phase: RoadmapPhase
) -> None:
    response = add_step(admin_client, roadmap_phase, **{'paths-1-path': 'backend/.env'})
    assert inline(response, 'paths').non_form_errors()
    assert not roadmap_phase.steps.exists()


def test_admin_rejects_same_block_twice_in_step(
    admin_client: Client, roadmap_phase: RoadmapPhase, blocks: Blocks
) -> None:
    changes = {
        'conditions-TOTAL_FORMS': 2,
        'conditions-1-block': blocks['django'].pk,
        'conditions-1-rule': 'excludes',
    }
    response = add_step(admin_client, roadmap_phase, **changes)
    assert inline(response, 'conditions').non_form_errors()
    assert not roadmap_phase.steps.exists()


def existing_step_data(step: RoadmapStep) -> dict:
    data = {'slug': step.slug, 'title_de': step.title_de, 'folder': step.folder}
    data |= {'conditions-INITIAL_FORMS': 1, 'conditions-TOTAL_FORMS': 1}
    condition = step.conditions.get()
    data |= {'conditions-0-id': condition.pk, 'conditions-0-step': step.pk}
    data |= {'conditions-0-block': condition.block_id, 'conditions-0-rule': condition.rule}
    data |= {'codes-INITIAL_FORMS': 2, 'codes-TOTAL_FORMS': 2}
    for index, code in enumerate(step.codes.all()):
        prefix = f'codes-{index}-'
        data |= {f'{prefix}id': code.pk, f'{prefix}step': step.pk, f'{prefix}kind': code.kind}
        data |= {f'{prefix}path': code.path, f'{prefix}language': code.language}
        data |= {f'{prefix}code_de': code.code_de, f'{prefix}position': code.position}
        data |= {f'{prefix}code_unix_de': code.code_unix_de or ''}
    data |= {'paths-INITIAL_FORMS': 2, 'paths-TOTAL_FORMS': 2}
    for index, path in enumerate(step.paths.all()):
        prefix = f'paths-{index}-'
        data |= {f'{prefix}id': path.pk, f'{prefix}step': step.pk, f'{prefix}path': path.path}
        data |= {f'{prefix}change': path.change, f'{prefix}tracked': 'on'}
        data |= {f'{prefix}explanation_de': path.explanation_de}
        data |= {f'{prefix}position': path.position}
    return step_data(step.phase, **data)


def post_step(admin_client: Client, step: RoadmapStep, data: dict) -> HttpResponse:
    url = reverse('admin:app_content_roadmapstep_change', args=[step.pk])
    return admin_client.post(url, data)


def test_admin_changes_step(admin_client: Client, roadmap_step: RoadmapStep) -> None:
    data = existing_step_data(roadmap_step) | {'title_de': 'App anlegen', 'folder': ''}
    response = post_step(admin_client, roadmap_step, data)
    roadmap_step.refresh_from_db()
    assert response.status_code == 302
    assert (roadmap_step.title_de, roadmap_step.folder) == ('App anlegen', '')
    assert (roadmap_step.codes.count(), roadmap_step.paths.count()) == (2, 2)


@pytest.mark.parametrize(
    ('prefix', 'model', 'left'),
    [
        ('codes', RoadmapCode, 1),
        ('paths', RoadmapPath, 1),
        ('conditions', RoadmapStepCondition, 0),
    ],
)
def test_admin_deletes_single_step_part(
    admin_client: Client, roadmap_step: RoadmapStep, prefix: str, model: type, left: int
) -> None:
    data = existing_step_data(roadmap_step) | {f'{prefix}-0-DELETE': 'on'}
    response = post_step(admin_client, roadmap_step, data)
    assert response.status_code == 302
    assert model.objects.filter(step=roadmap_step).count() == left


def test_admin_deletes_step_but_keeps_phase(
    admin_client: Client, roadmap_step: RoadmapStep
) -> None:
    url = reverse('admin:app_content_roadmapstep_delete', args=[roadmap_step.pk])
    response = admin_client.post(url, {'post': 'yes'})
    assert response.status_code == 302
    assert RoadmapPhase.objects.filter(pk=roadmap_step.phase_id).exists()
    assert not RoadmapCode.objects.exists()


def test_admin_rejects_moving_step_to_phase_with_same_slug(
    admin_client: Client, roadmap_step: RoadmapStep
) -> None:
    other = RoadmapPhase.objects.create(slug='verbinden', title_de='Verbinden', summary_de='x')
    other.steps.create(slug='app-anlegen', title_de='x', why_de='x', verification_de='x')
    data = existing_step_data(roadmap_step) | {'phase': other.pk}
    response = post_step(admin_client, roadmap_step, data)
    roadmap_step.refresh_from_db()
    assert form_error_codes(response, '__all__') == ['unique_together']
    assert roadmap_step.phase.slug == 'backend-anlegen'


def test_step_list_shows_phase_filters_and_searches(
    admin_client: Client, roadmap_step: RoadmapStep
) -> None:
    other = RoadmapPhase.objects.create(slug='verbinden', title_de='Verbinden', summary_de='x')
    other.steps.create(slug='proxy', title_de='Proxy anlegen', why_de='x', verification_de='x')
    url = reverse('admin:app_content_roadmapstep_changelist')
    by_phase = admin_client.get(url, {'phase__id__exact': roadmap_step.phase_id})
    by_search = admin_client.get(url, {'q': 'django-app'})
    assert 'Backend anlegen' in by_phase.content.decode()
    assert list(by_phase.context['cl'].result_list) == [roadmap_step]
    assert list(by_search.context['cl'].result_list) == [roadmap_step]


def test_step_change_page_loads_with_autocomplete(
    admin_client: Client, roadmap_step: RoadmapStep
) -> None:
    url = reverse('admin:app_content_roadmapstep_change', args=[roadmap_step.pk])
    content = admin_client.get(url).content.decode()
    assert 'admin-autocomplete' in content
    assert 'backend/app_recipes/' in content


# Lists and permissions
@pytest.mark.parametrize(('model', 'fixture'), ROADMAP_ADMINS.items())
def test_roadmap_lists_save_position(
    admin_client: Client, request: pytest.FixtureRequest, model: str, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 1,
        'form-0-id': obj.pk,
        'form-0-position': 8,
        '_save': 'Save',
    }
    if model == 'roadmapblock':
        data['form-0-available'] = 'on'
    response = admin_client.post(reverse(f'admin:app_content_{model}_changelist'), data)
    obj.refresh_from_db()
    assert response.status_code == 302
    assert obj.position == 8


@pytest.mark.parametrize(('model', 'fixture'), ROADMAP_ADMINS.items())
def test_staff_with_view_permission_cannot_change_roadmap(
    staff_client: Client,
    staff_user: User,
    request: pytest.FixtureRequest,
    model: str,
    fixture: str,
) -> None:
    obj = request.getfixturevalue(fixture)
    staff_user.user_permissions.add(Permission.objects.get(codename=f'view_{model}'))
    url = reverse(f'admin:app_content_{model}_change', args=[obj.pk])
    assert staff_client.get(url).status_code == 200
    assert staff_client.post(url, {'slug': 'neu-slug'}).status_code == 403
    assert type(obj).objects.get(pk=obj.pk).slug == obj.slug


@pytest.mark.parametrize(('model', 'fixture'), ROADMAP_ADMINS.items())
def test_roadmap_lists_escape_html(
    admin_client: Client, request: pytest.FixtureRequest, model: str, fixture: str
) -> None:
    obj = request.getfixturevalue(fixture)
    field = 'name_de' if model == 'roadmapblock' else 'title_de'
    type(obj).objects.filter(pk=obj.pk).update(**{field: SCRIPT})
    content = admin_client.get(reverse(f'admin:app_content_{model}_changelist')).content.decode()
    assert SCRIPT not in content
    assert ESCAPED in content


def test_step_change_page_escapes_html_in_code_and_paths(
    admin_client: Client, roadmap_step: RoadmapStep
) -> None:
    roadmap_step.codes.update(code_de=SCRIPT)
    roadmap_step.paths.update(explanation_de=SCRIPT)
    url = reverse('admin:app_content_roadmapstep_change', args=[roadmap_step.pk])
    content = admin_client.get(url).content.decode()
    assert SCRIPT not in content
    assert ESCAPED in content
