from rest_framework import generics
from rest_framework.permissions import AllowAny

from app_content.models import Group

from .serializers import GroupSerializer


class GroupListView(generics.ListAPIView):
    queryset = Group.objects.prefetch_related('topics__subtopics')
    serializer_class = GroupSerializer
    permission_classes = (AllowAny,)
