"""Flask application package."""

import os

from flask import Flask

from app.authorization import configure_jwt_error_handlers
from app.commands import seed_db
from app.extensions import api, db, jwt, migrate
from app.models import (  # noqa: F401
    Comment,
    Donation,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeLike,
    RecipeStep,
    User,
)
from app.resources.auth import LoginResource, RegisterResource
from app.resources.health import HealthResource
from config import CONFIG_BY_NAME

api.add_resource(HealthResource, "/health")
api.add_resource(RegisterResource, "/auth/register")
api.add_resource(LoginResource, "/auth/login")


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application instance."""
    selected_config = config_name or os.getenv("FLASK_ENV", "development")
    config_class = CONFIG_BY_NAME.get(selected_config.lower())

    if config_class is None:
        supported = ", ".join(CONFIG_BY_NAME)
        raise ValueError(
            f"Unsupported configuration '{selected_config}'. "
            f"Choose one of: {supported}."
        )

    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["APP_ENV"] = selected_config.lower()
    config_class.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db, compare_type=True)
    jwt.init_app(app)
    configure_jwt_error_handlers()
    api.init_app(app)
    app.cli.add_command(seed_db)

    return app
