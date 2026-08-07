"""Recipe like database model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import utc_now

if TYPE_CHECKING:
    from app.models.recipe import Recipe
    from app.models.user import User


class RecipeLike(db.Model):
    """A single user's endorsement of a recipe."""

    __tablename__ = "recipe_likes"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "recipe_id",
            name="uq_recipe_likes_user_recipe",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="recipe_likes")
    recipe: Mapped[Recipe] = relationship(back_populates="likes")
