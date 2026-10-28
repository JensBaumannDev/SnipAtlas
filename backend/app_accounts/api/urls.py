from django.urls import URLPattern, path

from .views import (
    CsrfView,
    FavoriteListView,
    FavoriteView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
)

urlpatterns: list[URLPattern] = [
    path('auth/csrf/', CsrfView.as_view(), name='auth-csrf'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('me/favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('me/favorites/<slug:entry>/', FavoriteView.as_view(), name='favorite-detail'),
]
