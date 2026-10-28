from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import ForeignKey
from django.forms.models import BaseInlineFormSet
from django.http import HttpRequest
from modeltranslation.admin import (
    TabbedTranslationAdmin,
    TranslationStackedInline,
    TranslationTabularInline,
)

from .models import (
    Blueprint,
    BlueprintCode,
    BlueprintStep,
    Concept,
    ContentItem,
    DebugGuide,
    DebugGuideStep,
    Entry,
    ErrorMessage,
    ErrorStep,
    GlossaryAlias,
    GlossaryTerm,
    Group,
    News,
    Subtopic,
    Topic,
)


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


class SubtopicChoicesMixin:
    def formfield_for_foreignkey(
        self, db_field: ForeignKey, request: HttpRequest, **kwargs: object
    ) -> forms.ModelChoiceField:
        if db_field.name == 'subtopic':
            kwargs['form_class'] = SubtopicChoiceField
            kwargs['queryset'] = Subtopic.objects.select_related('topic').order_by(
                'topic__position', 'topic_id', 'position', 'pk'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ContentItemAdmin(SubtopicChoicesMixin, TabbedTranslationAdmin):
    list_display = ('title', 'topic', 'subtopic', 'slug', 'position')
    list_editable = ('position',)
    list_filter = ('subtopic__topic', 'subtopic')
    search_fields = ('title',)
    list_select_related = ('subtopic__topic',)
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(description='topic', ordering='subtopic__topic__position')
    def topic(self, obj: ContentItem) -> Topic:
        return obj.subtopic.topic


@admin.register(Entry)
class EntryAdmin(ContentItemAdmin):
    pass


@admin.register(Concept)
class ConceptAdmin(ContentItemAdmin):
    pass


# Errors
class ErrorStepInline(TranslationTabularInline):
    model = ErrorStep
    extra = 1


@admin.register(ErrorMessage)
class ErrorMessageAdmin(TabbedTranslationAdmin):
    fields = ('topic', 'slug', 'message', 'meaning', 'cause', 'language', 'code', 'position')
    list_display = ('message', 'topic', 'slug', 'position')
    list_editable = ('position',)
    list_filter = ('topic',)
    search_fields = ('message',)
    list_select_related = ('topic',)
    prepopulated_fields = {'slug': ('message',)}
    inlines = (ErrorStepInline,)


# Debug guides
class DebugGuideStepInline(TranslationStackedInline):
    model = DebugGuideStep
    extra = 1


@admin.register(DebugGuide)
class DebugGuideAdmin(TabbedTranslationAdmin):
    fields = ('topic', 'label', 'slug', 'title', 'summary', 'position')
    list_display = ('title', 'topic', 'label', 'slug', 'position')
    list_editable = ('position',)
    list_filter = ('topic',)
    search_fields = ('title',)
    list_select_related = ('topic',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = (DebugGuideStepInline,)


# Blueprints
class BlueprintStepInline(TranslationStackedInline):
    model = BlueprintStep
    fields = ('title', 'slug', 'why', 'note', 'position')
    extra = 1
    prepopulated_fields = {'slug': ('title',)}
    show_change_link = True


@admin.register(Blueprint)
class BlueprintAdmin(TabbedTranslationAdmin):
    fields = ('topic', 'slug', 'title', 'summary', 'position')
    list_display = ('title', 'topic', 'slug', 'position')
    list_editable = ('position',)
    list_filter = ('topic',)
    search_fields = ('title', 'slug')
    list_select_related = ('topic',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = (BlueprintStepInline,)


class BlueprintCodeInline(TranslationStackedInline):
    model = BlueprintCode
    extra = 1


@admin.register(BlueprintStep)
class BlueprintStepAdmin(TabbedTranslationAdmin):
    fields = ('blueprint', 'slug', 'title', 'why', 'note', 'position')
    list_display = ('title', 'blueprint', 'slug', 'position')
    list_editable = ('position',)
    list_filter = ('blueprint',)
    search_fields = ('title',)
    list_select_related = ('blueprint',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = (BlueprintCodeInline,)


# Glossary
class GlossaryAliasFormSet(BaseInlineFormSet):
    def clean(self) -> None:
        super().clean()
        aliases = [
            (form.cleaned_data.get('language'), form.cleaned_data.get('name', '').lower())
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        ]
        if len(aliases) != len(set(aliases)):
            raise ValidationError('Use each alias only once per language.', code='duplicate')


class GlossaryAliasInline(admin.TabularInline):
    model = GlossaryAlias
    formset = GlossaryAliasFormSet
    fields = ('language', 'name')
    extra = 1


@admin.register(GlossaryTerm)
class GlossaryTermAdmin(TabbedTranslationAdmin):
    fields = ('term', 'slug', 'definition', 'concept')
    list_display = ('term', 'slug', 'concept')
    search_fields = ('term', 'slug', 'aliases__name')
    list_select_related = ('concept',)
    prepopulated_fields = {'slug': ('term',)}
    autocomplete_fields = ('concept',)
    inlines = (GlossaryAliasInline,)


# News
@admin.register(News)
class NewsAdmin(SubtopicChoicesMixin, TabbedTranslationAdmin):
    fields = ('date', 'title', 'area', 'topic', 'subtopic')
    list_display = ('date', 'title', 'area', 'topic', 'subtopic')
    list_filter = ('area', 'topic')
    search_fields = ('title',)
    list_select_related = ('topic', 'subtopic')
