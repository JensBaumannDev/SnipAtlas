from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import CompletedStep, Favorite, User

RIGHT_FIELDS = ('is_staff', 'is_superuser', 'groups', 'user_permissions')


def is_superuser_of_other(request: HttpRequest, obj: User | None) -> bool:
    return bool(obj and obj.is_superuser and not request.user.is_superuser)


class UserDataInline(admin.TabularInline):
    extra = 0
    related_field = ''

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related('user', self.related_field)

    def has_add_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return False


class FavoriteInline(UserDataInline):
    model = Favorite
    related_field = 'entry'
    fields = readonly_fields = ('entry', 'created_at')


class CompletedStepInline(UserDataInline):
    model = CompletedStep
    related_field = 'step'
    fields = readonly_fields = ('step', 'created_at')


class UserCreateForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ('email',)


class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreateForm
    form = UserEditForm
    list_display = ('email', 'date_joined', 'last_login', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')
    inlines = (FavoriteInline, CompletedStepInline)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Einstellungen', {'fields': ('notify_by_mail', 'accent', 'os', 'theme', 'language')}),
        (
            'Projektwerte',
            {
                'fields': (
                    'project_name',
                    'project_github_user',
                    'project_repo',
                    'project_domain',
                    'project_server_user',
                    'project_server_ip',
                )
            },
        ),
        (
            'Rechte',
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        ('Daten', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'usable_password', 'password1', 'password2'),
            },
        ),
    )

    def get_inlines(self, request: HttpRequest, obj: User | None) -> tuple:
        return self.inlines if obj else ()

    def get_readonly_fields(self, request: HttpRequest, obj: User | None = None) -> tuple:
        fields = tuple(super().get_readonly_fields(request, obj))
        if request.user.is_superuser:
            return fields
        return fields + RIGHT_FIELDS

    def has_change_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        if is_superuser_of_other(request, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        if is_superuser_of_other(request, obj):
            return False
        return super().has_delete_permission(request, obj)
