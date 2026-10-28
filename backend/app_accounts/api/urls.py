from django.urls import URLPattern, path

from .views import RegisterView

urlpatterns: list[URLPattern] = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
]
