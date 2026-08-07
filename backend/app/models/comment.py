"""Recipe comment database model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.recipe import Recipe
    from app.models.user import User


class Comment(TimestampMixin, db.Model):
    """A user's comment on a recipe."""

    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_recipe_id", "recipe_id"),
        Index("ix_comments_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="comments")
    recipe: Mapped[Recipe] = relationship(back_populates="comments")
