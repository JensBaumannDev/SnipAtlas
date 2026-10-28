from django.urls import URLPattern, path
from rest_framework.routers import SimpleRouter

from .views import ConceptViewSet, EntryViewSet, GroupListView, TopicDetailView

router = SimpleRouter()
router.register('entries', EntryViewSet)
router.register('concepts', ConceptViewSet)

urlpatterns: list[URLPattern] = [
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('topics/<slug:slug>/', TopicDetailView.as_view(), name='topic-detail'),
    *router.urls,
]
