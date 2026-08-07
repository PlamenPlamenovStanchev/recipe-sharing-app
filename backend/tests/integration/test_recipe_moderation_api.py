"""Integration tests for the recipe moderation API workflow."""

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Recipe, UserRole
from tests.factories import UserFactory


def _register_and_login(client, identity: str) -> dict[str, str]:
    """Register a normal user through the API and return its JWT header."""
    registration = {
        "email": f"{identity}@example.test",
        "username": identity,
        "password": "Password1",
        "first_name": "Recipe",
        "last_name": "Author",
    }
    response = client.post("/auth/register", json=registration)
    assert response.status_code == 201

    response = client.post(
        "/auth/login",
        json={"email": registration["email"], "password": "Password1"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}


def _staff_headers(app, role: UserRole) -> tuple[dict[str, str], int]:
    """Create a moderator or administrator for an API request."""
    with app.app_context():
        staff_user = UserFactory(role=role)
        staff_user_id = staff_user.id
        db.session.commit()
        token = create_access_token(
            identity=str(staff_user_id),
            additional_claims={"role": UserRole.USER.value},
        )
    return {"Authorization": f"Bearer {token}"}, staff_user_id


def _recipe_payload(title: str) -> dict:
    """Build valid recipe input accepted by the recipe creation endpoint."""
    return {
        "title": title,
        "description": "A recipe prepared for moderation.",
        "ingredients": [{"name": "Flour", "position": 1}],
        "steps": [{"step_number": 1, "instruction": "Mix ingredients."}],
    }


def _create_recipe(client, headers: dict[str, str], title: str) -> int:
    """Create a draft recipe through the authenticated API."""
    response = client.post(
        "/recipes", json=_recipe_payload(title), headers=headers
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def _submit_recipe(client, recipe_id: int, headers: dict[str, str]) -> None:
    """Submit a recipe and assert its transition to pending."""
    response = client.post(f"/recipes/{recipe_id}/submit", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["status"] == "PENDING"


def test_user_can_register_login_and_create_recipe(app):
    """Registration, login, and authenticated draft creation work together."""
    client = app.test_client()
    headers = _register_and_login(client, "new_recipe_author")

    response = client.post(
        "/recipes",
        json=_recipe_payload("Registered User Recipe"),
        headers=headers,
    )

    assert response.status_code == 201
    assert response.get_json()["status"] == "DRAFT"


def test_public_user_cannot_see_pending_recipe(app):
    """Public recipe reads hide content awaiting moderation."""
    client = app.test_client()
    headers = _register_and_login(client, "pending_author")
    recipe_id = _create_recipe(client, headers, "Pending Recipe")
    _submit_recipe(client, recipe_id, headers)

    assert client.get(f"/recipes/{recipe_id}").status_code == 404


def test_public_user_can_see_approved_recipe(app):
    """Approved recipes become publicly accessible."""
    client = app.test_client()
    author_headers = _register_and_login(client, "approved_author")
    recipe_id = _create_recipe(client, author_headers, "Approved Recipe")
    _submit_recipe(client, recipe_id, author_headers)
    moderator_headers, _ = _staff_headers(app, UserRole.MODERATOR)

    approval = client.post(
        f"/recipes/{recipe_id}/approve", headers=moderator_headers
    )
    public_read = client.get(f"/recipes/{recipe_id}")

    assert approval.status_code == 200
    assert public_read.status_code == 200
    assert public_read.get_json()["status"] == "APPROVED"


def test_author_can_submit_own_recipe(app):
    """An author can submit an eligible draft for moderation."""
    client = app.test_client()
    headers = _register_and_login(client, "submit_author")
    recipe_id = _create_recipe(client, headers, "Submission Recipe")

    response = client.post(f"/recipes/{recipe_id}/submit", headers=headers)

    assert response.status_code == 200
    assert response.get_json()["status"] == "PENDING"


def test_moderator_can_approve_pending_recipe(app):
    """A moderator can approve a pending recipe and records are updated."""
    client = app.test_client()
    author_headers = _register_and_login(client, "moderated_author")
    recipe_id = _create_recipe(client, author_headers, "Moderated Recipe")
    _submit_recipe(client, recipe_id, author_headers)
    moderator_headers, moderator_id = _staff_headers(app, UserRole.MODERATOR)

    response = client.post(
        f"/recipes/{recipe_id}/approve", headers=moderator_headers
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "APPROVED"
    with app.app_context():
        recipe = db.session.get(Recipe, recipe_id)
        assert recipe.approved_by_id == moderator_id
        assert recipe.approved_at is not None
        assert recipe.rejected_at is None
        assert recipe.rejection_reason is None


def test_normal_user_cannot_approve_recipe(app):
    """A regular user cannot call the staff-only approval endpoint."""
    client = app.test_client()
    author_headers = _register_and_login(client, "nonstaff_author")
    recipe_id = _create_recipe(client, author_headers, "Nonstaff Approval")
    _submit_recipe(client, recipe_id, author_headers)

    response = client.post(
        f"/recipes/{recipe_id}/approve", headers=author_headers
    )

    assert response.status_code == 403


def test_moderator_can_reject_pending_recipe(app):
    """A moderator can reject a pending recipe with a valid reason."""
    client = app.test_client()
    author_headers = _register_and_login(client, "rejected_author")
    recipe_id = _create_recipe(client, author_headers, "Rejected Recipe")
    _submit_recipe(client, recipe_id, author_headers)
    moderator_headers, _ = _staff_headers(app, UserRole.MODERATOR)

    response = client.post(
        f"/recipes/{recipe_id}/reject",
        json={"reason": "Please provide clearer measurements."},
        headers=moderator_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "REJECTED"
    with app.app_context():
        recipe = db.session.get(Recipe, recipe_id)
        assert recipe.rejected_at is not None
        assert recipe.rejection_reason == (
            "Please provide clearer measurements."
        )
        assert recipe.approved_by_id is None
        assert recipe.approved_at is None

    resubmission = client.post(
        f"/recipes/{recipe_id}/submit", headers=author_headers
    )

    assert resubmission.status_code == 200
    assert resubmission.get_json()["status"] == "PENDING"
    with app.app_context():
        recipe = db.session.get(Recipe, recipe_id)
        assert recipe.rejected_at is None
        assert recipe.rejection_reason is None


def test_invalid_moderation_transition_is_rejected(app):
    """Staff cannot approve a draft without first receiving a submission."""
    client = app.test_client()
    author_headers = _register_and_login(client, "draft_author")
    recipe_id = _create_recipe(client, author_headers, "Draft Approval")
    moderator_headers, _ = _staff_headers(app, UserRole.MODERATOR)

    response = client.post(
        f"/recipes/{recipe_id}/approve", headers=moderator_headers
    )

    assert response.status_code == 409
