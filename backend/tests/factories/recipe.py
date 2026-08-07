"""Factory for Recipe model instances."""

import factory

from app.extensions import db
from app.models import Recipe
from tests.factories.user import UserFactory


class RecipeFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create persisted recipes for model tests."""

    class Meta:
        model = Recipe
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "flush"

    author = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda number: f"Factory Recipe {number}")
    slug = factory.LazyAttribute(
        lambda recipe: recipe.title.lower().replace(" ", "-")
    )
    description = "Factory recipe description."
