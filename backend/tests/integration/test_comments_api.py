"""Focused integration tests for recipe comment endpoints."""

from datetime import timedelta

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Comment, RecipeStatus, UserRole
from app.models.mixins import utc_now
from tests.factories import CommentFactory, RecipeFactory, UserFactory


def _headers(user) -> dict[str, str]:
    """Return a valid authorization header for a persisted user."""
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_public_list_returns_active_comments_oldest_first_with_author(app):
    """Public listing is ordered and omits soft-deleted comments."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        author = UserFactory(username="comment_author")
        now = utc_now()
        newer = CommentFactory(
            recipe=recipe, user=author, content="Newer", created_at=now
        )
        older = CommentFactory(
            recipe=recipe,
            content="Older",
            created_at=now - timedelta(minutes=1),
        )
        CommentFactory(recipe=recipe, is_deleted=True)
        recipe_id, older_id, newer_id = recipe.id, older.id, newer.id
        author_id = author.id
        db.session.commit()

    response = app.test_client().get(f"/recipes/{recipe_id}/comments")

    assert response.status_code == 200
    payload = response.get_json()
    assert [item["id"] for item in payload] == [older_id, newer_id]
    assert payload[1]["author"] == {
        "id": author_id,
        "username": "comment_author",
        "first_name": "Factory",
        "last_name": "User",
    }


def test_anonymous_list_hides_unapproved_recipe(app):
    """Anonymous users cannot discover comments on an unapproved recipe."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.PENDING)
        recipe_id = recipe.id
        db.session.commit()

    response = app.test_client().get(f"/recipes/{recipe_id}/comments")
    assert response.status_code == 404


def test_authenticated_user_creates_trimmed_comment(app):
    """POST uses the current user and returns normalized comment data."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        user = UserFactory()
        recipe_id, user_id = recipe.id, user.id
        headers = _headers(user)
        db.session.commit()

    response = app.test_client().post(
        f"/recipes/{recipe_id}/comments",
        json={"content": "  Looks delicious!  "},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.get_json()["content"] == "Looks delicious!"
    comment = db.session.get(Comment, response.get_json()["id"])
    assert comment.user_id == user_id


def test_creation_requires_approved_recipe_and_valid_content(app):
    """POST rejects invalid text and comments on an unapproved recipe."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.DRAFT)
        user = UserFactory()
        recipe_id = recipe.id
        headers = _headers(user)
        db.session.commit()

    client = app.test_client()
    invalid = client.post(
        f"/recipes/{recipe_id}/comments",
        json={"content": "   a   "},
        headers=headers,
    )
    wrong_status = client.post(
        f"/recipes/{recipe_id}/comments",
        json={"content": "Valid comment"},
        headers=headers,
    )

    assert invalid.status_code == 400
    assert wrong_status.status_code == 409


def test_owner_can_edit_comment_but_another_user_cannot(app):
    """Only the owner or staff can update an active comment."""
    with app.app_context():
        owner = UserFactory()
        other_user = UserFactory()
        comment = CommentFactory(user=owner)
        comment_id = comment.id
        owner_headers = _headers(owner)
        other_headers = _headers(other_user)
        db.session.commit()

    client = app.test_client()
    denied = client.put(
        f"/comments/{comment_id}",
        json={"content": "Unauthorized edit"},
        headers=other_headers,
    )
    updated = client.put(
        f"/comments/{comment_id}",
        json={"content": "  Owner edit  "},
        headers=owner_headers,
    )

    assert denied.status_code == 403
    assert updated.status_code == 200
    assert updated.get_json()["content"] == "Owner edit"


def test_staff_can_edit_and_soft_delete_any_comment(app):
    """Moderators can manage others' comments without physical deletion."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        comment = CommentFactory(recipe=recipe)
        moderator = UserFactory(role=UserRole.MODERATOR)
        recipe_id, comment_id = recipe.id, comment.id
        headers = _headers(moderator)
        db.session.commit()

    client = app.test_client()
    updated = client.put(
        f"/comments/{comment_id}",
        json={"content": "Moderated content"},
        headers=headers,
    )
    deleted = client.delete(f"/comments/{comment_id}", headers=headers)
    listing = client.get(f"/recipes/{recipe_id}/comments")

    assert updated.status_code == 200
    assert deleted.status_code == 204
    assert listing.get_json() == []
    comment = db.session.get(Comment, comment_id)
    assert comment is not None
    assert comment.is_deleted is True


def test_comment_author_can_soft_delete_own_comment(app):
    """Authors can remove their comment without deleting its database row."""
    comment = CommentFactory()
    comment_id = comment.id
    headers = _headers(comment.user)
    db.session.commit()

    response = app.test_client().delete(
        f"/comments/{comment_id}", headers=headers
    )

    assert response.status_code == 204
    persisted = db.session.get(Comment, comment_id)
    assert persisted is not None
    assert persisted.is_deleted is True
