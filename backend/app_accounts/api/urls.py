from django.urls import URLPattern, path

from .views import (
    CsrfView,
    FavoriteListView,
    FavoriteView,
    LoginView,
    LogoutView,
    MeView,
    ProgressBlueprintView,
    ProgressListView,
    ProgressStepView,
    RegisterView,
    SettingsView,
)

urlpatterns: list[URLPattern] = [
    path('auth/csrf/', CsrfView.as_view(), name='auth-csrf'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('me/favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('me/favorites/<slug:entry>/', FavoriteView.as_view(), name='favorite-detail'),
    path('me/progress/', ProgressListView.as_view(), name='progress-list'),
    path(
        'me/progress/<slug:blueprint>/',
        ProgressBlueprintView.as_view(),
        name='progress-blueprint',
    ),
    path(
        'me/progress/<slug:blueprint>/<slug:step>/',
        ProgressStepView.as_view(),
        name='progress-step',
    ),
    path('me/settings/', SettingsView.as_view(), name='settings'),
]
