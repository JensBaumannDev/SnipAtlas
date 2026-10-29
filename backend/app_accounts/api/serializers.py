from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers

from app_accounts.models import (
    PROJECT_VALUE_FIELDS,
    PROJECT_VALUE_MAX_LENGTH,
    Favorite,
    User,
    UserManager,
)

from .exceptions import InvalidCredentials, WrongPassword


class UserSerializer(serializers.ModelSerializer):
    since = serializers.DateField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'since', 'notify_by_mail', 'accent')
        read_only_fields = ('email',)


def unique_email(value: str, user: User | None = None) -> str:
    email = UserManager.normalize_email(value)
    taken = User.objects.filter(email=email)
    if user:
        taken = taken.exclude(pk=user.pk)
    if taken.exists():
        raise serializers.ValidationError('Email is taken.', code='unique')
    return email


# Register
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value: str) -> str:
        return unique_email(value)

    def validate_password(self, value: str) -> str:
        password_validation.validate_password(value, User(email=self.initial_data.get('email')))
        return value

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(validated_data['email'], validated_data['password'])

    def to_representation(self, user: User) -> dict:
        return UserSerializer(user).data


# Login
class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        request = self.context['request']
        user = authenticate(request, email=attrs['email'], password=attrs['password'])
        if user is None:
            raise InvalidCredentials
        return {'user': user}


# Account
def check_current_password(user: User, value: str) -> str:
    if not user.check_password(value):
        raise WrongPassword
    return value


class CurrentPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value: str) -> str:
        return check_current_password(self.instance, value)


class EmailChangeSerializer(CurrentPasswordSerializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value: str) -> str:
        return unique_email(value, self.instance)

    def update(self, user: User, validated_data: dict) -> User:
        user.email = validated_data['email']
        user.save(update_fields=['email'])
        return user

    def to_representation(self, user: User) -> dict:
        return UserSerializer(user).data


class PasswordChangeSerializer(serializers.Serializer):
    current = serializers.CharField(write_only=True, trim_whitespace=False)
    next = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current(self, value: str) -> str:
        return check_current_password(self.instance, value)

    def validate_next(self, value: str) -> str:
        password_validation.validate_password(value, self.instance)
        return value

    def update(self, user: User, validated_data: dict) -> User:
        user.set_password(validated_data['next'])
        user.save(update_fields=['password'])
        return user

    def to_representation(self, user: User) -> dict:
        return UserSerializer(user).data


# Favorites
class FavoriteSerializer(serializers.ModelSerializer):
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
    project_values = serializers.DictField(
        child=serializers.CharField(max_length=PROJECT_VALUE_MAX_LENGTH, allow_blank=True)
    )

    class Meta:
        model = User
        fields = ('os', 'theme', 'language', 'project_values')

    def validate_project_values(self, values: dict[str, str]) -> dict[str, str]:
        unknown = [key for key in values if key not in PROJECT_VALUE_FIELDS]
        if unknown:
            error = serializers.ErrorDetail('Unknown key.', code='unknown_key')
            raise serializers.ValidationError({key: [error] for key in unknown})
        return values

    def update(self, user: User, validated_data: dict) -> User:
        user.set_project_values(validated_data.pop('project_values', {}))
        return super().update(user, validated_data)
