from django.urls import URLPattern, path

from .views import CsrfView, LoginView, RegisterView

urlpatterns: list[URLPattern] = [
    path('auth/csrf/', CsrfView.as_view(), name='auth-csrf'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
]
