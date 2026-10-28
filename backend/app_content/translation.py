from modeltranslation.translator import TranslationOptions, register

from .models import (
    Concept,
    DebugGuide,
    DebugGuideStep,
    Entry,
    ErrorMessage,
    ErrorStep,
    Group,
    Subtopic,
    Topic,
)


@register(Group)
class GroupTranslation(TranslationOptions):
    fields = ('name',)


@register(Topic)
class TopicTranslation(TranslationOptions):
    fields = ('name',)


@register(Subtopic)
class SubtopicTranslation(TranslationOptions):
    fields = ('name',)


@register(Entry)
class EntryTranslation(TranslationOptions):
    fields = ('title', 'description', 'code', 'code_unix')


@register(Concept)
class ConceptTranslation(TranslationOptions):
    fields = ('title', 'summary', 'explanation', 'code', 'note')


@register(ErrorMessage)
class ErrorMessageTranslation(TranslationOptions):
    fields = ('meaning', 'cause', 'code')


@register(ErrorStep)
class ErrorStepTranslation(TranslationOptions):
    fields = ('text',)


@register(DebugGuide)
class DebugGuideTranslation(TranslationOptions):
    fields = ('label', 'title', 'summary')


@register(DebugGuideStep)
class DebugGuideStepTranslation(TranslationOptions):
    fields = ('title', 'text', 'code', 'code_unix')
