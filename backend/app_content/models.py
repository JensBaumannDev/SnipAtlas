from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

RESERVED_TOPIC_SLUG = 'debuggen'

validate_hex_color = RegexValidator(r'^#[0-9a-fA-F]{6}$', code='invalid')
validate_clean_slug = RegexValidator(r'^[a-z0-9]+(-[a-z0-9]+)*$', code='invalid')


def validate_topic_slug(value: str) -> None:
    if value == RESERVED_TOPIC_SLUG:
        raise ValidationError('This slug is reserved.', code='reserved')


class Group(models.Model):
    slug = models.SlugField(unique=True, validators=[validate_clean_slug])
    name = models.CharField(max_length=60)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ('position', 'pk')

    def __str__(self) -> str:
        return self.name


class Topic(models.Model):
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name='topics')
    slug = models.SlugField(unique=True, validators=[validate_clean_slug, validate_topic_slug])
    name = models.CharField(max_length=60)
    color = models.CharField(max_length=7, validators=[validate_hex_color])
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ('position', 'pk')
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(slug__iexact=RESERVED_TOPIC_SLUG),
                name='topic_slug_not_reserved',
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Subtopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='subtopics')
    slug = models.SlugField(validators=[validate_clean_slug])
    name = models.CharField(max_length=80)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ('position', 'pk')
        constraints = [
            models.UniqueConstraint(
                fields=('topic', 'slug'), name='subtopic_slug_unique_per_topic'
            ),
        ]

    def __str__(self) -> str:
        return self.name


# Entries and concepts
class CodeLanguage(models.TextChoices):
    TERMINAL = 'terminal', 'Terminal'
    PYTHON = 'python', 'Python'
    JAVASCRIPT = 'javascript', 'JavaScript'
    TYPESCRIPT = 'typescript', 'TypeScript'
    HTML = 'html', 'HTML'
    CSS = 'css', 'CSS'
    GITIGNORE = 'gitignore', '.gitignore'
    ENV = 'env', '.env'


def language_constraint(*, optional: bool = False) -> models.CheckConstraint:
    values = [*CodeLanguage.values, ''] if optional else CodeLanguage.values
    return models.CheckConstraint(
        condition=models.Q(language__in=values), name='%(class)s_language_valid'
    )


def slug_constraint() -> models.CheckConstraint:
    return models.CheckConstraint(
        condition=models.Q(slug__regex=validate_clean_slug.regex.pattern),
        name='%(class)s_slug_clean',
    )


def field_error(field: str, code: str, message: str) -> ValidationError:
    return ValidationError({field: ValidationError(message, code=code)})


def require_german(obj: models.Model, field: str) -> None:
    if getattr(obj, f'{field}_en') and not getattr(obj, f'{field}_de'):
        raise field_error(f'{field}_de', 'required', 'Add the German text first.')


def split_os_code(code: str, code_unix: str) -> str | dict[str, str]:
    if not code_unix:
        return code
    return {'win': code, 'unix': code_unix}


class ContentItemQuerySet(models.QuerySet):
    def for_topic(self, slug: str) -> ContentItemQuerySet:
        if not validate_clean_slug.regex.fullmatch(slug):
            return self.none()
        return self.filter(subtopic__topic__slug=slug)


class ContentItem(models.Model):
    subtopic = models.ForeignKey(Subtopic, on_delete=models.PROTECT, related_name='+')
    slug = models.SlugField(max_length=80, unique=True, validators=[validate_clean_slug])
    title = models.CharField(max_length=120)
    language = models.CharField(max_length=20, choices=CodeLanguage.choices)
    code = models.TextField()
    position = models.IntegerField(default=0)

    objects = ContentItemQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = (
            'subtopic__topic__position',
            'subtopic__topic_id',
            'subtopic__position',
            'subtopic_id',
            'position',
            'pk',
        )
        constraints = [language_constraint(), slug_constraint()]

    def __str__(self) -> str:
        return self.title


class Entry(ContentItem):
    description = models.TextField()
    code_unix = models.TextField(blank=True)

    class Meta(ContentItem.Meta):
        verbose_name_plural = 'entries'

    def clean(self) -> None:
        super().clean()
        require_german(self, 'code_unix')

    @property
    def os_code(self) -> str | dict[str, str]:
        return split_os_code(self.code, self.code_unix)


class Concept(ContentItem):
    summary = models.TextField()
    explanation = models.TextField()
    note = models.TextField(blank=True)


# Errors and debug guides
class OptionalCode(models.Model):
    language = models.CharField(max_length=20, choices=CodeLanguage.choices, blank=True)
    code = models.TextField(blank=True)

    class Meta:
        abstract = True

    def clean(self) -> None:
        super().clean()
        if (self.language or self.code_en) and not self.code_de:
            raise field_error('code_de', 'required', 'Add the German code.')
        if self.code_de and not self.language:
            raise field_error('language', 'required', 'Choose the code language.')


class ErrorMessage(OptionalCode):
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name='+')
    slug = models.SlugField(max_length=80, unique=True, validators=[validate_clean_slug])
    message = models.CharField(max_length=300)
    meaning = models.TextField()
    cause = models.TextField()
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ('topic__position', 'topic_id', 'position', 'pk')
        constraints = [language_constraint(optional=True), slug_constraint()]

    def __str__(self) -> str:
        return self.message


class ErrorStep(models.Model):
    error = models.ForeignKey(ErrorMessage, on_delete=models.CASCADE, related_name='steps')
    text = models.TextField()
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ('position', 'pk')

    def __str__(self) -> str:
        return self.text


class DebugGuide(models.Model):
    topic = models.ForeignKey(
        Topic, on_delete=models.PROTECT, null=True, blank=True, related_name='+'
    )
    slug = models.SlugField(max_length=80, unique=True, validators=[validate_clean_slug])
    label = models.CharField(max_length=30, blank=True)
    title = models.CharField(max_length=120)
    summary = models.TextField()
    position = models.IntegerField(default=0)

    class Meta:
        ordering = (
            models.F('topic__position').asc(nulls_first=True),
            'topic_id',
            'position',
            'pk',
        )
        constraints = [slug_constraint()]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if self.topic_id is None and not self.label_de:
            raise field_error('label_de', 'required', 'General guides need a label.')
        labels = [field for field in ('label_de', 'label_en') if getattr(self, field)]
        if self.topic_id is not None and labels:
            raise field_error(labels[0], 'invalid', 'Only general guides have a label.')


class DebugGuideStep(OptionalCode):
    guide = models.ForeignKey(DebugGuide, on_delete=models.CASCADE, related_name='steps')
    title = models.CharField(max_length=120)
    text = models.TextField()
    code_unix = models.TextField(blank=True)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ('position', 'pk')
        constraints = [language_constraint(optional=True)]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if self.code_unix_de and not self.code_de:
            raise field_error('code_de', 'required', 'Add the Windows code first.')
        require_german(self, 'code_unix')

    @property
    def os_code(self) -> str | dict[str, str]:
        return split_os_code(self.code, self.code_unix)
