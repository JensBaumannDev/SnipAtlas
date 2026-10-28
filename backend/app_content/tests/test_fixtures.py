import pytest
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models import Model

from app_content.models import GlossaryAlias, GlossaryTerm

FIXTURES = (
    'topics',
    'entries',
    'concepts',
    'errors',
    'debug_guides',
    'blueprints',
    'glossary',
    'news',
)
CONTENT_MODELS = list(apps.get_app_config('app_content').get_models())


@pytest.fixture
def content(db: None) -> None:
    call_command('loaddata', *FIXTURES, verbosity=0)


def clean_errors(model: type[Model]) -> dict[str, dict[str, list[str]]]:
    errors = {}
    for obj in model.objects.all():
        try:
            obj.full_clean()
        except ValidationError as error:
            errors[str(obj)] = error.message_dict
    return errors


def test_fixtures_fill_every_content_model(content: None) -> None:
    empty = [model.__name__ for model in CONTENT_MODELS if not model.objects.exists()]
    assert empty == []


def test_fixtures_pass_full_clean(content: None) -> None:
    errors = {model.__name__: clean_errors(model) for model in CONTENT_MODELS}
    assert {name: found for name, found in errors.items() if found} == {}


def test_glossary_names_are_unique_per_language(content: None) -> None:
    names = [term.term_de.lower() for term in GlossaryTerm.objects.all()]
    names += [alias.name.lower() for alias in GlossaryAlias.objects.filter(language='de')]
    assert sorted({name for name in names if names.count(name) > 1}) == []
