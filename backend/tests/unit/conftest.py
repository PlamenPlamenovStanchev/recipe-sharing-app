"""Keep pure unit tests independent from the integration database fixture."""

import pytest


@pytest.fixture(autouse=True)
def clean_database():
    """Override the integration database cleanup fixture for unit tests."""
    yield
