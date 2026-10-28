from modeltranslation.translator import TranslationOptions, register

from .models import Group, Subtopic, Topic


@register(Group)
class GroupTranslation(TranslationOptions):
    fields = ('name',)


@register(Topic)
class TopicTranslation(TranslationOptions):
    fields = ('name',)


@register(Subtopic)
class SubtopicTranslation(TranslationOptions):
    fields = ('name',)
