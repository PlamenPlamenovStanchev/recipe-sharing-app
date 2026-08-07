"""Application configuration placeholders."""

import os


class Config:
    """Base configuration for the Flask application."""

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
