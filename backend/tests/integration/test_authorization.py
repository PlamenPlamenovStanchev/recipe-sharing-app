"""Integration tests for database-backed JWT role authorization."""

import pytest
from flask import jsonify
from flask_jwt_extended import create_access_token

from app.authorization import roles_required
from app.models import UserRole
from tests.factories import UserFactory


@pytest.fixture(scope="module", autouse=True)
def protected_test_route(app):
    """Register a minimal protected endpoint used only by these tests."""
    if "authorization_test_moderator" not in app.view_functions:

        @app.get("/_test/moderator")
        @roles_required(UserRole.MODERATOR, UserRole.ADMIN)
        def authorization_test_moderator():
            return jsonify({"status": "ok"})


def _authorization_header(
    app, user, claim_role: UserRole | None = None
) -> dict[str, str]:
    """Create a token header whose role claim is only informational."""
    with app.app_context():
        token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": (claim_role or user.role).value},
        )
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_access_is_rejected(app):
    """Endpoints guarded by roles reject missing JWTs."""
    response = app.test_client().get("/_test/moderator")

    assert response.status_code == 401
    assert response.get_json() == {"message": "Authentication is required."}


def test_user_is_denied_moderator_access(app):
    """A normal user cannot access a moderator-only endpoint."""
    user = UserFactory(role=UserRole.USER)

    response = app.test_client().get(
        "/_test/moderator", headers=_authorization_header(app, user)
    )

    assert response.status_code == 403
    assert response.get_json() == {"message": "Insufficient permissions."}


def test_current_database_role_overrides_jwt_role_claim(app):
    """A stale elevated claim cannot authorize a demoted database user."""
    user = UserFactory(role=UserRole.USER)

    response = app.test_client().get(
        "/_test/moderator",
        headers=_authorization_header(app, user, claim_role=UserRole.ADMIN),
    )

    assert response.status_code == 403
    assert response.get_json() == {"message": "Insufficient permissions."}


@pytest.mark.parametrize("role", [UserRole.MODERATOR, UserRole.ADMIN])
def test_moderator_and_admin_are_allowed(app, role):
    """Current moderator and administrator roles are authorized."""
    user = UserFactory(role=role)

    response = app.test_client().get(
        "/_test/moderator", headers=_authorization_header(app, user)
    )

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_inactive_user_is_denied_after_token_issuance(app):
    """Disabling an account invalidates a previously issued access token."""
    user = UserFactory(role=UserRole.MODERATOR)
    headers = _authorization_header(app, user)
    user.is_active = False

    response = app.test_client().get("/_test/moderator", headers=headers)

    assert response.status_code == 401
    assert response.get_json() == {"message": "Authentication is required."}
