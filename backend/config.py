"""Environment-based configuration for the Flask application."""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def normalize_database_url(database_url: str) -> str:
    """Normalize PostgreSQL URLs for SQLAlchemy's Psycopg driver."""
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url.removeprefix(
            "postgres://"
        )

    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix(
            "postgresql://"
        )

    return database_url


class BaseConfig:
    """Shared configuration values and initialization."""

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1_800,
        "pool_size": 5,
        "max_overflow": 5,
        "pool_timeout": 30,
    }
    TESTING = False
    DEBUG = False

    @classmethod
    def init_app(cls, app) -> None:
        """Load environment-dependent settings onto an application."""
        database_variable = (
            "TEST_DATABASE_URL" if cls.TESTING else "DATABASE_URL"
        )
        database_url = os.getenv(database_variable)

        if not database_url:
            raise RuntimeError(
                f"{database_variable} must be set to start the application."
            )

        if cls.TESTING and database_url == os.getenv("DATABASE_URL"):
            raise RuntimeError(
                "TEST_DATABASE_URL must be different from DATABASE_URL."
            )

        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
        app.config["JWT_SECRET_KEY"] = os.getenv(
            "JWT_SECRET_KEY", app.config["SECRET_KEY"]
        )
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
            minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
        )
        app.config["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
        app.config["AWS_SECRET_ACCESS_KEY"] = os.getenv(
            "AWS_SECRET_ACCESS_KEY"
        )
        app.config["AWS_REGION"] = os.getenv("AWS_REGION")
        app.config["AWS_S3_BUCKET_NAME"] = os.getenv("AWS_S3_BUCKET_NAME")
        app.config["AWS_SES_REGION"] = os.getenv("AWS_SES_REGION")
        app.config["AWS_SES_SENDER_EMAIL"] = os.getenv("AWS_SES_SENDER_EMAIL")
        app.config["PAYMENT_PROVIDER"] = os.getenv(
            "PAYMENT_PROVIDER", "wise"
        ).lower()
        app.config["WISE_API_TOKEN"] = os.getenv("WISE_API_TOKEN")
        app.config["WISE_PROFILE_ID"] = os.getenv("WISE_PROFILE_ID")
        app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(
            database_url
        )


class DevelopmentConfig(BaseConfig):
    """Configuration used for local development."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Configuration used by automated tests."""

    TESTING = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": 1,
        "max_overflow": 0,
    }


class ProductionConfig(BaseConfig):
    """Configuration used in production."""

    @classmethod
    def init_app(cls, app) -> None:
        """Require a secret key before starting a production application."""
        super().init_app(app)

        if not app.config["SECRET_KEY"]:
            raise RuntimeError("SECRET_KEY must be set in production.")
        if not os.getenv("JWT_SECRET_KEY"):
            raise RuntimeError("JWT_SECRET_KEY must be set in production.")


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
