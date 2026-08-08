"""Integration coverage for ADMIN-only user account management."""

from datetime import datetime, timezone

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import User, UserRole
from app.services.admin_users import (
    AdminUserSafetyError,
    deactivate_admin_user,
    update_admin_user,
)
from tests.factories import UserFactory


def _headers(user: User) -> dict[str, str]:
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def _payload(username: str = "managed_user", **changes) -> dict:
    payload = {
        "email": f"{username}@example.test",
        "username": username,
        "password": "AdminMade1",
        "first_name": "Managed",
        "last_name": "User",
        "role": "USER",
        "is_active": True,
    }
    return {**payload, **changes}


def _admin_with_headers() -> tuple[User, dict[str, str]]:
    admin = UserFactory(role=UserRole.ADMIN)
    db.session.commit()
    return admin, _headers(admin)


def _assert_safe_user(payload: dict) -> None:
    assert "password" not in payload
    assert "password_hash" not in payload
    assert "wise_recipient_id" not in payload
    assert set(payload) == {
        "id",
        "email",
        "username",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "created_at",
        "updated_at",
    }


def test_admin_user_list_requires_authentication(app):
    response = app.test_client().get("/admin/users")

    assert response.status_code == 401


@pytest.mark.parametrize("role", [UserRole.USER, UserRole.MODERATOR])
def test_non_admin_roles_cannot_list_users(app, role):
    user = UserFactory(role=role)
    db.session.commit()

    response = app.test_client().get("/admin/users", headers=_headers(user))

    assert response.status_code == 403


def test_admin_lists_users_newest_first_without_password_hash(app):
    admin = UserFactory(
        role=UserRole.ADMIN,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    newest = UserFactory(
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    db.session.commit()

    response = app.test_client().get(
        "/admin/users",
        headers=_headers(admin),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert [user["id"] for user in payload] == [newest.id, admin.id]
    assert all("password_hash" not in user for user in payload)
    _assert_safe_user(payload[0])


def test_admin_gets_individual_user_and_missing_user_returns_404(app):
    admin, headers = _admin_with_headers()
    target = UserFactory()
    db.session.commit()

    response = app.test_client().get(
        f"/admin/users/{target.id}", headers=headers
    )
    missing = app.test_client().get("/admin/users/999999", headers=headers)

    assert response.status_code == 200
    assert response.get_json()["id"] == target.id
    _assert_safe_user(response.get_json())
    assert missing.status_code == 404


@pytest.mark.parametrize("role", ["USER", "MODERATOR", "ADMIN"])
def test_admin_creates_each_allowed_role_with_hashed_password(app, role):
    _, headers = _admin_with_headers()
    payload = _payload(f"created_{role.lower()}", role=role)

    response = app.test_client().post(
        "/admin/users", json=payload, headers=headers
    )

    assert response.status_code == 201
    output = response.get_json()
    assert output["role"] == role
    _assert_safe_user(output)
    user = db.session.get(User, output["id"])
    assert user.check_password(payload["password"])
    assert user.password_hash != payload["password"]


def test_duplicate_email_is_rejected(app):
    _, headers = _admin_with_headers()
    existing = UserFactory()
    db.session.commit()

    response = app.test_client().post(
        "/admin/users",
        json=_payload("unique_name", email=existing.email),
        headers=headers,
    )

    assert response.status_code == 409
    assert "email" in response.get_json()["message"].lower()


def test_duplicate_username_is_rejected(app):
    _, headers = _admin_with_headers()
    existing = UserFactory()
    db.session.commit()

    response = app.test_client().post(
        "/admin/users",
        json=_payload(existing.username, email="unique@example.test"),
        headers=headers,
    )

    assert response.status_code == 409
    assert "username" in response.get_json()["message"].lower()


def test_invalid_password_and_protected_create_fields_are_rejected(app):
    _, headers = _admin_with_headers()

    invalid_password = app.test_client().post(
        "/admin/users",
        json=_payload("weak_password", password="weak"),
        headers=headers,
    )
    protected_field = app.test_client().post(
        "/admin/users",
        json={**_payload("protected_field"), "password_hash": "unsafe"},
        headers=headers,
    )

    assert invalid_password.status_code == 400
    assert protected_field.status_code == 400


def test_admin_updates_profile_fields_without_changing_password(app):
    _, headers = _admin_with_headers()
    target = UserFactory()
    original_hash = target.password_hash
    db.session.commit()

    response = app.test_client().put(
        f"/admin/users/{target.id}",
        json={
            "email": "updated@example.test",
            "username": "updated_user",
            "first_name": "Updated",
            "last_name": "Account",
        },
        headers=headers,
    )

    assert response.status_code == 200
    output = response.get_json()
    assert output["email"] == "updated@example.test"
    assert output["username"] == "updated_user"
    assert output["first_name"] == "Updated"
    assert output["last_name"] == "Account"
    assert db.session.get(User, target.id).password_hash == original_hash
    _assert_safe_user(output)


def test_admin_changes_another_users_role(app):
    _, headers = _admin_with_headers()
    target = UserFactory(role=UserRole.USER)
    db.session.commit()

    response = app.test_client().put(
        f"/admin/users/{target.id}",
        json={"role": "MODERATOR"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.get_json()["role"] == "MODERATOR"


def test_admin_deactivates_another_user_without_deleting_them(app):
    _, headers = _admin_with_headers()
    target = UserFactory(is_active=True)
    target_id = target.id
    db.session.commit()

    response = app.test_client().delete(
        f"/admin/users/{target_id}", headers=headers
    )

    assert response.status_code == 204
    persisted = db.session.get(User, target_id)
    assert persisted is not None
    assert persisted.is_active is False


def test_admin_can_reactivate_user_through_update(app):
    _, headers = _admin_with_headers()
    target = UserFactory(is_active=False)
    db.session.commit()

    response = app.test_client().put(
        f"/admin/users/{target.id}",
        json={"is_active": True},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.get_json()["is_active"] is True


def test_admin_cannot_deactivate_themselves(app):
    admin, headers = _admin_with_headers()

    response = app.test_client().delete(
        f"/admin/users/{admin.id}", headers=headers
    )

    assert response.status_code == 409
    assert db.session.get(User, admin.id).is_active is True


def test_admin_cannot_remove_their_own_admin_role(app):
    admin, headers = _admin_with_headers()

    response = app.test_client().put(
        f"/admin/users/{admin.id}",
        json={"role": "USER"},
        headers=headers,
    )

    assert response.status_code == 409
    assert db.session.get(User, admin.id).role == UserRole.ADMIN


def test_last_active_admin_cannot_be_deactivated_or_demoted(app):
    last_admin = UserFactory(role=UserRole.ADMIN, is_active=True)
    detached_actor = User(id=-1, role=UserRole.ADMIN, is_active=True)
    db.session.commit()

    with pytest.raises(AdminUserSafetyError, match="active administrator"):
        deactivate_admin_user(last_admin.id, detached_actor)
    with pytest.raises(AdminUserSafetyError, match="active administrator"):
        update_admin_user(
            last_admin.id,
            detached_actor,
            {"role": UserRole.MODERATOR},
        )

    persisted = db.session.get(User, last_admin.id)
    assert persisted.is_active is True
    assert persisted.role == UserRole.ADMIN


def test_update_rejects_password_and_never_returns_password_hash(app):
    _, headers = _admin_with_headers()
    target = UserFactory()
    original_hash = target.password_hash
    db.session.commit()

    response = app.test_client().put(
        f"/admin/users/{target.id}",
        json={"password": "Replacement1"},
        headers=headers,
    )

    assert response.status_code == 400
    assert db.session.get(User, target.id).password_hash == original_hash
