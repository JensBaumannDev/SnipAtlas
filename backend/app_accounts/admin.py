"""Admin for users with their favorites and progress."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import CompletedStep, Favorite, User

RIGHT_FIELDS = ('is_staff', 'is_superuser', 'groups', 'user_permissions')


def is_superuser_of_other(request: HttpRequest, obj: User | None) -> bool:
    """Return whether a non-superuser tries to edit a superuser."""
    return bool(obj and obj.is_superuser and not request.user.is_superuser)


class UserDataInline(admin.TabularInline):
    """Read-only inline for the personal data of a user."""

    extra = 0
    related_field = ''

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Return the rows with the user and the related item loaded."""
        return super().get_queryset(request).select_related('user', self.related_field)

    def has_add_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        """Forbid adding user data in the admin."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        """Forbid changing user data in the admin."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        """Forbid deleting user data in the admin."""
        return False


class FavoriteInline(UserDataInline):
    """Favorites of a user, read-only."""

    model = Favorite
    related_field = 'entry'
    fields = readonly_fields = ('entry', 'created_at')


class CompletedStepInline(UserDataInline):
    """Completed blueprint steps of a user, read-only."""

    model = CompletedStep
    related_field = 'step'
    fields = readonly_fields = ('step', 'created_at')


class UserCreateForm(AdminUserCreationForm):
    """Form for creating a user with email and password."""

    class Meta:
        model = User
        fields = ('email',)


class UserEditForm(UserChangeForm):
    """Form for editing a user."""

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for users that only superusers may grant rights in."""

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
        """Show the inlines only when editing an existing user."""
        return self.inlines if obj else ()

    def get_readonly_fields(self, request: HttpRequest, obj: User | None = None) -> tuple:
        """Make the rights fields read-only for non-superusers."""
        fields = tuple(super().get_readonly_fields(request, obj))
        if request.user.is_superuser:
            return fields
        return fields + RIGHT_FIELDS

    def has_change_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        """Forbid non-superusers to change a superuser."""
        if is_superuser_of_other(request, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        """Forbid non-superusers to delete a superuser."""
        if is_superuser_of_other(request, obj):
            return False
        return super().has_delete_permission(request, obj)
