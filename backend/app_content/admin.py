from django import forms
from django.contrib import admin
from django.db.models import ForeignKey
from django.http import HttpRequest
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from .models import Concept, ContentItem, Entry, Group, Subtopic, Topic


@admin.register(Group)
class GroupAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'slug', 'position')
    list_editable = ('position',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class SubtopicInline(TranslationTabularInline):
    model = Subtopic
    extra = 1
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Topic)
class TopicAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'group', 'slug', 'color', 'position')
    list_editable = ('position',)
    list_filter = ('group',)
    search_fields = ('name',)
    list_select_related = ('group',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = (SubtopicInline,)


# Entries and concepts
class SubtopicChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Subtopic) -> str:
        return f'{obj.topic} – {obj}'


class ContentItemAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'topic', 'subtopic', 'slug', 'position')
    list_editable = ('position',)
    list_filter = ('subtopic__topic', 'subtopic')
    search_fields = ('title',)
    list_select_related = ('subtopic__topic',)
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(description='topic', ordering='subtopic__topic__position')
    def topic(self, obj: ContentItem) -> Topic:
        return obj.subtopic.topic

    def formfield_for_foreignkey(
        self, db_field: ForeignKey, request: HttpRequest, **kwargs: object
    ) -> forms.ModelChoiceField:
        if db_field.name == 'subtopic':
            kwargs['form_class'] = SubtopicChoiceField
            kwargs['queryset'] = Subtopic.objects.select_related('topic').order_by(
                'topic__position', 'topic_id', 'position', 'pk'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Entry)
class EntryAdmin(ContentItemAdmin):
    pass


@admin.register(Concept)
class ConceptAdmin(ContentItemAdmin):
    pass
