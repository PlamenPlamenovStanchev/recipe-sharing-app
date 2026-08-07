"""Recipe step database model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.recipe import Recipe


class RecipeStep(db.Model):
    """An ordered instruction within a recipe."""

    __tablename__ = "recipe_steps"
    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "step_number",
            name="uq_recipe_steps_recipe_step_number",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)

    recipe: Mapped[Recipe] = relationship(back_populates="steps")
