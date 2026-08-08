"""Recipe API serialization with optional private image delivery."""

from collections.abc import Iterable

from app.models.recipe import Recipe
from app.schemas import RecipeOutputSchema
from app.services.storage import S3RecipeImageStorage


def serialize_recipe(
    recipe: Recipe,
    *,
    exclude: tuple[str, ...] = (),
    storage: S3RecipeImageStorage | None = None,
) -> dict:
    """Serialize one recipe and add its temporary private image URL."""
    payload = RecipeOutputSchema(exclude=exclude).dump(recipe)
    payload["image_url"] = (
        storage.generate_image_url(recipe.image_key)
        if recipe.image_key and storage is not None
        else None
    )
    return payload


def serialize_recipes(
    recipes: Iterable[Recipe],
    *,
    exclude: tuple[str, ...] = (),
) -> list[dict]:
    """Serialize recipes while constructing at most one S3 client per list."""
    recipe_list = list(recipes)
    storage = (
        S3RecipeImageStorage.from_app_config()
        if any(recipe.image_key for recipe in recipe_list)
        else None
    )
    return [
        serialize_recipe(recipe, exclude=exclude, storage=storage)
        for recipe in recipe_list
    ]
