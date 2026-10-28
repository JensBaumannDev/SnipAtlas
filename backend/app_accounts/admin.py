from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.http import HttpRequest

from .models import User

RIGHT_FIELDS = ('is_staff', 'is_superuser', 'groups', 'user_permissions')


def is_superuser_of_other(request: HttpRequest, obj: User | None) -> bool:
    return bool(obj and obj.is_superuser and not request.user.is_superuser)


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
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Einstellungen', {'fields': ('notify_by_mail', 'accent')}),
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
