"""URLs for login, account, favorites, progress, settings and the roadmap project."""

from django.urls import URLPattern, path

from .views import (
    ActivateView,
    ActivationResendView,
    CsrfView,
    DeleteAccountView,
    EmailConfirmView,
    EmailView,
    FavoriteListView,
    FavoriteView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetView,
    PasswordView,
    ProgressBlueprintView,
    ProgressListView,
    ProgressStepView,
    ProjectNoteView,
    ProjectStepView,
    ProjectView,
    RegisterView,
    SettingsView,
)

urlpatterns: list[URLPattern] = [
    path('auth/csrf/', CsrfView.as_view(), name='auth-csrf'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/activate/', ActivateView.as_view(), name='auth-activate'),
    path('auth/activate/resend/', ActivationResendView.as_view(), name='auth-activate-resend'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('auth/email/', EmailView.as_view(), name='auth-email'),
    path('auth/email/confirm/', EmailConfirmView.as_view(), name='auth-email-confirm'),
    path('auth/password/', PasswordView.as_view(), name='auth-password'),
    path('auth/delete-account/', DeleteAccountView.as_view(), name='auth-delete-account'),
    path('auth/password-reset/', PasswordResetView.as_view(), name='auth-password-reset'),
    path(
        'auth/password-reset/confirm/',
        PasswordResetConfirmView.as_view(),
        name='auth-password-reset-confirm',
    ),
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
    path('me/project/', ProjectView.as_view(), name='project'),
    path(
        'me/project/steps/<slug:phase>/<slug:step>/',
        ProjectStepView.as_view(),
        name='project-step',
    ),
    path(
        'me/project/notes/<slug:phase>/<slug:step>/',
        ProjectNoteView.as_view(),
        name='project-note',
    ),
]
