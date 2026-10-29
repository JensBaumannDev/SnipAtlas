"""User model with settings, favorites and completed blueprint steps."""

from datetime import date

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app_content.models import BlueprintStep, Entry


class UserManager(BaseUserManager):
    """Manager that creates users with the email address as login."""

    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        """Return the email address trimmed and in lower case."""
        return (email or '').strip().lower()

    def get_by_natural_key(self, email: str | None) -> User:
        """Find a user by email address, ignoring case."""
        return super().get_by_natural_key(self.normalize_email(email))

    def create_user(
        self, email: str | None, password: str | None = None, **extra_fields: object
    ) -> User:
        """Create a user with a normalized email and a hashed password."""
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
        """Create a user with staff and superuser rights."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        for field in ('is_staff', 'is_superuser'):
            if extra_fields[field] is not True:
                raise ValueError(f'Superuser must have {field}=True.')
        return self.create_user(email, password, **extra_fields)


# Settings
class Accent(models.TextChoices):
    """Accent colors a user can choose."""

    BLUE = 'blue', _('Blue')
    TEAL = 'teal', _('Teal')
    RASPBERRY = 'raspberry', _('Raspberry')
    FUCHSIA = 'fuchsia', _('Fuchsia')


class OperatingSystem(models.TextChoices):
    """Operating systems for which code is shown."""

    WIN = 'win', 'Windows'
    UNIX = 'unix', 'macOS/Linux'


class Theme(models.TextChoices):
    """Color themes a user can choose."""

    LIGHT = 'light', _('Light')
    DARK = 'dark', _('Dark')
    SYSTEM = 'system', _('System')


class Language(models.TextChoices):
    """Interface languages a user can choose."""

    AUTO = 'auto', _('Automatic')
    DE = 'de', 'Deutsch'
    EN = 'en', 'English'


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
    """Return a database constraint that only allows the given choices."""
    return models.CheckConstraint(
        condition=models.Q(**{f'{field}__in': choices.values}),
        name=f'user_{field}_valid',
    )


def project_value_field(verbose_name: str) -> models.CharField:
    """Return an optional text field for a project value."""
    return models.CharField(verbose_name, max_length=PROJECT_VALUE_MAX_LENGTH, blank=True)


class User(AbstractUser):
    """User who logs in by email and keeps settings and project values."""

    username = None
    first_name = None
    last_name = None
    email = models.EmailField(unique=True, verbose_name=_('email address'))
    notify_by_mail = models.BooleanField(default=True, verbose_name=_('notify by mail'))
    accent = models.CharField(
        max_length=20, choices=Accent, default=Accent.BLUE, verbose_name=_('accent color')
    )
    os = models.CharField(
        max_length=10,
        choices=OperatingSystem,
        default=OperatingSystem.WIN,
        verbose_name=_('operating system'),
    )
    theme = models.CharField(
        max_length=10, choices=Theme, default=Theme.SYSTEM, verbose_name=_('theme')
    )
    language = models.CharField(
        max_length=10, choices=Language, default=Language.AUTO, verbose_name=_('language')
    )
    project_name = project_value_field(_('project name'))
    project_github_user = project_value_field(_('GitHub user'))
    project_repo = project_value_field(_('repository'))
    project_domain = project_value_field(_('domain'))
    project_server_user = project_value_field(_('server user'))
    project_server_ip = project_value_field(_('server IP'))

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta(AbstractUser.Meta):
        verbose_name = _('user')
        verbose_name_plural = _('users')
        constraints = [
            choice_constraint(field, choices) for field, choices in SETTING_CHOICES.items()
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def since(self) -> date:
        """Return the local date the user registered."""
        return timezone.localdate(self.date_joined)

    @property
    def project_values(self) -> dict[str, str]:
        """Return the project values keyed by their API name."""
        return {key: getattr(self, field) for key, field in PROJECT_VALUE_FIELDS.items()}

    def set_project_values(self, values: dict[str, str]) -> None:
        """Set the project values given by their API name."""
        for key, value in values.items():
            setattr(self, PROJECT_VALUE_FIELDS[key], value)

    def progress(self) -> dict[str, list[str]]:
        """Return the completed step slugs grouped by blueprint slug."""
        steps = self.completed_steps.values_list('step__blueprint__slug', 'step__slug')
        progress: dict[str, list[str]] = {}
        for blueprint, step in steps:
            progress.setdefault(blueprint, []).append(step)
        return progress

    def save(self, *args: object, **kwargs: object) -> None:
        """Normalize the email address and save the user."""
        self.email = UserManager.normalize_email(self.email)
        super().save(*args, **kwargs)


# User data
class Favorite(models.Model):
    """Command a user has marked as favorite."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites', verbose_name=_('user')
    )
    entry = models.ForeignKey(
        Entry, on_delete=models.CASCADE, related_name='+', verbose_name=_('command')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    class Meta:
        verbose_name = _('favorite')
        verbose_name_plural = _('favorites')
        ordering = ('created_at', 'pk')
        constraints = [
            models.UniqueConstraint(fields=('user', 'entry'), name='favorite_unique_per_user'),
        ]

    def __str__(self) -> str:
        return f'{self.user}: {self.entry}'


class CompletedStep(models.Model):
    """Blueprint step a user has marked as done."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='completed_steps', verbose_name=_('user')
    )
    step = models.ForeignKey(
        BlueprintStep, on_delete=models.CASCADE, related_name='+', verbose_name=_('guide step')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    class Meta:
        verbose_name = _('completed step')
        verbose_name_plural = _('completed steps')
        ordering = ('step__blueprint_id', 'step__position', 'step_id')
        constraints = [
            models.UniqueConstraint(fields=('user', 'step'), name='completedstep_unique_per_user'),
        ]

    def __str__(self) -> str:
        return f'{self.user}: {self.step}'
