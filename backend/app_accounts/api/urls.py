from django.urls import URLPattern, path

from .views import CsrfView, RegisterView

urlpatterns: list[URLPattern] = [
    path('auth/csrf/', CsrfView.as_view(), name='auth-csrf'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
]
