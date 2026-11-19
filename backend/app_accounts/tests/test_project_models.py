from datetime import UTC, datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Model, ProtectedError

from app_accounts.models import Project, ProjectBlock, ProjectNote, ProjectStep, User
from app_content.models import RoadmapBlock, RoadmapPhase, RoadmapStep

pytestmark = pytest.mark.django_db

Blocks = dict[str, RoadmapBlock]
PASSWORD = 'Kaffee-Tasse-2026!'


def error_codes(obj: Model, field: str) -> list[str]:
    with pytest.raises(ValidationError) as error:
        obj.full_clean()
    return [item.code for item in error.value.error_dict[field]]


@pytest.fixture
def other_user(db: None) -> User:
    return User.objects.create_user('grace@example.com', PASSWORD)


@pytest.fixture
def second_step(roadmap_step: RoadmapStep) -> RoadmapStep:
    return roadmap_step.phase.steps.create(
        slug='migrieren', title_de='Migrieren', why_de='x', verification_de='x', position=10
    )


# Project
def test_project_belongs_to_user_with_blocks(project: Project, user: User) -> None:
    assert list(user.projects.all()) == [project]
    assert project.block_slugs() == {'angular', 'django', 'docker'}
    assert project.created_at is not None
    assert project.updated_at is not None


def test_project_str_names_user(project: Project) -> None:
    assert str(project) == 'ada@example.com'


def test_user_has_only_one_project(project: Project, user: User) -> None:
    with pytest.raises(IntegrityError):
        Project.objects.create(user=user)


def test_second_project_fails_validation(project: Project, user: User) -> None:
    assert error_codes(Project(user=user), 'user') == ['unique']


def test_other_user_may_have_a_project(project: Project, other_user: User) -> None:
    assert Project.objects.create(user=other_user).pk


def test_project_requires_user(db: None) -> None:
    assert error_codes(Project(), 'user') == ['null']


def test_same_block_twice_is_rejected(project: Project, blocks: Blocks) -> None:
    with pytest.raises(IntegrityError):
        ProjectBlock.objects.create(project=project, block=blocks['django'])


def test_project_block_str_names_project_and_block(project: Project) -> None:
    assert str(ProjectBlock.objects.get(block__slug='django')) == 'ada@example.com: Django'


def test_projects_are_ordered_oldest_first(project: Project, other_user: User) -> None:
    newer = Project.objects.create(user=other_user)
    Project.objects.filter(pk=project.pk).update(created_at=datetime(2026, 1, 1, tzinfo=UTC))
    assert list(Project.objects.all()) == [project, newer]


# Choosing blocks
@pytest.mark.parametrize(
    'chosen',
    [
        ['angular'],
        ['django'],
        ['angular', 'django'],
        ['angular', 'django', 'docker', 'postgresql'],
        ['django', 'postgresql'],
        ['angular', 'static-hosting'],
        ['angular', 'docker'],
    ],
)
def test_possible_choice_is_set(project: Project, blocks: Blocks, chosen: list[str]) -> None:
    project.set_blocks([blocks[slug] for slug in chosen])
    assert project.block_slugs() == set(chosen)


def test_impossible_choice_keeps_old_blocks(project: Project, blocks: Blocks) -> None:
    with pytest.raises(ValidationError):
        project.set_blocks([blocks['docker']])
    assert project.block_slugs() == {'angular', 'django', 'docker'}


def test_changing_blocks_keeps_progress_and_notes(
    project: Project, blocks: Blocks, roadmap_step: RoadmapStep
) -> None:
    project.completed_steps.create(step=roadmap_step)
    project.notes.create(step=roadmap_step, text='Port 8020.')
    project.set_blocks([blocks['angular']])
    assert project.block_slugs() == {'angular'}
    assert (project.completed_steps.count(), project.notes.count()) == (1, 1)


def test_chosen_block_cannot_be_deleted(project: Project, blocks: Blocks) -> None:
    with pytest.raises(ProtectedError):
        blocks['angular'].delete()


# Completed steps
def test_completed_step_links_project_and_step(project: Project, roadmap_step: RoadmapStep) -> None:
    done = project.completed_steps.create(step=roadmap_step)
    assert list(project.completed_steps.all()) == [done]
    assert done.created_at is not None
    assert str(done) == 'ada@example.com: Django-App anlegen'


def test_same_step_twice_is_rejected(project: Project, roadmap_step: RoadmapStep) -> None:
    project.completed_steps.create(step=roadmap_step)
    with pytest.raises(IntegrityError):
        project.completed_steps.create(step=roadmap_step)


def test_same_step_twice_fails_validation(project: Project, roadmap_step: RoadmapStep) -> None:
    project.completed_steps.create(step=roadmap_step)
    done = ProjectStep(project=project, step=roadmap_step)
    assert error_codes(done, '__all__') == ['unique_together']


def test_same_step_in_other_project_is_allowed(
    project: Project, other_user: User, roadmap_step: RoadmapStep
) -> None:
    other = Project.objects.create(user=other_user)
    project.completed_steps.create(step=roadmap_step)
    assert other.completed_steps.create(step=roadmap_step).pk


def test_completed_steps_follow_the_roadmap_order(
    project: Project, roadmap_step: RoadmapStep, second_step: RoadmapStep
) -> None:
    early = RoadmapPhase.objects.create(slug='vorbereiten', title_de='x', summary_de='x')
    first = early.steps.create(slug='git', title_de='Git', why_de='x', verification_de='x')
    for step in (second_step, roadmap_step, first):
        project.completed_steps.create(step=step)
    order = [done.step for done in project.completed_steps.all()]
    assert order == [first, roadmap_step, second_step]


# Notes
def test_note_links_project_and_step(project: Project, roadmap_step: RoadmapStep) -> None:
    note = project.notes.create(step=roadmap_step, text='Port 8020, weil 8000 belegt ist.')
    note.full_clean()
    assert list(project.notes.all()) == [note]
    assert (note.created_at, note.updated_at) != (None, None)
    assert str(note) == 'ada@example.com: Django-App anlegen'


def test_note_text_is_required(project: Project, roadmap_step: RoadmapStep) -> None:
    assert error_codes(ProjectNote(project=project, step=roadmap_step), 'text') == ['blank']


def test_note_text_is_limited(project: Project, roadmap_step: RoadmapStep) -> None:
    note = ProjectNote(project=project, step=roadmap_step, text='x' * 2001)
    assert error_codes(note, 'text') == ['max_length']


def test_note_with_maximum_length_is_valid(project: Project, roadmap_step: RoadmapStep) -> None:
    ProjectNote(project=project, step=roadmap_step, text='x' * 2000).full_clean()


@pytest.mark.parametrize('text', ['', 'x' * 2001])
def test_note_text_is_checked_in_database(
    project: Project, roadmap_step: RoadmapStep, text: str
) -> None:
    with pytest.raises(IntegrityError):
        project.notes.create(step=roadmap_step, text=text)


def test_one_note_per_step(project: Project, roadmap_step: RoadmapStep) -> None:
    project.notes.create(step=roadmap_step, text='Erste')
    with pytest.raises(IntegrityError):
        project.notes.create(step=roadmap_step, text='Zweite')


def test_second_note_fails_validation(project: Project, roadmap_step: RoadmapStep) -> None:
    project.notes.create(step=roadmap_step, text='Erste')
    note = ProjectNote(project=project, step=roadmap_step, text='Zweite')
    assert error_codes(note, '__all__') == ['unique_together']


def test_notes_follow_the_roadmap_order(
    project: Project, roadmap_step: RoadmapStep, second_step: RoadmapStep
) -> None:
    later = project.notes.create(step=second_step, text='Später')
    first = project.notes.create(step=roadmap_step, text='Zuerst')
    assert list(project.notes.all()) == [first, later]


def test_note_keeps_its_text_as_given(project: Project, roadmap_step: RoadmapStep) -> None:
    text = '<script>alert(1)</script>\n  Zeile 2'
    note = project.notes.create(step=roadmap_step, text=text)
    note.refresh_from_db()
    assert note.text == text


# Delete
def test_deleting_user_deletes_project_progress_and_notes(
    project: Project, other_user: User, roadmap_step: RoadmapStep
) -> None:
    other = Project.objects.create(user=other_user)
    for item in (project, other):
        item.completed_steps.create(step=roadmap_step)
        item.notes.create(step=roadmap_step, text='Notiz')
    project.user.delete()
    assert list(Project.objects.all()) == [other]
    assert list(ProjectStep.objects.values_list('project', flat=True)) == [other.pk]
    assert list(ProjectNote.objects.values_list('project', flat=True)) == [other.pk]
    assert not ProjectBlock.objects.exists()
    assert RoadmapBlock.objects.count() == 6


def test_deleting_step_deletes_its_progress_and_notes(
    project: Project, roadmap_step: RoadmapStep, second_step: RoadmapStep
) -> None:
    for step in (roadmap_step, second_step):
        project.completed_steps.create(step=step)
        project.notes.create(step=step, text='Notiz')
    roadmap_step.delete()
    assert [done.step for done in project.completed_steps.all()] == [second_step]
    assert [note.step for note in project.notes.all()] == [second_step]
    assert Project.objects.filter(pk=project.pk).exists()


# Roadmap of the project
def test_project_includes_steps_of_its_roadmap(
    project: Project, blocks: Blocks, roadmap_step: RoadmapStep
) -> None:
    project.set_blocks([blocks['angular'], blocks['django']])
    assert project.includes(roadmap_step)


def test_project_excludes_step_whose_conditions_fail(
    project: Project, roadmap_step: RoadmapStep
) -> None:
    assert project.block_slugs() == {'angular', 'django', 'docker'}
    assert not project.includes(roadmap_step)


def test_project_excludes_step_whose_phase_does_not_apply(
    project: Project, blocks: Blocks, roadmap_step: RoadmapStep
) -> None:
    project.set_blocks([blocks['angular']])
    assert not project.includes(roadmap_step)


def test_completed_map_groups_steps_by_phase_in_roadmap_order(
    project: Project, roadmap_step: RoadmapStep, second_step: RoadmapStep
) -> None:
    early = RoadmapPhase.objects.create(slug='vorbereiten', title_de='x', summary_de='x')
    git = early.steps.create(slug='git', title_de='Git', why_de='x', verification_de='x')
    for step in (second_step, git, roadmap_step):
        project.completed_steps.create(step=step)
    assert project.completed_map() == {
        'vorbereiten': ['git'],
        'backend-anlegen': ['app-anlegen', 'migrieren'],
    }


def test_notes_map_groups_texts_by_phase_and_step(
    project: Project, roadmap_step: RoadmapStep, second_step: RoadmapStep
) -> None:
    project.notes.create(step=second_step, text='Später')
    project.notes.create(step=roadmap_step, text='Zuerst')
    assert project.notes_map() == {
        'backend-anlegen': {'app-anlegen': 'Zuerst', 'migrieren': 'Später'}
    }


def test_maps_are_empty_without_progress_and_notes(project: Project) -> None:
    assert (project.completed_map(), project.notes_map()) == ({}, {})
