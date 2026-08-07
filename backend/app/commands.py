"""Custom Flask CLI commands."""

import os

import click
from flask import current_app

from app.extensions import db
from app.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeStatus,
    RecipeStep,
    User,
    UserRole,
)
from app.models.mixins import utc_now


def _seed_value(name: str, default: str) -> str:
    """Read a development-only seed value from the environment."""
    return os.getenv(name, default)


def _get_or_create_user(
    *,
    email: str,
    username: str,
    first_name: str,
    last_name: str,
    role: UserRole,
    password: str,
) -> User:
    """Return a user by email or create it with a hashed password."""
    user = db.session.scalar(db.select(User).where(User.email == email))

    if user:
        return user

    username_owner = db.session.scalar(
        db.select(User).where(User.username == username)
    )
    if username_owner:
        raise click.ClickException(
            f"Cannot seed '{email}': username '{username}' is already in use."
        )

    user = User(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        role=role,
        password_hash="",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def _get_or_create_ingredient(name: str) -> Ingredient:
    """Return an ingredient identified by name or create it."""
    ingredient = db.session.scalar(
        db.select(Ingredient).where(Ingredient.name == name)
    )
    if ingredient:
        return ingredient

    ingredient = Ingredient(name=name)
    db.session.add(ingredient)
    db.session.flush()
    return ingredient


def _add_recipe_details(
    recipe: Recipe,
    ingredient_rows: list[tuple[Ingredient, str, str, int]],
) -> None:
    """Add ordered ingredients and steps to a newly seeded recipe."""
    for ingredient, quantity, unit, position in ingredient_rows:
        recipe.recipe_ingredients.append(
            RecipeIngredient(
                ingredient=ingredient,
                quantity=quantity,
                unit=unit,
                position=position,
            )
        )

    recipe.steps.extend(
        [
            RecipeStep(step_number=1, instruction="Prepare all ingredients."),
            RecipeStep(
                step_number=2, instruction="Cook until ready to serve."
            ),
        ]
    )


def _get_or_create_recipe(
    *,
    title: str,
    slug: str,
    status: RecipeStatus,
    author: User,
    approved_by: User | None,
    ingredients: list[tuple[Ingredient, str, str, int]],
) -> Recipe:
    """Return a recipe identified by slug or create it with related records."""
    recipe = db.session.scalar(db.select(Recipe).where(Recipe.slug == slug))
    if recipe:
        return recipe

    now = utc_now()
    recipe = Recipe(
        title=title,
        slug=slug,
        description=(
            "Development seed recipe. Do not use as production content."
        ),
        status=status,
        author=author,
        submitted_at=now,
        approved_by=approved_by,
        approved_at=now if status == RecipeStatus.APPROVED else None,
    )
    _add_recipe_details(recipe, ingredients)
    db.session.add(recipe)
    return recipe


@click.command("seed-db")
def seed_db() -> None:
    """Create idempotent development-only seed data."""
    if current_app.config["APP_ENV"] != "development":
        raise click.ClickException("seed-db is available only in development.")

    click.secho(
        (
            "Development-only seed data: replace all default credentials "
            "before use."
        ),
        fg="yellow",
        err=True,
    )

    try:
        admin = _get_or_create_user(
            email=_seed_value("SEED_ADMIN_EMAIL", "admin@example.test"),
            username=_seed_value("SEED_ADMIN_USERNAME", "seed-admin"),
            first_name="Seed",
            last_name="Admin",
            role=UserRole.ADMIN,
            password=_seed_value("SEED_ADMIN_PASSWORD", "AdminPass1"),
        )
        moderator = _get_or_create_user(
            email=_seed_value(
                "SEED_MODERATOR_EMAIL", "moderator@example.test"
            ),
            username=_seed_value("SEED_MODERATOR_USERNAME", "seed-moderator"),
            first_name="Seed",
            last_name="Moderator",
            role=UserRole.MODERATOR,
            password=_seed_value("SEED_MODERATOR_PASSWORD", "ModeratorPass1"),
        )
        user = _get_or_create_user(
            email=_seed_value("SEED_USER_EMAIL", "user@example.test"),
            username=_seed_value("SEED_USER_USERNAME", "seed-user"),
            first_name="Seed",
            last_name="User",
            role=UserRole.USER,
            password=_seed_value("SEED_USER_PASSWORD", "UserPass1"),
        )

        flour = _get_or_create_ingredient("Flour")
        eggs = _get_or_create_ingredient("Eggs")
        milk = _get_or_create_ingredient("Milk")
        salt = _get_or_create_ingredient("Salt")

        ingredient_rows = [
            (flour, "200", "g", 1),
            (eggs, "2", "pieces", 2),
            (milk, "250", "ml", 3),
            (salt, "1", "pinch", 4),
        ]
        _get_or_create_recipe(
            title="Pending Seed Pancakes",
            slug="pending-seed-pancakes",
            status=RecipeStatus.PENDING,
            author=user,
            approved_by=None,
            ingredients=ingredient_rows,
        )
        _get_or_create_recipe(
            title="Approved Seed Pancakes",
            slug="approved-seed-pancakes",
            status=RecipeStatus.APPROVED,
            author=moderator,
            approved_by=admin,
            ingredients=ingredient_rows,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    click.echo(
        "Development seed data is ready. Running this command again is safe."
    )
