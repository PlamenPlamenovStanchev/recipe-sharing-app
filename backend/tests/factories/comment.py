"""Factory for Comment model instances."""

import factory

from app.extensions import db
from app.models import Comment
from tests.factories.recipe import RecipeFactory
from tests.factories.user import UserFactory


class CommentFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Create persisted comments for integration tests."""

    class Meta:
        model = Comment
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "flush"

    user = factory.SubFactory(UserFactory)
    recipe = factory.SubFactory(RecipeFactory)
    content = factory.Sequence(lambda number: f"Comment {number}")
