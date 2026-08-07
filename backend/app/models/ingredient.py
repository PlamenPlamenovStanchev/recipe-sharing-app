"""Ingredient database model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.recipe_ingredient import RecipeIngredient


class Ingredient(db.Model):
    """A reusable ingredient that can be included in recipes."""

    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    recipe_ingredients: Mapped[list[RecipeIngredient]] = relationship(
        back_populates="ingredient",
        passive_deletes=True,
    )
