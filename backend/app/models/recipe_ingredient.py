"""Recipe-to-ingredient association model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.ingredient import Ingredient
    from app.models.recipe import Recipe


class RecipeIngredient(db.Model):
    """An ingredient and its measured use in a recipe."""

    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "position",
            name="uq_recipe_ingredients_recipe_position",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[str | None] = mapped_column(String(50))
    unit: Mapped[str | None] = mapped_column(String(50))
    position: Mapped[int] = mapped_column(nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    recipe: Mapped[Recipe] = relationship(back_populates="recipe_ingredients")
    ingredient: Mapped[Ingredient] = relationship(
        back_populates="recipe_ingredients"
    )
