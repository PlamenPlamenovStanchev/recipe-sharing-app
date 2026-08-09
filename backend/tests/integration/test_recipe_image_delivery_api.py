"""Integration coverage for private recipe image URLs in API responses."""

from unittest.mock import Mock, patch

from app.extensions import db
from app.models import RecipeStatus
from tests.factories import RecipeFactory


def test_recipe_without_image_serializes_null_image_url(app):
    """A recipe with no stored key exposes a predictable null image URL."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED, image_key=None)
        recipe_id = recipe.id
        db.session.commit()

    response = app.test_client().get(f"/recipes/{recipe_id}")

    assert response.status_code == 200
    assert response.get_json()["image_url"] is None


def test_recipe_detail_serializes_mocked_presigned_image_url(app):
    """The detail response includes a private URL without contacting AWS."""
    with app.app_context():
        recipe = RecipeFactory(
            status=RecipeStatus.APPROVED,
            image_key="recipes/3/private.jpg",
        )
        recipe_id = recipe.id
        db.session.commit()

    storage = Mock()
    storage.generate_image_url.return_value = "https://signed.example/detail"
    with patch(
        "app.services.recipe_serialization.S3RecipeImageStorage.from_app_config",
        return_value=storage,
    ) as storage_factory:
        response = app.test_client().get(f"/recipes/{recipe_id}")

    assert response.status_code == 200
    assert response.get_json()["image_url"] == "https://signed.example/detail"
    storage_factory.assert_called_once_with()
    storage.generate_image_url.assert_called_once_with("recipes/3/private.jpg")


def test_recipe_list_includes_mocked_image_urls_with_one_storage_client(app):
    """Lists add URLs while creating the storage client only once."""
    with app.app_context():
        RecipeFactory(status=RecipeStatus.APPROVED, image_key=None)
        recipe_with_image = RecipeFactory(
            status=RecipeStatus.APPROVED,
            image_key="recipes/7/private.webp",
        )
        recipe_with_image_id = recipe_with_image.id
        db.session.commit()

    storage = Mock()
    storage.generate_image_url.return_value = "https://signed.example/list"
    with patch(
        "app.services.recipe_serialization.S3RecipeImageStorage.from_app_config",
        return_value=storage,
    ) as storage_factory:
        response = app.test_client().get("/recipes")

    assert response.status_code == 200
    recipes_by_id = {recipe["id"]: recipe for recipe in response.get_json()}
    assert recipes_by_id[recipe_with_image_id]["image_url"] == (
        "https://signed.example/list"
    )
    assert (
        sum(recipe["image_url"] is None for recipe in recipes_by_id.values())
        == 1
    )
    storage_factory.assert_called_once_with()
    storage.generate_image_url.assert_called_once_with(
        "recipes/7/private.webp"
    )
