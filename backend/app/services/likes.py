"""Business rules for liking and unliking approved recipes."""

from app.models.enums import RecipeStatus
from app.models.recipe_like import RecipeLike
from app.models.user import User
from app.repositories.likes import (
    DuplicateRecipeLikeError,
    count_recipe_likes,
    create_recipe_like,
    delete_recipe_like,
    get_user_recipe_like,
)
from app.repositories.recipes import get_recipe


class RecipeLikeNotFoundError(Exception):
    """Raised when a recipe or the current user's like is unavailable."""


class RecipeLikeConflictError(Exception):
    """Raised when the current user already likes a recipe."""


class RecipeLikeStatusError(Exception):
    """Raised when a recipe's state does not permit likes."""


def _get_approved_recipe(recipe_id: int):
    """Return an approved recipe or raise the appropriate service error."""
    recipe = get_recipe(recipe_id)
    if recipe is None:
        raise RecipeLikeNotFoundError("Recipe not found.")
    if recipe.status != RecipeStatus.APPROVED:
        raise RecipeLikeStatusError("Only approved recipes can be liked.")
    return recipe


def like_recipe(recipe_id: int, user: User) -> RecipeLike:
    """Create the current user's unique like for an approved recipe."""
    recipe = _get_approved_recipe(recipe_id)
    try:
        return create_recipe_like(recipe.id, user.id)
    except DuplicateRecipeLikeError as error:
        raise RecipeLikeConflictError(
            "You have already liked this recipe."
        ) from error


def unlike_recipe(recipe_id: int, user: User) -> None:
    """Remove the current user's like from an approved recipe."""
    recipe = _get_approved_recipe(recipe_id)
    like = get_user_recipe_like(recipe.id, user.id)
    if like is None:
        raise RecipeLikeNotFoundError("Like not found.")
    delete_recipe_like(like)


def get_recipe_like_count(recipe_id: int) -> int:
    """Return the public like count for an approved recipe."""
    recipe = _get_approved_recipe(recipe_id)
    return count_recipe_likes(recipe.id)
