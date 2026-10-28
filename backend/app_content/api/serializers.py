from rest_framework import serializers

from app_content.models import Concept, Entry, ErrorMessage, Group, Subtopic, Topic


class SubtopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtopic
        fields = ('slug', 'name')


class TopicSerializer(serializers.ModelSerializer):
    subtopics = SubtopicSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ('slug', 'name', 'color', 'subtopics')


class GroupSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('slug', 'name', 'topics')


# Entries and concepts
class ContentItemSerializer(serializers.ModelSerializer):
    topic = serializers.CharField(source='subtopic.topic.slug', read_only=True)
    subtopic = serializers.CharField(source='subtopic.slug', read_only=True)


class EntrySerializer(ContentItemSerializer):
    code = serializers.JSONField(source='os_code', read_only=True)

    class Meta:
        model = Entry
        fields = ('slug', 'topic', 'subtopic', 'title', 'description', 'language', 'code')


class ConceptSerializer(ContentItemSerializer):
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
    optional_fields: tuple[str, ...] = ()

    def to_representation(self, instance: object) -> dict:
        data = super().to_representation(instance)
        for field in self.optional_fields:
            if not data[field]:
                del data[field]
        return data


class ErrorMessageSerializer(OptionalFieldsSerializer):
    topic = serializers.CharField(source='topic.slug', read_only=True)
    steps = serializers.SlugRelatedField(many=True, read_only=True, slug_field='text')
    solution = serializers.SerializerMethodField()
    optional_fields = ('solution',)

    class Meta:
        model = ErrorMessage
        fields = ('slug', 'topic', 'message', 'meaning', 'cause', 'steps', 'solution')

    def get_solution(self, error: ErrorMessage) -> dict[str, str] | None:
        if not error.code:
            return None
        return {'language': error.language, 'code': error.code}
