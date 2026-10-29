from rest_framework import serializers

from app_content.models import Topic
from app_feedback.models import BugType, EntryArea, ImprovementArea, Kind, Suggestion

BASE_FIELDS = ('id', 'kind', 'email')
REQUIRED = {'required': True, 'allow_blank': False}


class SuggestionSerializer(serializers.ModelSerializer):
    kind = serializers.ChoiceField(choices=Kind.choices)

    class Meta:
        model = Suggestion
        fields = BASE_FIELDS
        read_only_fields = ('id',)
        extra_kwargs = {'email': REQUIRED}

    def get_fields(self) -> dict:
        fields = super().get_fields()
        if self.context['request'].user.is_authenticated:
            del fields['email']
        return fields

    def to_representation(self, instance: Suggestion) -> dict:
        return {'id': instance.pk}


class EntrySuggestionSerializer(SuggestionSerializer):
    area = serializers.ChoiceField(choices=EntryArea.choices)
    topic = serializers.SlugRelatedField(slug_field='slug', queryset=Topic.objects.all())

    class Meta(SuggestionSerializer.Meta):
        fields = (*BASE_FIELDS, 'area', 'topic', 'title', 'reason', 'example', 'source')
        extra_kwargs = SuggestionSerializer.Meta.extra_kwargs | {
            'title': REQUIRED,
            'reason': REQUIRED,
        }


class ImprovementSuggestionSerializer(SuggestionSerializer):
    area = serializers.ChoiceField(choices=ImprovementArea.choices)

    class Meta(SuggestionSerializer.Meta):
        fields = (*BASE_FIELDS, 'area', 'idea', 'benefit')
        extra_kwargs = SuggestionSerializer.Meta.extra_kwargs | {'idea': REQUIRED}


class BugSuggestionSerializer(SuggestionSerializer):
    type = serializers.ChoiceField(source='bug_type', choices=BugType.choices)

    class Meta(SuggestionSerializer.Meta):
        fields = (*BASE_FIELDS, 'type', 'location', 'problem', 'correction', 'environment')
        extra_kwargs = SuggestionSerializer.Meta.extra_kwargs | {
            'location': REQUIRED,
            'problem': REQUIRED,
        }


KIND_SERIALIZERS = {
    Kind.ENTRY: EntrySuggestionSerializer,
    Kind.IMPROVEMENT: ImprovementSuggestionSerializer,
    Kind.BUG: BugSuggestionSerializer,
}
