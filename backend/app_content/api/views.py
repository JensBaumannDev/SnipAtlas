from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny

from app_content.models import Concept, Entry, ErrorMessage, Group, Topic, TopicQuerySet

from .serializers import (
    ConceptSerializer,
    EntrySerializer,
    ErrorMessageSerializer,
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
        topic = self.request.query_params.get('topic')
        if topic and self.action == 'list':
            return queryset.for_topic(topic)
        return queryset


class EntryViewSet(PublicContentViewSet):
    queryset = Entry.objects.select_related('subtopic__topic')
    serializer_class = EntrySerializer


class ConceptViewSet(PublicContentViewSet):
    queryset = Concept.objects.select_related('subtopic__topic')
    serializer_class = ConceptSerializer


class ErrorMessageViewSet(PublicContentViewSet):
    queryset = ErrorMessage.objects.select_related('topic').prefetch_related('steps')
    serializer_class = ErrorMessageSerializer
