from django.urls import URLPattern, path
from rest_framework.routers import SimpleRouter

from .views import (
    BlueprintViewSet,
    ConceptViewSet,
    DebugGuideViewSet,
    EntryViewSet,
    ErrorMessageViewSet,
    GlossaryListView,
    GroupListView,
    NewsListView,
    TopicDetailView,
)

router = SimpleRouter()
router.register('entries', EntryViewSet)
router.register('concepts', ConceptViewSet)
router.register('errors', ErrorMessageViewSet, basename='error')
router.register('debug-guides', DebugGuideViewSet, basename='debug-guide')
router.register('blueprints', BlueprintViewSet, basename='blueprint')

urlpatterns: list[URLPattern] = [
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('topics/<slug:slug>/', TopicDetailView.as_view(), name='topic-detail'),
    path('glossary/', GlossaryListView.as_view(), name='glossary-list'),
    path('news/', NewsListView.as_view(), name='news-list'),
    *router.urls,
]
