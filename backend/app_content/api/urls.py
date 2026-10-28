from django.urls import URLPattern, path

from .views import GroupListView, TopicDetailView

urlpatterns: list[URLPattern] = [
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('topics/<slug:slug>/', TopicDetailView.as_view(), name='topic-detail'),
]
