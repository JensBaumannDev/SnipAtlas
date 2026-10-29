"""Translated fields of the content models."""

from modeltranslation.translator import TranslationOptions, register

from .models import (
    Blueprint,
    BlueprintCode,
    BlueprintStep,
    Concept,
    DebugGuide,
    DebugGuideStep,
    Entry,
    ErrorMessage,
    ErrorStep,
    GlossaryTerm,
    Group,
    News,
    Subtopic,
    Topic,
)


@register(Group)
class GroupTranslation(TranslationOptions):
    """Translated fields of a group."""

    fields = ('name',)


@register(Topic)
class TopicTranslation(TranslationOptions):
    """Translated fields of a topic."""

    fields = ('name',)


@register(Subtopic)
class SubtopicTranslation(TranslationOptions):
    """Translated fields of a subtopic."""

    fields = ('name',)


@register(Entry)
class EntryTranslation(TranslationOptions):
    """Translated fields of a command."""

    fields = ('title', 'description', 'code', 'code_unix')


@register(Concept)
class ConceptTranslation(TranslationOptions):
    """Translated fields of a concept."""

    fields = ('title', 'summary', 'explanation', 'code', 'note')


@register(ErrorMessage)
class ErrorMessageTranslation(TranslationOptions):
    """Translated fields of an error message."""

    fields = ('meaning', 'cause', 'code')


@register(ErrorStep)
class ErrorStepTranslation(TranslationOptions):
    """Translated fields of an error step."""

    fields = ('text',)


@register(DebugGuide)
class DebugGuideTranslation(TranslationOptions):
    """Translated fields of a debug guide."""

    fields = ('label', 'title', 'summary')


@register(DebugGuideStep)
class DebugGuideStepTranslation(TranslationOptions):
    """Translated fields of a debug guide step."""

    fields = ('title', 'text', 'code', 'code_unix')


@register(Blueprint)
class BlueprintTranslation(TranslationOptions):
    """Translated fields of a blueprint."""

    fields = ('title', 'summary')


@register(BlueprintStep)
class BlueprintStepTranslation(TranslationOptions):
    """Translated fields of a blueprint step."""

    fields = ('title', 'why', 'note')


@register(BlueprintCode)
class BlueprintCodeTranslation(TranslationOptions):
    """Translated fields of a blueprint code block."""

    fields = ('code', 'code_unix')


@register(GlossaryTerm)
class GlossaryTermTranslation(TranslationOptions):
    """Translated fields of a glossary term."""

    fields = ('term', 'definition')


@register(News)
class NewsTranslation(TranslationOptions):
    """Translated fields of a news item."""

    fields = ('title',)
