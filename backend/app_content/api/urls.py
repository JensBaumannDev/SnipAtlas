from django.urls import URLPattern, path

from .views import GroupListView

urlpatterns: list[URLPattern] = [
    path('groups/', GroupListView.as_view(), name='group-list'),
]
