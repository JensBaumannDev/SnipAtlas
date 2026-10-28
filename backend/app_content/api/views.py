from django.http import QueryDict
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny

from app_content.models import (
    Blueprint,
    Concept,
    DebugGuide,
    DebugGuideQuerySet,
    Entry,
    ErrorMessage,
    GlossaryTerm,
    Group,
    Topic,
    TopicQuerySet,
)

from .serializers import (
    BlueprintSerializer,
    ConceptSerializer,
    DebugGuideSerializer,
    EntrySerializer,
    ErrorMessageSerializer,
    GlossaryTermSerializer,
    GroupSerializer,
    TopicSerializer,
)


class GroupListView(generics.ListAPIView):
    queryset = Group.objects.prefetch_related('topics__subtopics')
    serializer_class = GroupSerializer
    permission_classes = (AllowAny,)


class TopicDetailView(generics.RetrieveAPIView):
    queryset = Topic.objects.prefetch_related('subtopics')
    serializer_class = TopicSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'slug'


# Public content
class PublicContentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    lookup_field = 'slug'
    lookup_value_regex = '[-a-zA-Z0-9_]+'

    def get_queryset(self) -> TopicQuerySet:
        queryset = super().get_queryset()
        if self.action == 'list':
            return self.filter_list(queryset, self.request.query_params)
        return queryset

    def filter_list(self, queryset: TopicQuerySet, params: QueryDict) -> TopicQuerySet:
        topic = params.get('topic')
        return queryset.for_topic(topic) if topic else queryset


class EntryViewSet(PublicContentViewSet):
    queryset = Entry.objects.select_related('subtopic__topic')
    serializer_class = EntrySerializer


class ConceptViewSet(PublicContentViewSet):
    queryset = Concept.objects.select_related('subtopic__topic')
    serializer_class = ConceptSerializer


class ErrorMessageViewSet(PublicContentViewSet):
    queryset = ErrorMessage.objects.select_related('topic').prefetch_related('steps')
    serializer_class = ErrorMessageSerializer


class DebugGuideViewSet(PublicContentViewSet):
    queryset = DebugGuide.objects.select_related('topic').prefetch_related('steps')
    serializer_class = DebugGuideSerializer

    def filter_list(self, queryset: DebugGuideQuerySet, params: QueryDict) -> TopicQuerySet:
        if params.get('general') == 'true':
            return queryset.general()
        return super().filter_list(queryset, params)


class BlueprintViewSet(PublicContentViewSet):
    queryset = Blueprint.objects.select_related('topic').prefetch_related('steps__codes')
    serializer_class = BlueprintSerializer


# Glossary
class GlossaryListView(generics.ListAPIView):
    queryset = GlossaryTerm.objects.select_related('concept__subtopic__topic').prefetch_related(
        'aliases'
    )
    serializer_class = GlossaryTermSerializer
    permission_classes = (AllowAny,)
