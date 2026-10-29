"""Models for all content shown in SnipAtlas."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

RESERVED_TOPIC_SLUG = 'debuggen'

validate_hex_color = RegexValidator(r'^#[0-9a-fA-F]{6}$', code='invalid')
validate_clean_slug = RegexValidator(r'^[a-z0-9]+(-[a-z0-9]+)*$', code='invalid')


def validate_topic_slug(value: str) -> None:
    """Reject the slug reserved for the debug guides."""
    if value == RESERVED_TOPIC_SLUG:
        raise ValidationError(_('This slug is reserved.'), code='reserved')


class Group(models.Model):
    """Group of topics in the sidebar, such as frontend or backend."""

    slug = models.SlugField(unique=True, validators=[validate_clean_slug], verbose_name=_('slug'))
    name = models.CharField(max_length=60, verbose_name=_('name'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('topic group')
        verbose_name_plural = _('topic groups')
        ordering = ('position', 'pk')

    def __str__(self) -> str:
        return self.name


class Topic(models.Model):
    """Topic such as Git or Angular with its own color."""

    group = models.ForeignKey(
        Group, on_delete=models.PROTECT, related_name='topics', verbose_name=_('topic group')
    )
    slug = models.SlugField(
        unique=True, validators=[validate_clean_slug, validate_topic_slug], verbose_name=_('slug')
    )
    name = models.CharField(max_length=60, verbose_name=_('name'))
    color = models.CharField(max_length=7, validators=[validate_hex_color], verbose_name=_('color'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('topic')
        verbose_name_plural = _('topics')
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
    """Section within a topic that groups commands and concepts."""

    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='subtopics', verbose_name=_('topic')
    )
    slug = models.SlugField(validators=[validate_clean_slug], verbose_name=_('slug'))
    name = models.CharField(max_length=80, verbose_name=_('name'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('subtopic')
        verbose_name_plural = _('subtopics')
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
    """Languages used for syntax highlighting."""

    TERMINAL = 'terminal', 'Terminal'
    PYTHON = 'python', 'Python'
    JAVASCRIPT = 'javascript', 'JavaScript'
    TYPESCRIPT = 'typescript', 'TypeScript'
    HTML = 'html', 'HTML'
    CSS = 'css', 'CSS'
    GITIGNORE = 'gitignore', '.gitignore'
    ENV = 'env', '.env'


def language_constraint(*, optional: bool = False) -> models.CheckConstraint:
    """Return a database constraint that only allows known languages."""
    values = [*CodeLanguage.values, ''] if optional else CodeLanguage.values
    return models.CheckConstraint(
        condition=models.Q(language__in=values), name='%(class)s_language_valid'
    )


def slug_constraint() -> models.CheckConstraint:
    """Return a database constraint that only allows clean slugs."""
    return models.CheckConstraint(
        condition=models.Q(slug__regex=validate_clean_slug.regex.pattern),
        name='%(class)s_slug_clean',
    )


def field_error(field: str, code: str, message: str) -> ValidationError:
    """Return a validation error for a single field."""
    return ValidationError({field: ValidationError(message, code=code)})


def require_german(obj: models.Model, field: str) -> None:
    """Raise an error if a field has an English text but no German one."""
    if getattr(obj, f'{field}_en') and not getattr(obj, f'{field}_de'):
        raise field_error(f'{field}_de', 'required', _('Add the German text first.'))


def split_os_code(code: str, code_unix: str) -> str | dict[str, str]:
    """Return the code, or Windows and Unix code if they differ."""
    if not code_unix:
        return code
    return {'win': code, 'unix': code_unix}


class TopicQuerySet(models.QuerySet):
    """Query set that filters content by topic slug."""

    topic_lookup = 'topic__slug'

    def for_topic(self, slug: str) -> TopicQuerySet:
        """Return the items of a topic, or none for a broken slug."""
        if not validate_clean_slug.regex.fullmatch(slug):
            return self.none()
        return self.filter(**{self.topic_lookup: slug})


class ContentItemQuerySet(TopicQuerySet):
    """Query set that filters content by the topic of its subtopic."""

    topic_lookup = 'subtopic__topic__slug'


class DebugGuideQuerySet(TopicQuerySet):
    """Query set for debug guides."""

    def general(self) -> DebugGuideQuerySet:
        """Return the general guides without a topic."""
        return self.filter(topic__isnull=True)


class ContentItem(models.Model):
    """Shared fields of commands and concepts."""

    subtopic = models.ForeignKey(
        Subtopic, on_delete=models.PROTECT, related_name='+', verbose_name=_('subtopic')
    )
    slug = models.SlugField(
        max_length=80, unique=True, validators=[validate_clean_slug], verbose_name=_('slug')
    )
    title = models.CharField(max_length=120, verbose_name=_('title'))
    language = models.CharField(
        max_length=20, choices=CodeLanguage.choices, verbose_name=_('code language')
    )
    code = models.TextField(verbose_name=_('code'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

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
    """Command or snippet to copy, optionally with separate Unix code."""

    description = models.TextField(verbose_name=_('description'))
    code_unix = models.TextField(blank=True, verbose_name=_('code for macOS/Linux'))

    class Meta(ContentItem.Meta):
        verbose_name = _('command')
        verbose_name_plural = _('commands')

    def clean(self) -> None:
        """Require the German Unix code before the English one."""
        super().clean()
        require_german(self, 'code_unix')

    @property
    def os_code(self) -> str | dict[str, str]:
        """Return the code, split by operating system if needed."""
        return split_os_code(self.code, self.code_unix)


class Concept(ContentItem):
    """Concept that explains the idea behind the code."""

    summary = models.TextField(verbose_name=_('summary'))
    explanation = models.TextField(verbose_name=_('explanation'))
    note = models.TextField(blank=True, verbose_name=_('note'))

    class Meta(ContentItem.Meta):
        verbose_name = _('concept')
        verbose_name_plural = _('concepts')


# Errors and debug guides
class OptionalCode(models.Model):
    """Shared optional code with its language."""

    language = models.CharField(
        max_length=20, choices=CodeLanguage.choices, blank=True, verbose_name=_('code language')
    )
    code = models.TextField(blank=True, verbose_name=_('code'))

    class Meta:
        abstract = True

    def clean(self) -> None:
        """Require German code and a language as soon as code is used."""
        super().clean()
        if (self.language or self.code_en) and not self.code_de:
            raise field_error('code_de', 'required', _('Add the German code.'))
        if self.code_de and not self.language:
            raise field_error('language', 'required', _('Choose the code language.'))


class ErrorMessage(OptionalCode):
    """Common error message of a topic with cause and solution."""

    topic = models.ForeignKey(
        Topic, on_delete=models.PROTECT, related_name='+', verbose_name=_('topic')
    )
    slug = models.SlugField(
        max_length=80, unique=True, validators=[validate_clean_slug], verbose_name=_('slug')
    )
    message = models.CharField(max_length=300, verbose_name=_('message'))
    meaning = models.TextField(verbose_name=_('meaning'))
    cause = models.TextField(verbose_name=_('cause'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    objects = TopicQuerySet.as_manager()

    class Meta:
        verbose_name = _('error message')
        verbose_name_plural = _('error messages')
        ordering = ('topic__position', 'topic_id', 'position', 'pk')
        constraints = [language_constraint(optional=True), slug_constraint()]

    def __str__(self) -> str:
        return self.message


class ErrorStep(models.Model):
    """Step towards solving an error message."""

    error = models.ForeignKey(
        ErrorMessage,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name=_('error message'),
    )
    text = models.TextField(verbose_name=_('text'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('solution step')
        verbose_name_plural = _('solution steps')
        ordering = ('position', 'pk')

    def __str__(self) -> str:
        return self.text


class DebugGuide(models.Model):
    """Guide for debugging, either general with a label or for one topic."""

    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('topic'),
    )
    slug = models.SlugField(
        max_length=80, unique=True, validators=[validate_clean_slug], verbose_name=_('slug')
    )
    label = models.CharField(max_length=30, blank=True, verbose_name=_('sidebar label'))
    title = models.CharField(max_length=120, verbose_name=_('title'))
    summary = models.TextField(verbose_name=_('summary'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    objects = DebugGuideQuerySet.as_manager()

    class Meta:
        verbose_name = _('debug guide')
        verbose_name_plural = _('debug guides')
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
        """Require a label for general guides and forbid it for topic guides."""
        super().clean()
        if self.topic_id is None and not self.label_de:
            raise field_error('label_de', 'required', _('General guides need a label.'))
        labels = [field for field in ('label_de', 'label_en') if getattr(self, field)]
        if self.topic_id is not None and labels:
            raise field_error(labels[0], 'invalid', _('Only general guides have a label.'))


class DebugGuideStep(OptionalCode):
    """Step of a debug guide with optional code."""

    guide = models.ForeignKey(
        DebugGuide, on_delete=models.CASCADE, related_name='steps', verbose_name=_('debug guide')
    )
    title = models.CharField(max_length=120, verbose_name=_('title'))
    text = models.TextField(verbose_name=_('text'))
    code_unix = models.TextField(blank=True, verbose_name=_('code for macOS/Linux'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('step')
        verbose_name_plural = _('steps')
        ordering = ('position', 'pk')
        constraints = [language_constraint(optional=True)]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        """Require the Windows code before the Unix code."""
        super().clean()
        if self.code_unix_de and not self.code_de:
            raise field_error('code_de', 'required', _('Add the Windows code first.'))
        require_german(self, 'code_unix')

    @property
    def os_code(self) -> str | dict[str, str]:
        """Return the code, split by operating system if needed."""
        return split_os_code(self.code, self.code_unix)


# Blueprints
class Blueprint(models.Model):
    """Step-by-step guide for a whole task, such as setting up a project."""

    topic = models.ForeignKey(
        Topic, on_delete=models.PROTECT, related_name='+', verbose_name=_('topic')
    )
    slug = models.SlugField(
        max_length=80, unique=True, validators=[validate_clean_slug], verbose_name=_('slug')
    )
    title = models.CharField(max_length=120, verbose_name=_('title'))
    summary = models.TextField(verbose_name=_('summary'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    objects = TopicQuerySet.as_manager()

    class Meta:
        verbose_name = _('guide')
        verbose_name_plural = _('guides')
        ordering = ('topic__position', 'topic_id', 'position', 'pk')
        constraints = [slug_constraint()]

    def __str__(self) -> str:
        return self.title


class BlueprintStep(models.Model):
    """Step of a blueprint that users can mark as done."""

    blueprint = models.ForeignKey(
        Blueprint, on_delete=models.CASCADE, related_name='steps', verbose_name=_('guide')
    )
    slug = models.SlugField(max_length=80, validators=[validate_clean_slug], verbose_name=_('slug'))
    title = models.CharField(max_length=120, verbose_name=_('title'))
    why = models.TextField(verbose_name=_('why'))
    note = models.TextField(blank=True, verbose_name=_('note'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('guide step')
        verbose_name_plural = _('guide steps')
        ordering = ('position', 'pk')
        constraints = [
            models.UniqueConstraint(
                fields=('blueprint', 'slug'), name='blueprintstep_slug_unique_per_blueprint'
            ),
            slug_constraint(),
        ]

    def __str__(self) -> str:
        return self.title


class BlueprintCode(models.Model):
    """Code block of a blueprint step."""

    step = models.ForeignKey(
        BlueprintStep, on_delete=models.CASCADE, related_name='codes', verbose_name=_('guide step')
    )
    language = models.CharField(
        max_length=20, choices=CodeLanguage.choices, verbose_name=_('code language')
    )
    code = models.TextField(verbose_name=_('code'))
    code_unix = models.TextField(blank=True, verbose_name=_('code for macOS/Linux'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('code block')
        verbose_name_plural = _('code blocks')
        ordering = ('position', 'pk')
        constraints = [language_constraint()]

    def __str__(self) -> str:
        return self.get_language_display()

    def clean(self) -> None:
        """Require the German Unix code before the English one."""
        super().clean()
        require_german(self, 'code_unix')

    @property
    def os_code(self) -> str | dict[str, str]:
        """Return the code, split by operating system if needed."""
        return split_os_code(self.code, self.code_unix)


# Glossary
class GlossaryTerm(models.Model):
    """Short definition of a term, optionally linked to a concept."""

    slug = models.SlugField(
        max_length=80, unique=True, validators=[validate_clean_slug], verbose_name=_('slug')
    )
    term = models.CharField(max_length=60, verbose_name=_('term'))
    definition = models.TextField(verbose_name=_('definition'))
    concept = models.ForeignKey(
        Concept,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('concept'),
    )

    class Meta:
        verbose_name = _('term')
        verbose_name_plural = _('terms')
        ordering = ('slug',)
        constraints = [slug_constraint()]

    def __str__(self) -> str:
        return self.term


class GlossaryAlias(models.Model):
    """Other name of a glossary term in one language."""

    term = models.ForeignKey(
        GlossaryTerm, on_delete=models.CASCADE, related_name='aliases', verbose_name=_('term')
    )
    language = models.CharField(
        max_length=2, choices=settings.LANGUAGES, default='de', verbose_name=_('language')
    )
    name = models.CharField(max_length=60, verbose_name=_('name'))

    class Meta:
        verbose_name = _('other name')
        verbose_name_plural = _('other names')
        ordering = ('name', 'pk')
        constraints = [
            models.UniqueConstraint(
                Lower('name'), 'language', name='glossaryalias_name_unique_per_language'
            ),
            models.CheckConstraint(
                condition=models.Q(language__in=[code for code, _ in settings.LANGUAGES]),
                name='glossaryalias_language_valid',
            ),
        ]

    def __str__(self) -> str:
        return self.name


# News
class NewsArea(models.TextChoices):
    """Areas a news item can point to."""

    COMMANDS = 'befehle', _('Commands')
    CONCEPTS = 'grundlagen', _('Concepts')
    BLUEPRINTS = 'anleitungen', _('Guides')
    ERRORS = 'fehler', _('Errors')


AREAS_WITH_SUBTOPICS = (NewsArea.COMMANDS, NewsArea.CONCEPTS)


class News(models.Model):
    """News item about new content on the start page."""

    date = models.DateField(verbose_name=_('date'))
    title = models.CharField(max_length=120, verbose_name=_('title'))
    area = models.CharField(max_length=20, choices=NewsArea.choices, verbose_name=_('area'))
    topic = models.ForeignKey(
        Topic, on_delete=models.PROTECT, related_name='+', verbose_name=_('topic')
    )
    subtopic = models.ForeignKey(
        Subtopic,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('subtopic'),
    )

    class Meta:
        verbose_name = _('news item')
        verbose_name_plural = _('news')
        ordering = ('-date', '-pk')
        constraints = [
            models.CheckConstraint(
                condition=models.Q(area__in=NewsArea.values), name='news_area_valid'
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        """Allow a subtopic only for commands and concepts of the same topic."""
        super().clean()
        if self.subtopic and self.area not in AREAS_WITH_SUBTOPICS:
            raise field_error(
                'subtopic', 'invalid', _('Only commands and concepts have subtopics.')
            )
        if self.subtopic and self.subtopic.topic_id != self.topic_id:
            raise field_error('subtopic', 'invalid', _('The subtopic belongs to another topic.'))

    @property
    def link(self) -> list[str]:
        """Return the URL parts of the area, topic and subtopic."""
        parts = [f'/{self.area}', self.topic.slug]
        return [*parts, self.subtopic.slug] if self.subtopic else parts
