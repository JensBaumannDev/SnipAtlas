from django.urls import URLPattern, path
from rest_framework.routers import SimpleRouter

from .views import EntryViewSet, GroupListView, TopicDetailView

router = SimpleRouter()
router.register('entries', EntryViewSet)

urlpatterns: list[URLPattern] = [
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('topics/<slug:slug>/', TopicDetailView.as_view(), name='topic-detail'),
    *router.urls,
]
