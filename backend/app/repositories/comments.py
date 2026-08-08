"""Data access for recipe comments."""

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.comment import Comment


def list_active_comments(recipe_id: int) -> list[Comment]:
    """Return non-deleted comments for a recipe, oldest first."""
    statement = (
        db.select(Comment)
        .options(selectinload(Comment.user))
        .where(
            Comment.recipe_id == recipe_id,
            Comment.is_deleted.is_(False),
        )
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    )
    return list(db.session.scalars(statement))


def get_active_comment(comment_id: int) -> Comment | None:
    """Return a non-deleted comment with its author preloaded."""
    statement = (
        db.select(Comment)
        .options(selectinload(Comment.user))
        .where(
            Comment.id == comment_id,
            Comment.is_deleted.is_(False),
        )
    )
    return db.session.scalar(statement)
