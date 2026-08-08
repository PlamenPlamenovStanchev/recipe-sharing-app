"""Integration tests for the moderator pending-recipe queue."""

from datetime import datetime, timedelta, timezone

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import RecipeStatus, UserRole
from tests.factories import RecipeFactory, UserFactory


def _headers(user) -> dict[str, str]:
    """Return an authorization header for a persisted test user."""
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_pending_recipes_requires_authentication(app):
    """Anonymous requests cannot inspect the moderation queue."""
    response = app.test_client().get("/recipes/pending")

    assert response.status_code == 401


def test_normal_user_cannot_list_pending_recipes(app):
    """A normal authenticated user is forbidden from the queue."""
    user = UserFactory(role=UserRole.USER)
    db.session.commit()

    response = app.test_client().get(
        "/recipes/pending",
        headers=_headers(user),
    )

    assert response.status_code == 403


@pytest.mark.parametrize("role", [UserRole.MODERATOR, UserRole.ADMIN])
def test_staff_can_list_pending_recipes(app, role):
    """Moderators and administrators may inspect pending recipes."""
    staff = UserFactory(role=role)
    db.session.commit()

    response = app.test_client().get(
        "/recipes/pending",
        headers=_headers(staff),
    )

    assert response.status_code == 200
    assert response.get_json() == []


def test_pending_recipes_are_filtered_and_ordered_oldest_first(app):
    """Only pending recipes are returned by ascending submission time."""
    staff = UserFactory(role=UserRole.ADMIN)
    submitted_at = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)
    newer = RecipeFactory(
        status=RecipeStatus.PENDING,
        submitted_at=submitted_at + timedelta(hours=2),
    )
    older = RecipeFactory(
        status=RecipeStatus.PENDING,
        submitted_at=submitted_at,
    )
    RecipeFactory(
        status=RecipeStatus.APPROVED,
        submitted_at=submitted_at - timedelta(days=1),
    )
    db.session.commit()

    response = app.test_client().get(
        "/recipes/pending",
        headers=_headers(staff),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert [recipe["id"] for recipe in payload] == [older.id, newer.id]
    assert all(recipe["status"] == "PENDING" for recipe in payload)
    assert all(recipe["submitted_at"] for recipe in payload)
    assert {
        "id",
        "title",
        "slug",
        "author",
        "status",
        "submitted_at",
        "created_at",
        "image_url",
        "like_count",
    }.issubset(payload[0])
