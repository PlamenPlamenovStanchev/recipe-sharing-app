"""Pytest fixtures for isolated database-backed API tests."""

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
def app(tmp_path_factory):
    """Create an app using an explicit test DB or a disposable SQLite DB."""
    test_database_url = os.getenv("TEST_DATABASE_URL")
    development_database_url = os.getenv("DATABASE_URL")
    use_explicit_database = os.getenv("RUN_DATABASE_TESTS") == "1"

    if use_explicit_database:
        if not test_database_url:
            raise RuntimeError("TEST_DATABASE_URL is required to run tests.")
        if test_database_url == development_database_url:
            raise RuntimeError(
                "TEST_DATABASE_URL must differ from DATABASE_URL "
                "for test safety."
            )
    else:
        database_path = tmp_path_factory.mktemp("database") / "test.sqlite"
        test_database_url = f"sqlite:///{database_path.as_posix()}"

    previous_test_database_url = os.environ.get("TEST_DATABASE_URL")
    os.environ["TEST_DATABASE_URL"] = test_database_url

    application = create_app("testing")
    application.config.update(
        SECRET_KEY="test-only-secret-key-at-least-32-bytes",
        JWT_SECRET_KEY="test-only-jwt-key-at-least-32-bytes",
        AWS_ACCESS_KEY_ID=None,
        AWS_SECRET_ACCESS_KEY=None,
        AWS_REGION=None,
        AWS_S3_BUCKET_NAME=None,
        AWS_SES_REGION=None,
        AWS_SES_SENDER_EMAIL=None,
        WISE_API_TOKEN=None,
        WISE_PROFILE_ID=None,
    )

    try:
        with application.app_context():
            db.create_all()
            yield application
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
    finally:
        if previous_test_database_url is None:
            os.environ.pop("TEST_DATABASE_URL", None)
        else:
            os.environ["TEST_DATABASE_URL"] = previous_test_database_url


@pytest.fixture(autouse=True)
def clean_database(app):
    """Ensure every test starts and ends with an empty test database."""
    with app.app_context():
        _clear_database()
        yield
        db.session.rollback()
        _clear_database()
