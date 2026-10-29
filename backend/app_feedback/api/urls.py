from django.urls import URLPattern, path

from .views import MyRequestListView, RequestCreateView

urlpatterns: list[URLPattern] = [
    path('requests/', RequestCreateView.as_view(), name='request-create'),
    path('me/requests/', MyRequestListView.as_view(), name='my-requests'),
]
