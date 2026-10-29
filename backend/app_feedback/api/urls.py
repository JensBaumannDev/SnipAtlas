from django.urls import URLPattern, path

from .views import RequestCreateView

urlpatterns: list[URLPattern] = [
    path('requests/', RequestCreateView.as_view(), name='request-create'),
]
