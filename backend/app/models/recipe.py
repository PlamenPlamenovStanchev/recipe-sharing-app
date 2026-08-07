"""Recipe database model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import RecipeStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.donation import Donation
    from app.models.recipe_ingredient import RecipeIngredient
    from app.models.recipe_like import RecipeLike
    from app.models.recipe_step import RecipeStep
    from app.models.user import User


class Recipe(TimestampMixin, db.Model):
    """A recipe submitted by a user."""

    __tablename__ = "recipes"
    __table_args__ = (
        Index("ix_recipes_status", "status"),
        Index("ix_recipes_author_id", "author_id"),
        Index("ix_recipes_created_at", "created_at"),
        Index("ix_recipes_approved_at", "approved_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_key: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[RecipeStatus] = mapped_column(
        Enum(RecipeStatus, name="recipe_status"),
        default=RecipeStatus.DRAFT,
        nullable=False,
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    author: Mapped[User] = relationship(
        "User",
        foreign_keys=[author_id],
        back_populates="authored_recipes",
    )
    approved_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[approved_by_id],
        back_populates="approved_recipes",
    )
    steps: Mapped[list[RecipeStep]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecipeStep.step_number",
    )
    recipe_ingredients: Mapped[list[RecipeIngredient]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecipeIngredient.position",
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    likes: Mapped[list[RecipeLike]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    donations: Mapped[list[Donation]] = relationship(
        back_populates="recipe",
        passive_deletes=True,
    )
