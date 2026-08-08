"""Focused integration tests for recipe like endpoints."""

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import RecipeLike, RecipeStatus
from tests.factories import RecipeFactory, UserFactory


def _headers(user) -> dict[str, str]:
    """Return a valid authorization header for a persisted user."""
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_authenticated_user_can_like_approved_recipe(app):
    """A like is created for the current user and exposed in detail data."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        user = UserFactory()
        recipe_id, user_id = recipe.id, user.id
        headers = _headers(user)
        db.session.commit()

    client = app.test_client()
    response = client.post(f"/recipes/{recipe_id}/likes", headers=headers)
    detail = client.get(f"/recipes/{recipe_id}", headers=headers)
    public_detail = client.get(f"/recipes/{recipe_id}")

    assert response.status_code == 201
    assert detail.get_json()["like_count"] == 1
    assert detail.get_json()["liked_by_current_user"] is True
    assert "liked_by_current_user" not in public_detail.get_json()
    like = db.session.scalar(
        db.select(RecipeLike).where(
            RecipeLike.recipe_id == recipe_id,
            RecipeLike.user_id == user_id,
        )
    )
    assert like is not None


def test_duplicate_like_returns_conflict(app):
    """The same user cannot like one recipe more than once."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        user = UserFactory()
        recipe_id = recipe.id
        headers = _headers(user)
        db.session.commit()

    client = app.test_client()
    assert (
        client.post(f"/recipes/{recipe_id}/likes", headers=headers).status_code
        == 201
    )

    duplicate = client.post(f"/recipes/{recipe_id}/likes", headers=headers)

    assert duplicate.status_code == 409


def test_authenticated_user_can_unlike_recipe(app):
    """DELETE removes the current user's existing like."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        user = UserFactory()
        like = RecipeLike(recipe=recipe, user=user)
        db.session.add(like)
        recipe_id = recipe.id
        headers = _headers(user)
        db.session.commit()

    client = app.test_client()
    response = client.delete(f"/recipes/{recipe_id}/likes", headers=headers)
    missing = client.delete(f"/recipes/{recipe_id}/likes", headers=headers)

    assert response.status_code == 204
    assert missing.status_code == 404


def test_user_cannot_like_pending_recipe(app):
    """Likes are rejected unless the recipe is approved."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.PENDING)
        user = UserFactory()
        recipe_id = recipe.id
        headers = _headers(user)
        db.session.commit()

    response = app.test_client().post(
        f"/recipes/{recipe_id}/likes", headers=headers
    )

    assert response.status_code == 409


def test_public_like_count_and_recipe_output(app):
    """Public endpoints expose aggregate counts without a user-like flag."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        first_user = UserFactory()
        second_user = UserFactory()
        db.session.add_all(
            [
                RecipeLike(recipe=recipe, user=first_user),
                RecipeLike(recipe=recipe, user=second_user),
            ]
        )
        recipe_id = recipe.id
        db.session.commit()

    client = app.test_client()
    count_response = client.get(f"/recipes/{recipe_id}/likes")
    detail_response = client.get(f"/recipes/{recipe_id}")

    assert count_response.status_code == 200
    assert count_response.get_json() == {"count": 2}
    assert detail_response.get_json()["like_count"] == 2
    assert "liked_by_current_user" not in detail_response.get_json()
