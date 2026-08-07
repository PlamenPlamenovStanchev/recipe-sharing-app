"""Data access for eagerly loaded recipe records."""

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.enums import RecipeStatus
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient


def _recipe_load_options():
    """Return relationship options used by recipe API queries."""
    return (
        selectinload(Recipe.author),
        selectinload(Recipe.steps),
        selectinload(Recipe.recipe_ingredients).selectinload(
            RecipeIngredient.ingredient
        ),
    )


def list_approved_recipes() -> list[Recipe]:
    """Return approved recipes with API relationships preloaded."""
    statement = (
        db.select(Recipe)
        .options(*_recipe_load_options())
        .where(Recipe.status == RecipeStatus.APPROVED)
        .order_by(Recipe.created_at.desc())
    )
    return list(db.session.scalars(statement))


def get_recipe(recipe_id: int) -> Recipe | None:
    """Return one recipe with API relationships preloaded."""
    statement = (
        db.select(Recipe)
        .options(*_recipe_load_options())
        .where(Recipe.id == recipe_id)
    )
    return db.session.scalar(statement)
