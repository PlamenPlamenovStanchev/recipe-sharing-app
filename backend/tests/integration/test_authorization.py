"""Integration tests for database-backed JWT role authorization."""

from flask_jwt_extended import create_access_token

from app.models import UserRole
from tests.factories import UserFactory


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
    response = app.test_client().get("/recipes/pending")

    assert response.status_code == 401
    assert response.get_json() == {"message": "Authentication is required."}


def test_user_is_denied_moderator_access(app):
    """A normal user cannot access a moderator-only endpoint."""
    user = UserFactory(role=UserRole.USER)

    response = app.test_client().get(
        "/recipes/pending", headers=_authorization_header(app, user)
    )

    assert response.status_code == 403
    assert response.get_json() == {"message": "Insufficient permissions."}


def test_current_database_role_overrides_jwt_role_claim(app):
    """A stale elevated claim cannot authorize a demoted database user."""
    user = UserFactory(role=UserRole.USER)

    response = app.test_client().get(
        "/recipes/pending",
        headers=_authorization_header(app, user, claim_role=UserRole.ADMIN),
    )

    assert response.status_code == 403
    assert response.get_json() == {"message": "Insufficient permissions."}


def test_moderator_and_admin_are_allowed(app):
    """Current moderator and administrator roles are authorized."""
    moderator = UserFactory(role=UserRole.MODERATOR)
    admin = UserFactory(role=UserRole.ADMIN)

    moderator_response = app.test_client().get(
        "/recipes/pending",
        headers=_authorization_header(app, moderator),
    )
    admin_response = app.test_client().get(
        "/recipes/pending",
        headers=_authorization_header(app, admin),
    )

    assert moderator_response.status_code == 200
    assert admin_response.status_code == 200


def test_inactive_user_is_denied_after_token_issuance(app):
    """Disabling an account invalidates a previously issued access token."""
    user = UserFactory(role=UserRole.MODERATOR)
    headers = _authorization_header(app, user)
    user.is_active = False

    response = app.test_client().get("/recipes/pending", headers=headers)

    assert response.status_code == 401
    assert response.get_json() == {"message": "Authentication is required."}
