"""Data access and persistence for recipe likes."""

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.recipe_like import RecipeLike


class DuplicateRecipeLikeError(Exception):
    """Raised when the database rejects a duplicate recipe like."""


def count_recipe_likes(recipe_id: int) -> int:
    """Return the number of likes belonging to a recipe."""
    statement = db.select(db.func.count(RecipeLike.id)).where(
        RecipeLike.recipe_id == recipe_id
    )
    return db.session.scalar(statement) or 0


def get_user_recipe_like(recipe_id: int, user_id: int) -> RecipeLike | None:
    """Return a user's like for a recipe, if it exists."""
    statement = db.select(RecipeLike).where(
        RecipeLike.recipe_id == recipe_id,
        RecipeLike.user_id == user_id,
    )
    return db.session.scalar(statement)


def create_recipe_like(recipe_id: int, user_id: int) -> RecipeLike:
    """Persist a like while safely enforcing the database uniqueness rule."""
    like = RecipeLike(recipe_id=recipe_id, user_id=user_id)
    db.session.add(like)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise DuplicateRecipeLikeError from error
    return like


def delete_recipe_like(like: RecipeLike) -> None:
    """Physically remove a user's existing recipe like."""
    db.session.delete(like)
    db.session.commit()
