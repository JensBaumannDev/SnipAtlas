"""Public read-only views for the content."""

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
    News,
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
    NewsSerializer,
    TopicSerializer,
)


class GroupListView(generics.ListAPIView):
    """List all groups with their topics and subtopics."""

    queryset = Group.objects.prefetch_related('topics__subtopics')
    serializer_class = GroupSerializer
    permission_classes = (AllowAny,)


class TopicDetailView(generics.RetrieveAPIView):
    """Return a single topic with its subtopics."""

    queryset = Topic.objects.prefetch_related('subtopics')
    serializer_class = TopicSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'slug'


# Public content
class PublicContentViewSet(viewsets.ReadOnlyModelViewSet):
    """Public list and detail view that can filter by topic."""

    permission_classes = (AllowAny,)
    lookup_field = 'slug'
    lookup_value_regex = '[-a-zA-Z0-9_]+'

    def get_queryset(self) -> TopicQuerySet:
        """Return the items, filtered for the list."""
        queryset = super().get_queryset()
        if self.action == 'list':
            return self.filter_list(queryset, self.request.query_params)
        return queryset

    def filter_list(self, queryset: TopicQuerySet, params: QueryDict) -> TopicQuerySet:
        """Filter the list by the topic parameter."""
        topic = params.get('topic')
        return queryset.for_topic(topic) if topic else queryset


class EntryViewSet(PublicContentViewSet):
    """List and show commands."""

    queryset = Entry.objects.select_related('subtopic__topic')
    serializer_class = EntrySerializer


class ConceptViewSet(PublicContentViewSet):
    """List and show concepts."""

    queryset = Concept.objects.select_related('subtopic__topic')
    serializer_class = ConceptSerializer


class ErrorMessageViewSet(PublicContentViewSet):
    """List and show error messages."""

    queryset = ErrorMessage.objects.select_related('topic').prefetch_related('steps')
    serializer_class = ErrorMessageSerializer


class DebugGuideViewSet(PublicContentViewSet):
    """List and show debug guides."""

    queryset = DebugGuide.objects.select_related('topic').prefetch_related('steps')
    serializer_class = DebugGuideSerializer

    def filter_list(self, queryset: DebugGuideQuerySet, params: QueryDict) -> TopicQuerySet:
        """Return only general guides if requested, else by topic."""
        if params.get('general') == 'true':
            return queryset.general()
        return super().filter_list(queryset, params)


class BlueprintViewSet(PublicContentViewSet):
    """List and show blueprints."""

    queryset = Blueprint.objects.select_related('topic').prefetch_related('steps__codes')
    serializer_class = BlueprintSerializer


# Glossary
class GlossaryListView(generics.ListAPIView):
    """List all glossary terms."""

    queryset = GlossaryTerm.objects.select_related('concept__subtopic__topic').prefetch_related(
        'aliases'
    )
    serializer_class = GlossaryTermSerializer
    permission_classes = (AllowAny,)


# News
class NewsListView(generics.ListAPIView):
    """List all news items, newest first."""

    queryset = News.objects.select_related('topic', 'subtopic')
    serializer_class = NewsSerializer
    permission_classes = (AllowAny,)
