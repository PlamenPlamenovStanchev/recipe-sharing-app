"""Flask application package."""

from flask import Flask

from config import Config


def create_app(config_class: type[Config] = Config) -> Flask:
    """Create the Flask application instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    return app
