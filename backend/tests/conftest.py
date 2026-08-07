"""Pytest fixtures for isolated PostgreSQL database tests."""

import os

import pytest

from app import create_app
from app.extensions import db


def _clear_database() -> None:
    """Delete all rows while preserving the schema in the test database."""
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


@pytest.fixture(scope="session")
def app():
    """Create an application backed only by TEST_DATABASE_URL."""
    test_database_url = os.getenv("TEST_DATABASE_URL")
    development_database_url = os.getenv("DATABASE_URL")

    if os.getenv("RUN_DATABASE_TESTS") != "1":
        raise RuntimeError(
            "Set RUN_DATABASE_TESTS=1 to explicitly authorize database tests."
        )
    if not test_database_url:
        raise RuntimeError("TEST_DATABASE_URL is required to run tests.")
    if test_database_url == development_database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must differ from DATABASE_URL for test safety."
        )

    application = create_app("testing")

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def clean_database(app):
    """Ensure every test starts and ends with an empty test database."""
    with app.app_context():
        _clear_database()
        yield
        db.session.rollback()
        _clear_database()
