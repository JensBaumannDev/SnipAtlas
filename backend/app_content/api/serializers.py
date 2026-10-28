from rest_framework import serializers

from app_content.models import Concept, Entry, Group, Subtopic, Topic


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
