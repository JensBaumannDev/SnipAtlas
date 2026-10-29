from datetime import date

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from app_content.models import BlueprintStep, Entry


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        return (email or '').strip().lower()

    def get_by_natural_key(self, email: str | None) -> User:
        return super().get_by_natural_key(self.normalize_email(email))

    def create_user(
        self, email: str | None, password: str | None = None, **extra_fields: object
    ) -> User:
        email = self.normalize_email(email)
        if not email:
            raise ValueError('Email is required.')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str | None, password: str | None = None, **extra_fields: object
    ) -> User:
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        for field in ('is_staff', 'is_superuser'):
            if extra_fields[field] is not True:
                raise ValueError(f'Superuser must have {field}=True.')
        return self.create_user(email, password, **extra_fields)


# Settings
class Accent(models.TextChoices):
    BLUE = 'blue'
    TEAL = 'teal'
    RASPBERRY = 'raspberry'
    FUCHSIA = 'fuchsia'


class OperatingSystem(models.TextChoices):
    WIN = 'win'
    UNIX = 'unix'


class Theme(models.TextChoices):
    LIGHT = 'light'
    DARK = 'dark'
    SYSTEM = 'system'


class Language(models.TextChoices):
    AUTO = 'auto'
    DE = 'de'
    EN = 'en'


SETTING_CHOICES = {
    'accent': Accent,
    'os': OperatingSystem,
    'theme': Theme,
    'language': Language,
}

PROJECT_VALUE_MAX_LENGTH = 100

PROJECT_VALUE_FIELDS = {
    'project': 'project_name',
    'github_user': 'project_github_user',
    'repo': 'project_repo',
    'domain': 'project_domain',
    'server_user': 'project_server_user',
    'server_ip': 'project_server_ip',
}


def choice_constraint(field: str, choices: type[models.TextChoices]) -> models.CheckConstraint:
    return models.CheckConstraint(
        condition=models.Q(**{f'{field}__in': choices.values}),
        name=f'user_{field}_valid',
    )


def project_value_field() -> models.CharField:
    return models.CharField(max_length=PROJECT_VALUE_MAX_LENGTH, blank=True)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField(unique=True)
    notify_by_mail = models.BooleanField(default=True)
    accent = models.CharField(max_length=20, choices=Accent, default=Accent.BLUE)
    os = models.CharField(max_length=10, choices=OperatingSystem, default=OperatingSystem.WIN)
    theme = models.CharField(max_length=10, choices=Theme, default=Theme.SYSTEM)
    language = models.CharField(max_length=10, choices=Language, default=Language.AUTO)
    project_name = project_value_field()
    project_github_user = project_value_field()
    project_repo = project_value_field()
    project_domain = project_value_field()
    project_server_user = project_value_field()
    project_server_ip = project_value_field()

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta(AbstractUser.Meta):
        constraints = [
            choice_constraint(field, choices) for field, choices in SETTING_CHOICES.items()
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def since(self) -> date:
        return timezone.localdate(self.date_joined)

    @property
    def project_values(self) -> dict[str, str]:
        return {key: getattr(self, field) for key, field in PROJECT_VALUE_FIELDS.items()}

    def set_project_values(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            setattr(self, PROJECT_VALUE_FIELDS[key], value)

    def progress(self) -> dict[str, list[str]]:
        steps = self.completed_steps.values_list('step__blueprint__slug', 'step__slug')
        progress: dict[str, list[str]] = {}
        for blueprint, step in steps:
            progress.setdefault(blueprint, []).append(step)
        return progress

    def save(self, *args: object, **kwargs: object) -> None:
        self.email = UserManager.normalize_email(self.email)
        super().save(*args, **kwargs)


# User data
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'pk')
        constraints = [
            models.UniqueConstraint(fields=('user', 'entry'), name='favorite_unique_per_user'),
        ]

    def __str__(self) -> str:
        return f'{self.user}: {self.entry}'


class CompletedStep(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_steps')
    step = models.ForeignKey(BlueprintStep, on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('step__blueprint_id', 'step__position', 'step_id')
        constraints = [
            models.UniqueConstraint(fields=('user', 'step'), name='completedstep_unique_per_user'),
        ]

    def __str__(self) -> str:
        return f'{self.user}: {self.step}'
