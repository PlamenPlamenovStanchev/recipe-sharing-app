"""Business logic coordinating recipe images and S3 storage."""

from werkzeug.datastructures import FileStorage

from app.models.enums import RecipeStatus, UserRole
from app.models.recipe import Recipe
from app.models.user import User
from app.repositories.recipes import (
    RecipeImagePersistenceError,
    update_recipe_image_key,
)
from app.services.storage import ImageStorageError, S3RecipeImageStorage


class RecipeImagePermissionError(Exception):
    """Raised when a user cannot update a recipe image."""


def _may_update_image(recipe: Recipe, user: User) -> bool:
    """Return whether the current user may replace this recipe's image."""
    if user.role in {UserRole.MODERATOR, UserRole.ADMIN}:
        return True
    return recipe.author_id == user.id and recipe.status in {
        RecipeStatus.DRAFT,
        RecipeStatus.REJECTED,
    }


def replace_recipe_image(
    recipe: Recipe,
    user: User,
    uploaded_file: FileStorage,
    storage: S3RecipeImageStorage | None = None,
) -> tuple[str, str]:
    """Upload a new image, persist its key, and remove replaced objects."""
    if not _may_update_image(recipe, user):
        raise RecipeImagePermissionError

    storage = storage or S3RecipeImageStorage.from_app_config()
    previous_key = recipe.image_key
    new_key = storage.upload_recipe_image(recipe.id, uploaded_file)

    try:
        update_recipe_image_key(recipe, new_key)
    except RecipeImagePersistenceError:
        try:
            storage.delete_recipe_image(new_key)
        except ImageStorageError:
            pass
        raise

    if previous_key:
        try:
            storage.delete_recipe_image(previous_key)
        except ImageStorageError:
            pass

    return new_key, storage.generate_image_url(new_key)
