from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny

from app_content.models import Concept, ContentItemQuerySet, Entry, Group, Topic

from .serializers import ConceptSerializer, EntrySerializer, GroupSerializer, TopicSerializer


class GroupListView(generics.ListAPIView):
    queryset = Group.objects.prefetch_related('topics__subtopics')
    serializer_class = GroupSerializer
    permission_classes = (AllowAny,)


class TopicDetailView(generics.RetrieveAPIView):
    queryset = Topic.objects.prefetch_related('subtopics')
    serializer_class = TopicSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'slug'


# Entries and concepts
class ContentItemViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    lookup_field = 'slug'
    lookup_value_regex = '[-a-zA-Z0-9_]+'

    def get_queryset(self) -> ContentItemQuerySet:
        queryset = super().get_queryset().select_related('subtopic__topic')
        topic = self.request.query_params.get('topic')
        if topic and self.action == 'list':
            return queryset.for_topic(topic)
        return queryset


class EntryViewSet(ContentItemViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer


class ConceptViewSet(ContentItemViewSet):
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
