from modeltranslation.translator import TranslationOptions, register

from .models import Concept, Entry, Group, Subtopic, Topic


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
