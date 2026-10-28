from rest_framework import serializers

from app_content.models import Group, Subtopic, Topic


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
