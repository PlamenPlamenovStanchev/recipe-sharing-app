"""Integration tests for recipe update permissions by moderation status."""

import pytest

from app.models import RecipeStatus, UserRole
from app.services.recipes import RecipePermissionError, update_recipe
from tests.factories import RecipeFactory, UserFactory


@pytest.mark.parametrize("status", [RecipeStatus.DRAFT, RecipeStatus.REJECTED])
def test_owner_can_update_draft_or_rejected_recipe(status):
    """Owners may update recipes that are still editable by regular users."""
    owner = UserFactory(role=UserRole.USER)
    recipe = RecipeFactory(author=owner, status=status)

    updated_recipe = update_recipe(
        recipe, owner, {"description": "Updated description."}
    )

    assert updated_recipe.description == "Updated description."


@pytest.mark.parametrize(
    "status", [RecipeStatus.PENDING, RecipeStatus.APPROVED]
)
def test_owner_cannot_update_pending_or_approved_recipe(status):
    """Owners cannot edit recipes while they are undergoing or past review."""
    owner = UserFactory(role=UserRole.USER)
    recipe = RecipeFactory(author=owner, status=status)

    with pytest.raises(RecipePermissionError):
        update_recipe(recipe, owner, {"description": "Updated description."})


@pytest.mark.parametrize("role", [UserRole.MODERATOR, UserRole.ADMIN])
def test_staff_can_update_approved_recipe(role):
    """Moderators and administrators may update approved recipes."""
    author = UserFactory(role=UserRole.USER)
    staff_user = UserFactory(role=role)
    recipe = RecipeFactory(author=author, status=RecipeStatus.APPROVED)

    updated_recipe = update_recipe(
        recipe, staff_user, {"description": "Staff update."}
    )

    assert updated_recipe.description == "Staff update."
