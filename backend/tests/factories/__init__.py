"""Factories used by the backend test suite."""

from tests.factories.comment import CommentFactory
from tests.factories.ingredient import IngredientFactory
from tests.factories.recipe import RecipeFactory
from tests.factories.user import UserFactory

__all__ = [
    "CommentFactory",
    "IngredientFactory",
    "RecipeFactory",
    "UserFactory",
]
