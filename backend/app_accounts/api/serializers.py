"""Serializers for login, account, favorites and settings."""

from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.fields import get_error_detail

from app_accounts.emails import send_reset_mail
from app_accounts.models import (
    PROJECT_VALUE_FIELDS,
    PROJECT_VALUE_MAX_LENGTH,
    Favorite,
    User,
    UserManager,
)

from .exceptions import InvalidCredentials, InvalidLink, WrongPassword


class UserSerializer(serializers.ModelSerializer):
    """Public data of the logged-in user."""

    since = serializers.DateField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'since', 'notify_by_mail', 'accent')
        read_only_fields = ('email',)


def unique_email(value: str, user: User | None = None) -> str:
    """Return the normalized email or raise an error if another user has it."""
    email = UserManager.normalize_email(value)
    taken = User.objects.filter(email=email)
    if user:
        taken = taken.exclude(pk=user.pk)
    if taken.exists():
        raise serializers.ValidationError('Email is taken.', code='unique')
    return email


# Register
class RegisterSerializer(serializers.Serializer):
    """Registration with email and password."""

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value: str) -> str:
        """Check that the email address is still free."""
        return unique_email(value)

    def validate_password(self, value: str) -> str:
        """Check the password against the password rules."""
        password_validation.validate_password(value, User(email=self.initial_data.get('email')))
        return value

    def create(self, validated_data: dict) -> User:
        """Create the new user."""
        return User.objects.create_user(validated_data['email'], validated_data['password'])

    def to_representation(self, user: User) -> dict:
        """Return the new user like the user endpoint."""
        return UserSerializer(user).data


# Login
class LoginSerializer(serializers.Serializer):
    """Login with email and password."""

    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        """Check the login data and return the matching user."""
        request = self.context['request']
        user = authenticate(request, email=attrs['email'], password=attrs['password'])
        if user is None:
            raise InvalidCredentials
        return {'user': user}


# Account
def check_current_password(user: User, value: str) -> str:
    """Return the password or raise WrongPassword if it does not match."""
    if not user.check_password(value):
        raise WrongPassword
    return value


class CurrentPasswordSerializer(serializers.Serializer):
    """Confirmation of an action with the current password."""

    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value: str) -> str:
        """Check the current password of the user."""
        return check_current_password(self.instance, value)


class EmailChangeSerializer(CurrentPasswordSerializer):
    """Change of the email address, confirmed with the password."""

    email = serializers.EmailField(max_length=254)

    def validate_email(self, value: str) -> str:
        """Check that no other user has the new address."""
        return unique_email(value, self.instance)

    def update(self, user: User, validated_data: dict) -> User:
        """Save the new email address."""
        user.email = validated_data['email']
        user.save(update_fields=['email'])
        return user

    def to_representation(self, user: User) -> dict:
        """Return the user like the user endpoint."""
        return UserSerializer(user).data


class PasswordChangeSerializer(serializers.Serializer):
    """Change of the password, confirmed with the current one."""

    current = serializers.CharField(write_only=True, trim_whitespace=False)
    next = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current(self, value: str) -> str:
        """Check the current password of the user."""
        return check_current_password(self.instance, value)

    def validate_next(self, value: str) -> str:
        """Check the new password against the rules."""
        password_validation.validate_password(value, self.instance)
        return value

    def update(self, user: User, validated_data: dict) -> User:
        """Save the new password."""
        user.set_password(validated_data['next'])
        user.save(update_fields=['password'])
        return user

    def to_representation(self, user: User) -> dict:
        """Return the user like the user endpoint."""
        return UserSerializer(user).data


class PasswordResetSerializer(serializers.Serializer):
    """Request of a password reset mail."""

    email = serializers.EmailField(max_length=254)

    def save(self) -> None:
        """Send the mail if an active user with a password exists."""
        email = UserManager.normalize_email(self.validated_data['email'])
        user = User.objects.filter(email=email, is_active=True).first()
        if user and user.has_usable_password():
            send_reset_mail(user)


def user_from_link(uid: str, token: str) -> User:
    """Return the user of a reset link or raise InvalidLink."""
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=pk, is_active=True)
    except ValueError, User.DoesNotExist:
        raise InvalidLink from None
    if not default_token_generator.check_token(user, token):
        raise InvalidLink
    return user


def check_password_rules(password: str, user: User) -> None:
    """Raise a field error if the password breaks the password rules."""
    try:
        password_validation.validate_password(password, user)
    except DjangoValidationError as error:
        raise serializers.ValidationError({'password': get_error_detail(error)}) from None


class PasswordResetConfirmSerializer(serializers.Serializer):
    """New password from a password reset link."""

    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        """Check the link and the new password."""
        user = user_from_link(attrs['uid'], attrs['token'])
        check_password_rules(attrs['password'], user)
        return {'user': user, 'password': attrs['password']}

    def save(self) -> User:
        """Save the new password and return the user."""
        user = self.validated_data['user']
        user.set_password(self.validated_data['password'])
        user.save(update_fields=['password'])
        return user


# Favorites
class FavoriteSerializer(serializers.ModelSerializer):
    """Favorite with the data needed to link to the command."""

    topic = serializers.CharField(source='entry.subtopic.topic.slug')
    subtopic = serializers.CharField(source='entry.subtopic.slug')
    slug = serializers.CharField(source='entry.slug')
    title = serializers.CharField(source='entry.title')

    class Meta:
        model = Favorite
        fields = ('topic', 'subtopic', 'slug', 'title')
        read_only_fields = fields


# Settings
class SettingsSerializer(serializers.ModelSerializer):
    """Settings and project values of the logged-in user."""

    project_values = serializers.DictField(
        child=serializers.CharField(max_length=PROJECT_VALUE_MAX_LENGTH, allow_blank=True)
    )

    class Meta:
        model = User
        fields = ('os', 'theme', 'language', 'project_values')

    def validate_project_values(self, values: dict[str, str]) -> dict[str, str]:
        """Reject unknown project value keys."""
        unknown = [key for key in values if key not in PROJECT_VALUE_FIELDS]
        if unknown:
            error = serializers.ErrorDetail('Unknown key.', code='unknown_key')
            raise serializers.ValidationError({key: [error] for key in unknown})
        return values

    def update(self, user: User, validated_data: dict) -> User:
        """Save the given project values and settings."""
        user.set_project_values(validated_data.pop('project_values', {}))
        return super().update(user, validated_data)
