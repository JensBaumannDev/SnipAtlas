"""Root URL configuration that mounts the sitemap, the admin and the API of each app."""

from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_page

from app_content.sitemaps import SITEMAPS

from .views import ApiNotFoundView

SITEMAP_CACHE_SECONDS = 60 * 60

urlpatterns = [
    path(
        'sitemap.xml',
        cache_page(SITEMAP_CACHE_SECONDS)(sitemap),
        {'sitemaps': SITEMAPS},
        name='sitemap',
    ),
    path(settings.ADMIN_PATH, admin.site.urls),
    path('api/', include('app_accounts.api.urls')),
    path('api/', include('app_content.api.urls')),
    path('api/', include('app_feedback.api.urls')),
    re_path(r'^api/(?:.*/)?$', ApiNotFoundView.as_view()),
]
