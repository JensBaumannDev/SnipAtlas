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
