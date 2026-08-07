"""Factory for Ingredient model instances."""

import factory

from app.extensions import db
from app.models import Ingredient


class IngredientFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create persisted ingredients for model tests."""

    class Meta:
        model = Ingredient
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda number: f"Ingredient {number}")
