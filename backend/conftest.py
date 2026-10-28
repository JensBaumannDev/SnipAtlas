import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    cache.clear()
