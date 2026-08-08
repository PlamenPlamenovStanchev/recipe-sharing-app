"""Data access for eagerly loaded recipe records."""

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.enums import RecipeStatus
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_like import RecipeLike


def _recipe_load_options():
    """Return relationship options used by recipe API queries."""
    return (
        selectinload(Recipe.author),
        selectinload(Recipe.steps),
        selectinload(Recipe.recipe_ingredients).selectinload(
            RecipeIngredient.ingredient
        ),
    )


def _attach_like_metadata(
    recipes: list[Recipe], current_user_id: int | None = None
) -> None:
    """Attach aggregate like data without loading every like record."""
    recipe_ids = [recipe.id for recipe in recipes]
    if not recipe_ids:
        return

    count_statement = (
        db.select(RecipeLike.recipe_id, db.func.count(RecipeLike.id))
        .where(RecipeLike.recipe_id.in_(recipe_ids))
        .group_by(RecipeLike.recipe_id)
    )
    counts = dict(db.session.execute(count_statement).all())

    liked_recipe_ids: set[int] = set()
    if current_user_id is not None:
        liked_statement = db.select(RecipeLike.recipe_id).where(
            RecipeLike.recipe_id.in_(recipe_ids),
            RecipeLike.user_id == current_user_id,
        )
        liked_recipe_ids = set(db.session.scalars(liked_statement))

    for recipe in recipes:
        recipe.like_count = counts.get(recipe.id, 0)
        if current_user_id is not None:
            recipe.liked_by_current_user = recipe.id in liked_recipe_ids
        elif hasattr(recipe, "liked_by_current_user"):
            delattr(recipe, "liked_by_current_user")


def list_approved_recipes() -> list[Recipe]:
    """Return approved recipes with API relationships preloaded."""
    statement = (
        db.select(Recipe)
        .options(*_recipe_load_options())
        .where(Recipe.status == RecipeStatus.APPROVED)
        .order_by(Recipe.created_at.desc())
    )
    recipes = list(db.session.scalars(statement))
    _attach_like_metadata(recipes)
    return recipes


def get_recipe(
    recipe_id: int, current_user_id: int | None = None
) -> Recipe | None:
    """Return one recipe with API relationships preloaded."""
    statement = (
        db.select(Recipe)
        .options(*_recipe_load_options())
        .where(Recipe.id == recipe_id)
    )
    recipe = db.session.scalar(statement)
    if recipe is not None:
        _attach_like_metadata([recipe], current_user_id)
    return recipe
