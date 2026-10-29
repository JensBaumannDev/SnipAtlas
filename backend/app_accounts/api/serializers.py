from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers

from app_accounts.models import (
    PROJECT_VALUE_FIELDS,
    PROJECT_VALUE_MAX_LENGTH,
    Favorite,
    User,
    UserManager,
)

from .exceptions import InvalidCredentials


class UserSerializer(serializers.ModelSerializer):
    since = serializers.DateField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'since', 'notify_by_mail', 'accent')
        read_only_fields = ('email',)


# Register
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value: str) -> str:
        email = UserManager.normalize_email(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email is taken.', code='unique')
        return email

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
