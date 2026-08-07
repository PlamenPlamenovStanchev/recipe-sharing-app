"""Environment-based configuration for the Flask application."""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")


class BaseConfig:
    """Shared configuration values and initialization."""

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        """Load environment-dependent settings onto an application."""
        database_variable = (
            "TEST_DATABASE_URL" if cls.TESTING else "DATABASE_URL"
        )
        database_url = os.getenv(database_variable)

        if not database_url:
            raise RuntimeError(
                f"{database_variable} must be set to start the application."
            )

        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url


class DevelopmentConfig(BaseConfig):
    """Configuration used for local development."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Configuration used by automated tests."""

    TESTING = True


class ProductionConfig(BaseConfig):
    """Configuration used in production."""

    @classmethod
    def init_app(cls, app):
        """Require a secret key before starting a production application."""
        super().init_app(app)

        if not app.config["SECRET_KEY"]:
            raise RuntimeError("SECRET_KEY must be set in production.")


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
