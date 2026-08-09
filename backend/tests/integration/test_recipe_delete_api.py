"""Integration tests for current recipe deletion rules."""

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Recipe, RecipeStatus, UserRole
from tests.factories import RecipeFactory, UserFactory


def _headers(user) -> dict[str, str]:
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_owner_can_delete_own_draft_recipe(app):
    owner = UserFactory()
    recipe = RecipeFactory(author=owner, status=RecipeStatus.DRAFT)
    recipe_id = recipe.id
    headers = _headers(owner)
    db.session.commit()

    response = app.test_client().delete(
        f"/recipes/{recipe_id}", headers=headers
    )

    assert response.status_code == 204
    assert db.session.get(Recipe, recipe_id) is None


@pytest.mark.parametrize(
    "status", [RecipeStatus.PENDING, RecipeStatus.APPROVED]
)
def test_owner_cannot_delete_pending_or_approved_recipe(app, status):
    owner = UserFactory()
    recipe = RecipeFactory(author=owner, status=status)
    recipe_id = recipe.id
    headers = _headers(owner)
    db.session.commit()

    response = app.test_client().delete(
        f"/recipes/{recipe_id}", headers=headers
    )

    assert response.status_code == 403
    assert db.session.get(Recipe, recipe_id) is not None


def test_non_owner_cannot_delete_another_users_draft(app):
    recipe = RecipeFactory(status=RecipeStatus.DRAFT)
    other_user = UserFactory()
    recipe_id = recipe.id
    headers = _headers(other_user)
    db.session.commit()

    response = app.test_client().delete(
        f"/recipes/{recipe_id}", headers=headers
    )

    assert response.status_code == 403


@pytest.mark.parametrize("role", [UserRole.MODERATOR, UserRole.ADMIN])
def test_staff_can_delete_any_recipe(app, role):
    recipe = RecipeFactory(status=RecipeStatus.APPROVED)
    staff = UserFactory(role=role)
    recipe_id = recipe.id
    headers = _headers(staff)
    db.session.commit()

    response = app.test_client().delete(
        f"/recipes/{recipe_id}", headers=headers
    )

    assert response.status_code == 204
    assert db.session.get(Recipe, recipe_id) is None


@pytest.mark.parametrize(
    "status",
    [RecipeStatus.DRAFT, RecipeStatus.PENDING, RecipeStatus.REJECTED],
)
def test_public_cannot_read_unapproved_recipes(app, status):
    recipe = RecipeFactory(status=status)
    recipe_id = recipe.id
    db.session.commit()

    response = app.test_client().get(f"/recipes/{recipe_id}")

    assert response.status_code == 404
