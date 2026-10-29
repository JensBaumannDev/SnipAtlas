"""Admin for all content with tabs for German and English."""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import ForeignKey
from django.forms.models import BaseInlineFormSet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
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
    """Admin for groups."""

    list_display = ('name', 'slug', 'position')
    list_editable = ('position',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class SubtopicInline(TranslationTabularInline):
    """Subtopics of a topic."""

    model = Subtopic
    extra = 1
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Topic)
class TopicAdmin(TabbedTranslationAdmin):
    """Admin for topics with their subtopics."""

    list_display = ('name', 'group', 'slug', 'color', 'position')
    list_editable = ('position',)
    list_filter = ('group',)
    search_fields = ('name',)
    list_select_related = ('group',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = (SubtopicInline,)


# Entries and concepts
class SubtopicChoiceField(forms.ModelChoiceField):
    """Subtopic choice that also shows the topic."""

    def label_from_instance(self, obj: Subtopic) -> str:
        """Return the label with topic and subtopic."""
        return f'{obj.topic} – {obj}'


class SubtopicChoicesMixin:
    """Mixin that lists subtopics with their topic, sorted by topic."""

    def formfield_for_foreignkey(
        self, db_field: ForeignKey, request: HttpRequest, **kwargs: object
    ) -> forms.ModelChoiceField:
        """Use the subtopic choice for subtopics."""
        if db_field.name == 'subtopic':
            kwargs['form_class'] = SubtopicChoiceField
            kwargs['queryset'] = Subtopic.objects.select_related('topic').order_by(
                'topic__position', 'topic_id', 'position', 'pk'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ContentItemAdmin(SubtopicChoicesMixin, TabbedTranslationAdmin):
    """Shared admin for commands and concepts."""

    list_display = ('title', 'topic', 'subtopic', 'slug', 'position')
    list_editable = ('position',)
    list_filter = ('subtopic__topic', 'subtopic')
    search_fields = ('title',)
    list_select_related = ('subtopic__topic',)
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(description=_('topic'), ordering='subtopic__topic__position')
    def topic(self, obj: ContentItem) -> Topic:
        """Return the topic of the subtopic for the list."""
        return obj.subtopic.topic


@admin.register(Entry)
class EntryAdmin(ContentItemAdmin):
    """Admin for commands."""

    pass


@admin.register(Concept)
class ConceptAdmin(ContentItemAdmin):
    """Admin for concepts."""

    pass


# Errors
class ErrorStepInline(TranslationTabularInline):
    """Steps of an error message."""

    model = ErrorStep
    extra = 1


@admin.register(ErrorMessage)
class ErrorMessageAdmin(TabbedTranslationAdmin):
    """Admin for error messages with their steps."""

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
    """Steps of a debug guide."""

    model = DebugGuideStep
    extra = 1


@admin.register(DebugGuide)
class DebugGuideAdmin(TabbedTranslationAdmin):
    """Admin for debug guides with their steps."""

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
    """Steps of a blueprint, with a link to edit their code."""

    model = BlueprintStep
    fields = ('title', 'slug', 'why', 'note', 'position')
    extra = 1
    prepopulated_fields = {'slug': ('title',)}
    show_change_link = True


@admin.register(Blueprint)
class BlueprintAdmin(TabbedTranslationAdmin):
    """Admin for blueprints with their steps."""

    fields = ('topic', 'slug', 'title', 'summary', 'position')
    list_display = ('title', 'topic', 'slug', 'position')
    list_editable = ('position',)
    list_filter = ('topic',)
    search_fields = ('title', 'slug')
    list_select_related = ('topic',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = (BlueprintStepInline,)


class BlueprintCodeInline(TranslationStackedInline):
    """Code blocks of a blueprint step."""

    model = BlueprintCode
    extra = 1


@admin.register(BlueprintStep)
class BlueprintStepAdmin(TabbedTranslationAdmin):
    """Admin for blueprint steps with their code blocks."""

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
    """Form set that rejects duplicate aliases."""

    def clean(self) -> None:
        """Raise an error if an alias appears twice in one language."""
        super().clean()
        aliases = [
            (form.cleaned_data.get('language'), form.cleaned_data.get('name', '').lower())
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        ]
        if len(aliases) != len(set(aliases)):
            raise ValidationError(_('Use each alias only once per language.'), code='duplicate')


class GlossaryAliasInline(admin.TabularInline):
    """Aliases of a glossary term."""

    model = GlossaryAlias
    formset = GlossaryAliasFormSet
    fields = ('language', 'name')
    extra = 1


@admin.register(GlossaryTerm)
class GlossaryTermAdmin(TabbedTranslationAdmin):
    """Admin for glossary terms with their aliases."""

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
    """Admin for news items."""

    fields = ('date', 'title', 'area', 'topic', 'subtopic')
    list_display = ('date', 'title', 'area', 'topic', 'subtopic')
    list_filter = ('area', 'topic')
    search_fields = ('title',)
    list_select_related = ('topic', 'subtopic')
