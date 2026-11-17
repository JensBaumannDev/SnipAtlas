"""Sitemaps that list every public frontend page for search engines."""

from collections.abc import Iterable

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet

from .models import (
    AI_PATH,
    BLUEPRINTS_PATH,
    COMMANDS_PATH,
    CONCEPTS_PATH,
    ERRORS_PATH,
    Blueprint,
    Concept,
    ContentItem,
    DebugGuide,
    Entry,
    ErrorMessage,
)

STATIC_PATHS = (
    '/',
    f'/{COMMANDS_PATH}',
    f'/{CONCEPTS_PATH}',
    f'/{BLUEPRINTS_PATH}',
    f'/{ERRORS_PATH}',
    AI_PATH,
    '/begriffe',
    '/neu',
    '/faq',
    '/vscode-theme',
)


def entries() -> QuerySet[Entry]:
    """Return all commands with the data their URL needs."""
    return Entry.objects.select_related('subtopic__topic__group')


def concepts() -> QuerySet[Concept]:
    """Return all concepts with the data their URL needs."""
    return Concept.objects.select_related('subtopic__topic__group')


def blueprints() -> QuerySet[Blueprint]:
    """Return all guides with the data their URL needs."""
    return Blueprint.objects.select_related('topic__group')


def errors() -> QuerySet[ErrorMessage]:
    """Return all error messages with the data their URL needs."""
    return ErrorMessage.objects.select_related('topic__group')


def subtopic_pages(items: Iterable[ContentItem]) -> Iterable[str]:
    """Yield the topic and subtopic pages of commands or concepts."""
    for item in items:
        yield item.subtopic.topic.area_url(item.url_area)
        yield item.subtopic.area_url(item.url_area)


def topic_pages() -> Iterable[str]:
    """Yield the topic and subtopic pages of every area that has content."""
    yield from subtopic_pages(entries())
    yield from subtopic_pages(concepts())
    for blueprint in blueprints():
        yield blueprint.topic.area_url(BLUEPRINTS_PATH)
    for error in errors():
        yield error.topic.area_url(ERRORS_PATH)
    for guide in DebugGuide.objects.select_related('topic__group').filter(topic__isnull=False):
        yield guide.get_absolute_url()


class PathSitemap(Sitemap):
    """Sitemap of pages given as paths."""

    def location(self, item: str) -> str:
        """Return the path itself as the location."""
        return item


class StaticSitemap(PathSitemap):
    """Sitemap of the start page and the fixed pages."""

    def items(self) -> tuple[str, ...]:
        """Return the fixed paths."""
        return STATIC_PATHS


class TopicSitemap(PathSitemap):
    """Sitemap of the topic and subtopic pages with content."""

    def items(self) -> list[str]:
        """Return each topic and subtopic page only once."""
        return list(dict.fromkeys(topic_pages()))


class EntrySitemap(Sitemap):
    """Sitemap of the command pages."""

    def items(self) -> QuerySet[Entry]:
        """Return all commands."""
        return entries()


class ConceptSitemap(Sitemap):
    """Sitemap of the concept pages."""

    def items(self) -> QuerySet[Concept]:
        """Return all concepts."""
        return concepts()


class BlueprintSitemap(Sitemap):
    """Sitemap of the guide pages."""

    def items(self) -> QuerySet[Blueprint]:
        """Return all guides."""
        return blueprints()


class ErrorSitemap(Sitemap):
    """Sitemap of the error pages."""

    def items(self) -> QuerySet[ErrorMessage]:
        """Return all error messages."""
        return errors()


class DebugGuideSitemap(Sitemap):
    """Sitemap of the general debug guides, topic guides live on the topic pages."""

    def items(self) -> QuerySet[DebugGuide]:
        """Return the general debug guides."""
        return DebugGuide.objects.general()


SITEMAPS = {
    'pages': StaticSitemap,
    'topics': TopicSitemap,
    'commands': EntrySitemap,
    'concepts': ConceptSitemap,
    'guides': BlueprintSitemap,
    'errors': ErrorSitemap,
    'debug': DebugGuideSitemap,
}
