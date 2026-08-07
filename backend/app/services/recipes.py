"""Business logic for recipe creation, updates, and deletion."""

import re
import unicodedata
from collections.abc import Iterable

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.enums import RecipeStatus, UserRole
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.recipe_step import RecipeStep
from app.models.user import User


class RecipeConflictError(Exception):
    """Raised when a unique recipe or ingredient constraint is violated."""


class RecipePermissionError(Exception):
    """Raised when a user cannot perform the requested recipe operation."""


class RecipeValidationError(Exception):
    """Raised when structured recipe data violates ordering rules."""


def _slugify(title: str) -> str:
    """Produce a URL-safe base slug from a recipe title."""
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug or "recipe"


def _unique_slug(title: str, recipe_id: int | None = None) -> str:
    """Return an unused slug, excluding ``recipe_id`` during an update."""
    base_slug = _slugify(title)
    candidate = base_slug
    suffix = 2

    while True:
        statement = db.select(Recipe.id).where(Recipe.slug == candidate)
        if recipe_id is not None:
            statement = statement.where(Recipe.id != recipe_id)
        if db.session.scalar(statement) is None:
            return candidate
        candidate = f"{base_slug}-{suffix}"
        suffix += 1


def _validate_unique_order(values: Iterable[dict], field: str) -> None:
    """Reject duplicate ingredient positions or recipe step numbers."""
    order_values = [value[field] for value in values]
    if len(order_values) != len(set(order_values)):
        raise RecipeValidationError(f"{field} values must be unique.")


def _ingredients_by_name(ingredient_data: list[dict]) -> dict[str, Ingredient]:
    """Load existing ingredients and prepare missing reusable ingredients."""
    names = {item["name"] for item in ingredient_data}
    statement = db.select(Ingredient).where(Ingredient.name.in_(names))
    ingredients = {
        ingredient.name: ingredient
        for ingredient in db.session.scalars(statement)
    }

    for name in names - ingredients.keys():
        ingredient = Ingredient(name=name)
        db.session.add(ingredient)
        ingredients[name] = ingredient
    return ingredients


def _replace_ingredients(recipe: Recipe, ingredient_data: list[dict]) -> None:
    """Replace recipe ingredient associations with validated input data."""
    _validate_unique_order(ingredient_data, "position")
    ingredients = _ingredients_by_name(ingredient_data)
    recipe.recipe_ingredients = []
    for item in ingredient_data:
        recipe_ingredient = RecipeIngredient(
            quantity=item.get("quantity"),
            unit=item.get("unit"),
            position=item["position"],
            notes=item.get("notes"),
        )
        recipe.recipe_ingredients.append(recipe_ingredient)
        recipe_ingredient.ingredient = ingredients[item["name"]]


def _replace_steps(recipe: Recipe, step_data: list[dict]) -> None:
    """Replace ordered recipe steps with validated input data."""
    _validate_unique_order(step_data, "step_number")
    recipe.steps = [
        RecipeStep(
            step_number=item["step_number"],
            instruction=item["instruction"],
        )
        for item in step_data
    ]


def _commit() -> None:
    """Commit a recipe transaction and normalize database conflicts."""
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise RecipeConflictError(
            "Recipe data conflicts with an existing record."
        ) from error


def _flush() -> None:
    """Flush child-row changes and normalize database conflicts."""
    try:
        db.session.flush()
    except IntegrityError as error:
        db.session.rollback()
        raise RecipeConflictError(
            "Recipe data conflicts with an existing record."
        ) from error


def create_recipe(author: User, recipe_data: dict) -> Recipe:
    """Create a draft recipe and all submitted ingredient and step records."""
    recipe = Recipe(
        title=recipe_data["title"],
        slug=_unique_slug(recipe_data["title"]),
        description=recipe_data["description"],
        author=author,
    )
    db.session.add(recipe)
    _replace_ingredients(recipe, recipe_data["ingredients"])
    _replace_steps(recipe, recipe_data["steps"])
    _commit()
    return recipe


def _may_update(recipe: Recipe, user: User) -> bool:
    """Return whether a user can update a recipe."""
    return user.role in {UserRole.MODERATOR, UserRole.ADMIN} or (
        recipe.author_id == user.id
    )


def update_recipe(recipe: Recipe, user: User, recipe_data: dict) -> Recipe:
    """Update permitted fields and replace submitted child collections."""
    if not _may_update(recipe, user):
        raise RecipePermissionError
    if not recipe_data:
        raise RecipeValidationError(
            "At least one recipe field must be provided."
        )
    if "ingredients" in recipe_data:
        _validate_unique_order(recipe_data["ingredients"], "position")
    if "steps" in recipe_data:
        _validate_unique_order(recipe_data["steps"], "step_number")

    if "title" in recipe_data and recipe_data["title"] != recipe.title:
        recipe.title = recipe_data["title"]
        recipe.slug = _unique_slug(recipe.title, recipe.id)
    if "description" in recipe_data:
        recipe.description = recipe_data["description"]
    if "ingredients" in recipe_data:
        recipe.recipe_ingredients.clear()
        _flush()
        _replace_ingredients(recipe, recipe_data["ingredients"])
    if "steps" in recipe_data:
        recipe.steps.clear()
        _flush()
        _replace_steps(recipe, recipe_data["steps"])

    _commit()
    return recipe


def delete_recipe(recipe: Recipe, user: User) -> None:
    """Delete a recipe when current role and status permit it."""
    is_staff = user.role in {UserRole.MODERATOR, UserRole.ADMIN}
    is_deletable_owner_recipe = (
        recipe.author_id == user.id
        and recipe.status in {RecipeStatus.DRAFT, RecipeStatus.REJECTED}
    )
    if not is_staff and not is_deletable_owner_recipe:
        raise RecipePermissionError

    db.session.delete(recipe)
    _commit()
