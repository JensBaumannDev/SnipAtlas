import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Model, ProtectedError
from django.utils import translation

from app_content.models import Group, Subtopic, Topic

pytestmark = pytest.mark.django_db


def error_codes(obj: Model, field: str) -> list[str]:
    with pytest.raises(ValidationError) as error:
        obj.full_clean()
    return [item.code for item in error.value.error_dict[field]]


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


@pytest.mark.parametrize('slug', ['Python', 'node_npm', 'git-', '-git', 'git--hub'])
@pytest.mark.parametrize('fixture', ['group', 'topic', 'subtopic'])
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


# Delete
def test_group_with_topics_cannot_be_deleted(group: Group, topic: Topic) -> None:
    with pytest.raises(ProtectedError):
        group.delete()


def test_deleting_topic_deletes_subtopics(topic: Topic, subtopic: Subtopic) -> None:
    topic.delete()
    assert not Subtopic.objects.exists()
