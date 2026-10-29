"""Model for requests sent by users and guests."""

from datetime import date, timedelta

from django.conf import settings
from django.core.validators import MaxLengthValidator, MinLengthValidator, URLValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app_content.models import Topic

SUBJECT_LENGTH = 60
GUEST_TICKET_DAYS = 183

LIMITS = {
    'title': 120,
    'short': 20,
    'text': 2000,
    'note': 1000,
    'location': 200,
    'source': 300,
}


# Choices
class Kind(models.TextChoices):
    """Kinds of requests."""

    ENTRY = 'entry', _('New entry')
    IMPROVEMENT = 'improvement', _('Improvement')
    BUG = 'bug', _('Bug')


class Status(models.TextChoices):
    """Processing states of a request."""

    OPEN = 'open', _('Open')
    DONE = 'done', _('Done')


class EntryArea(models.TextChoices):
    """Areas a new entry can be suggested for."""

    COMMAND = 'command', _('Command')
    CONCEPT = 'concept', _('Concept')
    ERROR = 'error', _('Error message')


class ImprovementArea(models.TextChoices):
    """Areas an improvement can be about."""

    CONTENT = 'content', _('Content')
    USABILITY = 'usability', _('Usability')
    DESIGN = 'design', _('Design')
    FEATURE = 'feature', _('Feature')
    OTHER = 'other', _('Other')


class BugType(models.TextChoices):
    """Types of reported bugs."""

    WRONG = 'wrong', _('Wrong')
    OUTDATED = 'outdated', _('Outdated')
    BROKEN = 'broken', _('Broken')
    TYPO = 'typo', _('Typo')


# Fields
def text_field(verbose_name: str, max_length: int, *, min_length: int = 0) -> models.TextField:
    """Return an optional text field with length limits."""
    validators = [MaxLengthValidator(max_length)]
    if min_length:
        validators.append(MinLengthValidator(min_length))
    return models.TextField(verbose_name, max_length=max_length, blank=True, validators=validators)


def char_field(verbose_name: str, max_length: int) -> models.CharField:
    """Return an optional short text field."""
    return models.CharField(verbose_name, max_length=max_length, blank=True)


def shorten(text: str) -> str:
    """Return the text cut at a word boundary to fit the subject length."""
    if len(text) <= SUBJECT_LENGTH:
        return text
    return text[:SUBJECT_LENGTH].rsplit(' ', 1)[0] + '…'


# Constraints
def filled(*fields: str) -> Q:
    """Return a condition that requires all given fields to be filled."""
    condition = Q()
    for field in fields:
        condition &= ~Q(**{field: ''})
    return condition


def kind_constraint() -> models.CheckConstraint:
    """Return a database constraint that requires the fields of each kind."""
    entry = Q(kind=Kind.ENTRY, area__in=EntryArea.values, topic__isnull=False)
    improvement = Q(kind=Kind.IMPROVEMENT, area__in=ImprovementArea.values)
    bug = Q(kind=Kind.BUG, bug_type__in=BugType.values)
    return models.CheckConstraint(
        condition=(entry & filled('title', 'reason'))
        | (improvement & filled('idea'))
        | (bug & filled('location', 'problem')),
        name='suggestion_fields_match_kind',
    )


class Suggestion(models.Model):
    """Request from a user or guest, handled as a ticket in the admin."""

    kind = models.CharField(max_length=20, choices=Kind, verbose_name=_('kind'))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='suggestions',
        verbose_name=_('user'),
    )
    email = models.EmailField(blank=True, verbose_name=_('email'))
    status = models.CharField(
        max_length=10, choices=Status, default=Status.OPEN, verbose_name=_('status')
    )
    answer = models.TextField(blank=True, verbose_name=_('answer'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('received at'))
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name=_('answered at'))
    area = models.CharField(
        max_length=20,
        choices=[*EntryArea.choices, *ImprovementArea.choices],
        blank=True,
        verbose_name=_('area'),
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('topic'),
    )
    title = char_field(_('title'), LIMITS['title'])
    reason = text_field(_('reason'), LIMITS['note'], min_length=LIMITS['short'])
    example = text_field(_('example'), LIMITS['text'])
    source = models.CharField(
        max_length=LIMITS['source'],
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
        verbose_name=_('source'),
    )
    idea = text_field(_('idea'), LIMITS['text'], min_length=LIMITS['short'])
    benefit = text_field(_('benefit'), LIMITS['note'])
    bug_type = models.CharField(
        max_length=20, choices=BugType, blank=True, verbose_name=_('bug type')
    )
    location = char_field(_('location'), LIMITS['location'])
    problem = text_field(_('problem'), LIMITS['text'], min_length=LIMITS['short'])
    correction = text_field(_('correction'), LIMITS['note'])
    environment = char_field(_('environment'), LIMITS['location'])

    class Meta:
        verbose_name = _('request')
        verbose_name_plural = _('requests')
        ordering = ('-created_at', '-pk')
        constraints = [
            kind_constraint(),
            models.CheckConstraint(
                condition=Q(status__in=Status.values), name='suggestion_status_valid'
            ),
            models.CheckConstraint(
                condition=Q(user__isnull=False) | ~Q(email=''), name='suggestion_has_contact'
            ),
        ]

    def __str__(self) -> str:
        return self.subject

    def save(self, *args: object, **kwargs: object) -> None:
        """Mark the request as done when it gets its first answer."""
        if self.answer and not self.answered_at:
            self.status = Status.DONE
            self.answered_at = timezone.now()
        super().save(*args, **kwargs)

    @classmethod
    def delete_old_guest_tickets(cls) -> int:
        """Delete old done guest requests and return the count."""
        cutoff = timezone.now() - timedelta(days=GUEST_TICKET_DAYS)
        old = cls.objects.filter(user__isnull=True, status=Status.DONE, created_at__lt=cutoff)
        count, _ = old.delete()
        return count

    @property
    def subject(self) -> str:
        """Return a short subject that fits the kind of request."""
        if self.kind == Kind.ENTRY:
            return self.title
        if self.kind == Kind.BUG:
            return self.location
        return shorten(self.idea)

    @property
    def created_on(self) -> date:
        """Return the local date the request was sent."""
        return timezone.localdate(self.created_at)

    @property
    def contact_email(self) -> str:
        """Return the email of the user or the guest."""
        return self.user.email if self.user else self.email

    @property
    def notify_email(self) -> str:
        """Return the address for the answer mail, or empty if unwanted."""
        if self.user and not self.user.notify_by_mail:
            return ''
        return self.contact_email
