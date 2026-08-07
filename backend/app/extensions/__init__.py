"""Centralized, unbound Flask extension instances."""

from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
api = Api()
