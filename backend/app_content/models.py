"""Models for all content shown in SnipAtlas."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

RESERVED_TOPIC_SLUG = 'debuggen'

# Frontend paths
AI_PATH = '/ki-coding'
COMMANDS_PATH = 'befehle'
CONCEPTS_PATH = 'grundlagen'
BLUEPRINTS_PATH = 'anleitungen'
ERRORS_PATH = 'fehler'

validate_hex_color = RegexValidator(r'^#[0-9a-fA-F]{6}$', code='invalid')
validate_clean_slug = RegexValidator(r'^[a-z0-9]+(-[a-z0-9]+)*$', code='invalid')


def validate_topic_slug(value: str) -> None:
    """Reject the slug reserved for the debug guides."""
    if value == RESERVED_TOPIC_SLUG:
        raise ValidationError(_('This slug is reserved.'), code='reserved')


class GroupArea(models.TextChoices):
    """Navigation area a topic group belongs to."""

    GENERAL = 'general', _('General areas')
    AI = 'ai', _('AI coding')


class Group(models.Model):
    """Group of topics in the sidebar, such as frontend or backend."""

    slug = models.SlugField(unique=True, validators=[validate_clean_slug], verbose_name=_('slug'))
    name = models.CharField(max_length=60, verbose_name=_('name'))
    area = models.CharField(
        max_length=20,
        choices=GroupArea.choices,
        default=GroupArea.GENERAL,
        verbose_name=_('area'),
    )
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('topic group')
        verbose_name_plural = _('topic groups')
        ordering = ('position', 'pk')
        constraints = [
            models.CheckConstraint(
                condition=models.Q(area__in=GroupArea.values), name='group_area_valid'
            ),
        ]

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

    def area_url(self, area: str) -> str:
        """Return the URL of the topic page in an area, under AI coding for AI topics."""
        prefix = AI_PATH if self.group.area == GroupArea.AI else ''
        return f'{prefix}/{area}/{self.slug}'


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

    def area_url(self, area: str) -> str:
        """Return the URL of the subtopic page in an area."""
        return f'{self.topic.area_url(area)}/{self.slug}'


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
    JSON = 'json', 'JSON'
    NGINX = 'nginx', 'nginx'
    YAML = 'yaml', 'YAML'
    DOCKERFILE = 'dockerfile', 'Dockerfile'


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

    url_area = ''

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

    def get_absolute_url(self) -> str:
        """Return the URL of the detail page in the frontend."""
        return f'{self.subtopic.area_url(self.url_area)}/{self.slug}'


class Entry(ContentItem):
    """Command or snippet to copy, optionally with separate Unix code."""

    url_area = COMMANDS_PATH
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

    url_area = CONCEPTS_PATH
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

    def get_absolute_url(self) -> str:
        """Return the URL of the error page in the frontend."""
        return f'{self.topic.area_url(ERRORS_PATH)}/{self.slug}'


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

    def get_absolute_url(self) -> str:
        """Return the page of a general guide, or the error page of its topic."""
        if self.topic is None:
            return f'/{ERRORS_PATH}/{RESERVED_TOPIC_SLUG}/{self.slug}'
        return self.topic.area_url(ERRORS_PATH)

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
    in_roadmap = models.BooleanField(default=False, verbose_name=_('short version of my project'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    objects = TopicQuerySet.as_manager()

    class Meta:
        verbose_name = _('guide')
        verbose_name_plural = _('guides')
        ordering = ('topic__position', 'topic_id', 'position', 'pk')
        constraints = [slug_constraint()]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        """Return the URL of the guide page in the frontend."""
        return f'{self.topic.area_url(BLUEPRINTS_PATH)}/{self.slug}'


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


# Roadmap
RESERVED_PHASE_SLUGS = ('neu', 'ordnerstruktur')
PATH_SEGMENT = r'\.?[A-Za-z0-9_@+-][A-Za-z0-9_.@+-]*'
FILE_PATTERN = rf'\A{PATH_SEGMENT}(/{PATH_SEGMENT})*\Z'
FOLDER_PATTERN = rf'\A{PATH_SEGMENT}(/{PATH_SEGMENT})*/\Z'
PATH_PATTERN = rf'\A{PATH_SEGMENT}(/{PATH_SEGMENT})*/?\Z'
PATH_MAX_LENGTH = 200

validate_path = RegexValidator(PATH_PATTERN, code='invalid')
validate_folder = RegexValidator(FOLDER_PATTERN, code='invalid')


def validate_phase_slug(value: str) -> None:
    """Reject the slugs used by the pages for a new project and the folder tree."""
    if value in RESERVED_PHASE_SLUGS:
        raise ValidationError(_('This slug is reserved.'), code='reserved')


def is_folder(path: str) -> bool:
    """Return whether a valid path points to a folder."""
    return bool(validate_folder.regex.search(path))


def choice_constraint(field: str, choices: type[models.TextChoices]) -> models.CheckConstraint:
    """Return a database constraint that only allows the given choices."""
    return models.CheckConstraint(
        condition=models.Q(**{f'{field}__in': choices.values}),
        name=f'%(class)s_{field}_valid',
    )


class BlockKind(models.TextChoices):
    """Kinds of building blocks a project is made of."""

    FRONTEND = 'frontend', _('Frontend')
    BACKEND = 'backend', _('Backend')
    EXTRA = 'extra', _('Extra')
    HOSTING = 'hosting', _('Hosting')


SINGLE_BLOCK_KINDS = (BlockKind.FRONTEND, BlockKind.BACKEND, BlockKind.HOSTING)


class BlockRequirement(models.TextChoices):
    """What a project needs before a block can be chosen."""

    ANY = 'any', _('No requirement')
    BACKEND = 'backend', _('Only with a backend')
    NO_BACKEND = 'no-backend', _('Only without a backend')


class ConditionRule(models.TextChoices):
    """How a condition uses its block."""

    REQUIRES = 'requires', _('must be chosen')
    EXCLUDES = 'excludes', _('must not be chosen')


class CodeKind(models.TextChoices):
    """What a code block of a roadmap step does."""

    COMMAND = 'command', _('Command')
    CREATE = 'create', _('Create file')
    CHANGE = 'change', _('Change file')


class PathChange(models.TextChoices):
    """How a step changes a path in the project."""

    NEW = 'new', _('new')
    CHANGED = 'changed', _('changed')
    REMOVED = 'removed', _('removed')


class RoadmapBlock(models.Model):
    """Building block a user can choose for a project, such as Angular or Docker."""

    slug = models.SlugField(
        max_length=40, unique=True, validators=[validate_clean_slug], verbose_name=_('slug')
    )
    name = models.CharField(max_length=60, verbose_name=_('name'))
    kind = models.CharField(max_length=20, choices=BlockKind.choices, verbose_name=_('kind'))
    requirement = models.CharField(
        max_length=20,
        choices=BlockRequirement.choices,
        default=BlockRequirement.ANY,
        verbose_name=_('requirement'),
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('topic'),
    )
    available = models.BooleanField(default=True, verbose_name=_('available'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('building block')
        verbose_name_plural = _('building blocks')
        ordering = ('position', 'pk')
        constraints = [
            slug_constraint(),
            choice_constraint('kind', BlockKind),
            choice_constraint('requirement', BlockRequirement),
        ]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def check_choice(cls, blocks: list[RoadmapBlock]) -> None:
        """Raise an error if the blocks do not make a possible project."""
        kinds = [block.kind for block in blocks]
        errors = [
            *unavailable_errors(blocks),
            *kind_errors(kinds),
            *requirement_errors(blocks, has_backend=BlockKind.BACKEND in kinds),
        ]
        if errors:
            raise ValidationError(errors)


def unavailable_errors(blocks: list[RoadmapBlock]) -> list[ValidationError]:
    """Return an error for each block that cannot be chosen yet."""
    message = _('%(block)s is not available yet.')
    return [
        ValidationError(message, code='unavailable', params={'block': block.name})
        for block in blocks
        if not block.available
    ]


def kind_errors(kinds: list[str]) -> list[ValidationError]:
    """Return errors for a missing frontend and backend or a kind chosen twice."""
    errors = []
    if BlockKind.FRONTEND not in kinds and BlockKind.BACKEND not in kinds:
        errors.append(ValidationError(_('Choose a frontend, a backend or both.'), code='empty'))
    message = _('Choose only one %(kind)s.')
    errors += [
        ValidationError(message, code='duplicate_kind', params={'kind': kind.label})
        for kind in SINGLE_BLOCK_KINDS
        if kinds.count(kind) > 1
    ]
    return errors


def requirement_errors(blocks: list[RoadmapBlock], *, has_backend: bool) -> list[ValidationError]:
    """Return an error for each block whose requirement on the backend is not met."""
    errors = []
    for block in blocks:
        params = {'block': block.name}
        if block.requirement == BlockRequirement.BACKEND and not has_backend:
            message = _('%(block)s needs a backend.')
            errors.append(ValidationError(message, code='needs_backend', params=params))
        if block.requirement == BlockRequirement.NO_BACKEND and has_backend:
            message = _('%(block)s only works without a backend.')
            errors.append(ValidationError(message, code='no_backend', params=params))
    return errors


class ConditionalMixin:
    """Mixin for roadmap parts that only belong to plans with certain blocks."""

    def applies_to(self, blocks: set[str]) -> bool:
        """Return whether the part belongs to a plan with the given block slugs."""
        return all(condition.is_met(blocks) for condition in self.conditions.all())


class RoadmapCondition(models.Model):
    """Rule that ties a roadmap part to a block that must or must not be chosen."""

    block = models.ForeignKey(
        RoadmapBlock, on_delete=models.PROTECT, related_name='+', verbose_name=_('building block')
    )
    rule = models.CharField(max_length=10, choices=ConditionRule.choices, verbose_name=_('rule'))

    class Meta:
        abstract = True
        verbose_name = _('condition')
        verbose_name_plural = _('conditions')
        ordering = ('block__position', 'pk')

    def __str__(self) -> str:
        return f'{self.block}: {self.get_rule_display()}'

    def is_met(self, blocks: set[str]) -> bool:
        """Return whether the chosen block slugs fulfil the rule."""
        return (self.block.slug in blocks) == (self.rule == ConditionRule.REQUIRES)


class RoadmapPhase(ConditionalMixin, models.Model):
    """Phase of the project roadmap, such as setting up the backend."""

    slug = models.SlugField(
        max_length=80,
        unique=True,
        validators=[validate_clean_slug, validate_phase_slug],
        verbose_name=_('slug'),
    )
    title = models.CharField(max_length=120, verbose_name=_('title'))
    summary = models.TextField(verbose_name=_('summary'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('roadmap phase')
        verbose_name_plural = _('roadmap phases')
        ordering = ('position', 'pk')
        constraints = [
            slug_constraint(),
            models.CheckConstraint(
                condition=~models.Q(slug__in=RESERVED_PHASE_SLUGS),
                name='roadmapphase_slug_not_reserved',
            ),
        ]

    def __str__(self) -> str:
        return self.title


class RoadmapPhaseCondition(RoadmapCondition):
    """Condition of a roadmap phase."""

    phase = models.ForeignKey(
        RoadmapPhase,
        on_delete=models.CASCADE,
        related_name='conditions',
        verbose_name=_('roadmap phase'),
    )

    class Meta(RoadmapCondition.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=('phase', 'block'), name='roadmapphasecondition_block_unique'
            ),
            choice_constraint('rule', ConditionRule),
        ]


class RoadmapStep(ConditionalMixin, models.Model):
    """Step of a roadmap phase with everything needed to do it."""

    phase = models.ForeignKey(
        RoadmapPhase,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name=_('roadmap phase'),
    )
    slug = models.SlugField(max_length=80, validators=[validate_clean_slug], verbose_name=_('slug'))
    title = models.CharField(max_length=120, verbose_name=_('title'))
    why = models.TextField(verbose_name=_('why'))
    folder = models.CharField(
        max_length=PATH_MAX_LENGTH,
        blank=True,
        validators=[validate_folder],
        verbose_name=_('folder'),
    )
    context = models.CharField(max_length=120, blank=True, verbose_name=_('context'))
    verification = models.TextField(verbose_name=_('verification'))
    note = models.TextField(blank=True, verbose_name=_('note'))
    errors = models.ManyToManyField(
        ErrorMessage, blank=True, related_name='+', verbose_name=_('error messages')
    )
    concepts = models.ManyToManyField(
        Concept, blank=True, related_name='+', verbose_name=_('concepts')
    )
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('roadmap step')
        verbose_name_plural = _('roadmap steps')
        ordering = ('position', 'pk')
        constraints = [
            models.UniqueConstraint(fields=('phase', 'slug'), name='roadmapstep_slug_unique'),
            slug_constraint(),
            models.CheckConstraint(
                condition=models.Q(folder='') | models.Q(folder__regex=FOLDER_PATTERN),
                name='roadmapstep_folder_valid',
            ),
        ]

    def __str__(self) -> str:
        return self.title


class RoadmapStepCondition(RoadmapCondition):
    """Condition of a roadmap step."""

    step = models.ForeignKey(
        RoadmapStep,
        on_delete=models.CASCADE,
        related_name='conditions',
        verbose_name=_('roadmap step'),
    )

    class Meta(RoadmapCondition.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=('step', 'block'), name='roadmapstepcondition_block_unique'
            ),
            choice_constraint('rule', ConditionRule),
        ]


class RoadmapCode(models.Model):
    """Command or file content of a roadmap step."""

    step = models.ForeignKey(
        RoadmapStep, on_delete=models.CASCADE, related_name='codes', verbose_name=_('roadmap step')
    )
    kind = models.CharField(max_length=10, choices=CodeKind.choices, verbose_name=_('kind'))
    path = models.CharField(
        max_length=PATH_MAX_LENGTH,
        blank=True,
        validators=[validate_path],
        verbose_name=_('file path'),
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
        constraints = [
            language_constraint(),
            models.CheckConstraint(
                condition=models.Q(kind=CodeKind.COMMAND, path='')
                | models.Q(kind__in=(CodeKind.CREATE, CodeKind.CHANGE), path__regex=FILE_PATTERN),
                name='roadmapcode_path_matches_kind',
            ),
        ]

    def __str__(self) -> str:
        return self.get_language_display()

    def clean(self) -> None:
        """Require a file path for files only and the German Unix code first."""
        super().clean()
        require_german(self, 'code_unix')
        self.check_path()

    def check_path(self) -> None:
        """Raise an error if the path does not fit the kind of code."""
        if self.kind == CodeKind.COMMAND and self.path:
            raise field_error('path', 'not_allowed', _('Commands have no file path.'))
        if self.kind in (CodeKind.CREATE, CodeKind.CHANGE) and not self.path:
            raise field_error('path', 'required', _('Enter the path of the file.'))
        if is_folder(self.path):
            raise field_error('path', 'folder', _('Enter a file, not a folder.'))

    @property
    def os_code(self) -> str | dict[str, str]:
        """Return the code, split by operating system if needed."""
        return split_os_code(self.code, self.code_unix)


class RoadmapPath(models.Model):
    """File or folder a roadmap step adds, changes or removes."""

    step = models.ForeignKey(
        RoadmapStep, on_delete=models.CASCADE, related_name='paths', verbose_name=_('roadmap step')
    )
    path = models.CharField(
        max_length=PATH_MAX_LENGTH, validators=[validate_path], verbose_name=_('path')
    )
    change = models.CharField(max_length=10, choices=PathChange.choices, verbose_name=_('change'))
    tracked = models.BooleanField(default=True, verbose_name=_('in Git'))
    explanation = models.TextField(verbose_name=_('explanation'))
    position = models.IntegerField(default=0, verbose_name=_('position'))

    class Meta:
        verbose_name = _('path')
        verbose_name_plural = _('paths')
        ordering = ('position', 'pk')
        constraints = [
            models.UniqueConstraint(fields=('step', 'path'), name='roadmappath_path_unique'),
            choice_constraint('change', PathChange),
            models.CheckConstraint(
                condition=models.Q(path__regex=PATH_PATTERN), name='roadmappath_path_valid'
            ),
        ]

    def __str__(self) -> str:
        return self.path
