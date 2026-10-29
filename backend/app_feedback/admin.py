from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Kind, Status, Suggestion

KIND_FIELDSETS = {
    Kind.ENTRY: ('Ergänzung', ('area', 'topic', 'title', 'reason', 'example', 'source')),
    Kind.IMPROVEMENT: ('Verbesserung', ('area', 'idea', 'benefit')),
    Kind.BUG: ('Fehler', ('bug_type', 'location', 'problem', 'correction', 'environment')),
}

SUBMITTED_FIELDS = (
    'kind',
    'contact_email',
    'created_at',
    'answered_at',
    'area',
    'topic',
    'title',
    'reason',
    'example',
    'source',
    'idea',
    'benefit',
    'bug_type',
    'location',
    'problem',
    'correction',
    'environment',
)


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind', 'subject', 'contact_email', 'status', 'created_at')
    list_display_links = ('id', 'subject')
    list_filter = ('status', 'kind')
    list_select_related = ('user',)
    search_fields = (
        'title',
        'reason',
        'idea',
        'location',
        'problem',
        'email',
        'user__email',
    )
    ordering = ('-status', '-created_at', '-pk')
    readonly_fields = SUBMITTED_FIELDS
    actions = ('mark_done',)

    def get_fieldsets(self, request: HttpRequest, obj: Suggestion | None = None) -> list:
        fieldsets = [(None, {'fields': ('kind', 'contact_email', 'created_at')})]
        if obj:
            name, fields = KIND_FIELDSETS[obj.kind]
            fieldsets.append((name, {'fields': fields}))
        fieldsets.append(('Bearbeitung', {'fields': ('status', 'answer', 'answered_at')}))
        return fieldsets

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @admin.action(description='Als erledigt markieren', permissions=('change',))
    def mark_done(self, request: HttpRequest, queryset: QuerySet[Suggestion]) -> None:
        queryset.update(status=Status.DONE)
