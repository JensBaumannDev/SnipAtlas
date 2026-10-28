from rest_framework import generics
from rest_framework.permissions import AllowAny

from app_content.models import Group, Topic

from .serializers import GroupSerializer, TopicSerializer


class GroupListView(generics.ListAPIView):
    queryset = Group.objects.prefetch_related('topics__subtopics')
    serializer_class = GroupSerializer
    permission_classes = (AllowAny,)


class TopicDetailView(generics.RetrieveAPIView):
    queryset = Topic.objects.prefetch_related('subtopics')
    serializer_class = TopicSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'slug'
