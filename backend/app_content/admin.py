from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from .models import Group, Subtopic, Topic


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
