"""Data-access repository package."""

from app.repositories.recipes import get_recipe, list_approved_recipes

__all__ = ["get_recipe", "list_approved_recipes"]
