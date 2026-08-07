"""Validation rules for recipe fields."""

from marshmallow import ValidationError


def validate_recipe_title(title: str) -> None:
    """Require a meaningful recipe title within the database column limit."""
    if not 3 <= len(title) <= 255:
        raise ValidationError(
            "Recipe title must be between 3 and 255 characters."
        )
    if not title.strip():
        raise ValidationError("Recipe title cannot contain only whitespace.")
