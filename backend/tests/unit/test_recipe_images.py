"""Unit tests for recipe image business orchestration."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.models.enums import RecipeStatus, UserRole
from app.repositories.recipes import RecipeImagePersistenceError
from app.services.recipe_images import (
    RecipeImagePermissionError,
    replace_recipe_image,
)
from app.services.storage import ImageUploadError


def _recipe(**overrides):
    values = {
        "id": 12,
        "author_id": 3,
        "status": RecipeStatus.DRAFT,
        "image_key": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _user(**overrides):
    values = {"id": 3, "role": UserRole.USER}
    values.update(overrides)
    return SimpleNamespace(**values)


def test_owner_can_replace_image_and_old_object_is_deleted():
    """A successful DB update is followed by cleanup of the prior key."""
    recipe = _recipe(image_key="recipes/12/old.jpg")
    storage = Mock()
    storage.upload_recipe_image.return_value = "recipes/12/new.png"
    storage.generate_image_url.return_value = "https://example.test/new.png"

    with patch(
        "app.services.recipe_images.update_recipe_image_key"
    ) as update_key:
        result = replace_recipe_image(recipe, _user(), Mock(), storage)

    update_key.assert_called_once_with(recipe, "recipes/12/new.png")
    storage.delete_recipe_image.assert_called_once_with("recipes/12/old.jpg")
    assert result == (
        "recipes/12/new.png",
        "https://example.test/new.png",
    )


def test_unauthorized_owner_state_does_not_upload():
    """A normal owner cannot change an image after recipe submission."""
    storage = Mock()

    with pytest.raises(RecipeImagePermissionError):
        replace_recipe_image(
            _recipe(status=RecipeStatus.PENDING), _user(), Mock(), storage
        )

    storage.upload_recipe_image.assert_not_called()


@pytest.mark.parametrize("role", [UserRole.MODERATOR, UserRole.ADMIN])
def test_staff_can_replace_image_for_any_recipe(role):
    """Moderators and administrators bypass owner and status restrictions."""
    recipe = _recipe(author_id=99, status=RecipeStatus.APPROVED)
    storage = Mock()
    storage.upload_recipe_image.return_value = "recipes/12/new.webp"
    storage.generate_image_url.return_value = "https://example.test/new.webp"

    with patch("app.services.recipe_images.update_recipe_image_key"):
        replace_recipe_image(recipe, _user(role=role), Mock(), storage)

    storage.upload_recipe_image.assert_called_once()


def test_upload_failure_does_not_attempt_database_update():
    """A failed S3 upload leaves database persistence untouched."""
    storage = Mock()
    storage.upload_recipe_image.side_effect = ImageUploadError("failed")

    with patch(
        "app.services.recipe_images.update_recipe_image_key"
    ) as update_key:
        with pytest.raises(ImageUploadError):
            replace_recipe_image(_recipe(), _user(), Mock(), storage)

    update_key.assert_not_called()


def test_database_failure_cleans_up_newly_uploaded_object():
    """A new S3 object is removed when its key cannot be committed."""
    storage = Mock()
    storage.upload_recipe_image.return_value = "recipes/12/orphan.png"

    with patch(
        "app.services.recipe_images.update_recipe_image_key",
        side_effect=RecipeImagePersistenceError,
    ):
        with pytest.raises(RecipeImagePersistenceError):
            replace_recipe_image(_recipe(), _user(), Mock(), storage)

    storage.delete_recipe_image.assert_called_once_with(
        "recipes/12/orphan.png"
    )
