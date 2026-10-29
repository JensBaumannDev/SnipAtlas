"""Serializers for the content in the form of the frontend interfaces."""

from modeltranslation.utils import get_language
from rest_framework import serializers

from app_content.models import (
    Blueprint,
    BlueprintCode,
    BlueprintStep,
    Concept,
    DebugGuide,
    DebugGuideStep,
    Entry,
    ErrorMessage,
    GlossaryTerm,
    Group,
    News,
    Subtopic,
    Topic,
)


class SubtopicSerializer(serializers.ModelSerializer):
    """Subtopic with slug and name."""

    class Meta:
        model = Subtopic
        fields = ('slug', 'name')


class TopicSerializer(serializers.ModelSerializer):
    """Topic with its subtopics."""

    subtopics = SubtopicSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ('slug', 'name', 'color', 'subtopics')


class GroupSerializer(serializers.ModelSerializer):
    """Group with its topics."""

    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('slug', 'name', 'topics')


# Entries and concepts
class ContentItemSerializer(serializers.ModelSerializer):
    """Shared fields of commands and concepts."""

    topic = serializers.CharField(source='subtopic.topic.slug', read_only=True)
    subtopic = serializers.CharField(source='subtopic.slug', read_only=True)


class EntrySerializer(ContentItemSerializer):
    """Command with code split by operating system if needed."""

    code = serializers.JSONField(source='os_code', read_only=True)

    class Meta:
        model = Entry
        fields = ('slug', 'topic', 'subtopic', 'title', 'description', 'language', 'code')


class ConceptSerializer(ContentItemSerializer):
    """Concept with explanation and optional code."""

    class Meta:
        model = Concept
        fields = (
            'slug',
            'topic',
            'subtopic',
            'title',
            'summary',
            'explanation',
            'language',
            'code',
            'note',
        )


# Errors and debug guides
class OptionalFieldsSerializer(serializers.ModelSerializer):
    """Serializer that leaves out empty optional fields."""

    optional_fields: tuple[str, ...] = ()

    def to_representation(self, instance: object) -> dict:
        """Return the data without empty fields."""
        data = super().to_representation(instance)
        for field in self.optional_fields:
            if not data[field]:
                del data[field]
        return data


class ErrorMessageSerializer(OptionalFieldsSerializer):
    """Error message with steps and optional solution."""

    topic = serializers.CharField(source='topic.slug', read_only=True)
    steps = serializers.SlugRelatedField(many=True, read_only=True, slug_field='text')
    solution = serializers.SerializerMethodField()
    optional_fields = ('solution',)

    class Meta:
        model = ErrorMessage
        fields = ('slug', 'topic', 'message', 'meaning', 'cause', 'steps', 'solution')

    def get_solution(self, error: ErrorMessage) -> dict[str, str] | None:
        """Return the solution code or None without code."""
        if not error.code:
            return None
        return {'language': error.language, 'code': error.code}


class DebugGuideStepSerializer(OptionalFieldsSerializer):
    """Step of a debug guide with optional code."""

    code = serializers.SerializerMethodField()
    optional_fields = ('code',)

    class Meta:
        model = DebugGuideStep
        fields = ('title', 'text', 'code')

    def get_code(self, step: DebugGuideStep) -> dict[str, object] | None:
        """Return the code with its language or None."""
        if not step.code:
            return None
        return {'language': step.language, 'code': step.os_code}


class DebugGuideSerializer(OptionalFieldsSerializer):
    """Debug guide with its steps."""

    topic = serializers.SlugRelatedField(read_only=True, slug_field='slug')
    steps = DebugGuideStepSerializer(many=True, read_only=True)
    optional_fields = ('topic', 'label')

    class Meta:
        model = DebugGuide
        fields = ('slug', 'topic', 'label', 'title', 'summary', 'steps')


# Blueprints
class BlueprintCodeSerializer(serializers.ModelSerializer):
    """Code block of a blueprint step."""

    code = serializers.JSONField(source='os_code', read_only=True)

    class Meta:
        model = BlueprintCode
        fields = ('language', 'code')


class BlueprintStepSerializer(OptionalFieldsSerializer):
    """Step of a blueprint with its code blocks."""

    code = BlueprintCodeSerializer(source='codes', many=True, read_only=True)
    optional_fields = ('note',)

    class Meta:
        model = BlueprintStep
        fields = ('slug', 'title', 'why', 'code', 'note')


class BlueprintSerializer(serializers.ModelSerializer):
    """Blueprint with its steps."""

    topic = serializers.CharField(source='topic.slug', read_only=True)
    steps = BlueprintStepSerializer(many=True, read_only=True)

    class Meta:
        model = Blueprint
        fields = ('slug', 'topic', 'title', 'summary', 'steps')


# Glossary
class GlossaryTermSerializer(OptionalFieldsSerializer):
    """Glossary term with aliases and optional concept link."""

    aliases = serializers.SerializerMethodField()
    concept = serializers.SerializerMethodField()
    optional_fields = ('concept',)

    class Meta:
        model = GlossaryTerm
        fields = ('slug', 'term', 'aliases', 'definition', 'concept')

    def get_aliases(self, term: GlossaryTerm) -> list[str]:
        """Return the aliases in the current language."""
        language = get_language()
        return [alias.name for alias in term.aliases.all() if alias.language == language]

    def get_concept(self, term: GlossaryTerm) -> dict[str, str] | None:
        """Return the link parts of the concept or None."""
        if not term.concept:
            return None
        subtopic = term.concept.subtopic
        return {'topic': subtopic.topic.slug, 'subtopic': subtopic.slug, 'slug': term.concept.slug}


# News
class NewsSerializer(serializers.ModelSerializer):
    """News item with its link."""

    topic = serializers.CharField(source='topic.slug', read_only=True)
    link = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = News
        fields = ('date', 'topic', 'title', 'link')
