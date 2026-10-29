"""Admin site that groups the models into sections like the website areas."""

from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

SECTIONS = (
    ('structure', _('Site structure'), ('app_content.group', 'app_content.topic')),
    ('commands', _('Commands & concepts'), ('app_content.entry', 'app_content.concept')),
    ('guides', _('Guides'), ('app_content.blueprint', 'app_content.blueprintstep')),
    ('errors', _('Errors'), ('app_content.errormessage', 'app_content.debugguide')),
    ('terms', _('Terms & news'), ('app_content.glossaryterm', 'app_content.news')),
    (
        'people',
        _('Users & requests'),
        ('app_accounts.user', 'app_feedback.suggestion', 'auth.group'),
    ),
)
OTHER_SECTION = ('other', _('More'))
MODEL_NAMES = {'auth.group': _('Permission groups')}


def _models_by_label(app_list: list[dict]) -> dict[str, dict]:
    """Return the model entries of the app list keyed by their model label."""
    entries = {}
    for app in app_list:
        for entry in app['models']:
            label = entry['model']._meta.label_lower
            entries[label] = {**entry, 'name': str(MODEL_NAMES.get(label, entry['name']))}
    return entries


def _section(key: str, name: str | Promise, models: list[dict]) -> dict:
    """Build an app list entry for a section that links to its first model."""
    return {
        'name': str(name),
        'app_label': key,
        'app_url': models[0]['admin_url'],
        'has_module_perms': True,
        'models': models,
    }


def group_into_sections(app_list: list[dict]) -> list[dict]:
    """Regroup the app list into sections, unlisted models go into a last section."""
    entries = _models_by_label(app_list)
    sections = []
    for key, name, labels in SECTIONS:
        models = [entries.pop(label) for label in labels if label in entries]
        if models:
            sections.append(_section(key, name, models))
    if entries:
        sections.append(_section(*OTHER_SECTION, list(entries.values())))
    return sections


class SnipAtlasAdminSite(AdminSite):
    """Admin site with SnipAtlas branding and sections on the index page."""

    site_header = 'SnipAtlas Admin'
    site_title = 'SnipAtlas Admin'

    def get_app_list(self, request: HttpRequest, app_label: str | None = None) -> list[dict]:
        """Return the sections on the index and sidebar, the plain app on an app page."""
        app_list = super().get_app_list(request, app_label)
        return app_list if app_label else group_into_sections(app_list)
