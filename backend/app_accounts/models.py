from datetime import date

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


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


class Accent(models.TextChoices):
    BLUE = 'blue'
    TEAL = 'teal'
    RASPBERRY = 'raspberry'
    FUCHSIA = 'fuchsia'


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField(unique=True)
    notify_by_mail = models.BooleanField(default=True)
    accent = models.CharField(max_length=20, choices=Accent, default=Accent.BLUE)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email

    @property
    def since(self) -> date:
        return timezone.localdate(self.date_joined)

    def save(self, *args: object, **kwargs: object) -> None:
        self.email = UserManager.normalize_email(self.email)
        super().save(*args, **kwargs)
