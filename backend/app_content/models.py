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
        constraints = [
            models.CheckConstraint(
                condition=models.Q(language__in=CodeLanguage.values),
                name='%(class)s_language_valid',
            ),
            models.CheckConstraint(
                condition=models.Q(slug__regex=validate_clean_slug.regex.pattern),
                name='%(class)s_slug_clean',
            ),
        ]

    def __str__(self) -> str:
        return self.title


class Entry(ContentItem):
    description = models.TextField()
    code_unix = models.TextField(blank=True)

    class Meta(ContentItem.Meta):
        verbose_name_plural = 'entries'

    def clean(self) -> None:
        super().clean()
        if self.code_unix_en and not self.code_unix_de:
            error = ValidationError('Add the German unix code first.', code='required')
            raise ValidationError({'code_unix_de': error})

    @property
    def os_code(self) -> str | dict[str, str]:
        if not self.code_unix:
            return self.code
        return {'win': self.code, 'unix': self.code_unix}


class Concept(ContentItem):
    summary = models.TextField()
    explanation = models.TextField()
    note = models.TextField(blank=True)
