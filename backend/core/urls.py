"""Root URL configuration that mounts the admin and the API of each app."""

from django.contrib import admin
from django.urls import include, path, re_path

from .views import ApiNotFoundView

admin.site.site_header = 'SnipAtlas Admin'
admin.site.site_title = 'SnipAtlas Admin'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app_accounts.api.urls')),
    path('api/', include('app_content.api.urls')),
    path('api/', include('app_feedback.api.urls')),
    re_path(r'^api/(?:.*/)?$', ApiNotFoundView.as_view()),
]
