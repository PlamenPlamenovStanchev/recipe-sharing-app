"""Focused integration tests for registration and login behavior."""

from unittest.mock import patch

import pytest

from app.extensions import db
from tests.factories import UserFactory


def _registration_payload(username: str = "auth_user") -> dict[str, str]:
    return {
        "email": f"{username}@example.test",
        "username": username,
        "password": "Password1",
        "first_name": "Auth",
        "last_name": "User",
    }


def test_registration_and_login_return_safe_user_and_token(app):
    payload = _registration_payload()
    client = app.test_client()

    with patch("app.services.registration.send_welcome_email") as email:
        registration = client.post("/auth/register", json=payload)
    login = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    assert registration.status_code == 201
    assert login.status_code == 200
    assert login.get_json()["access_token"]
    assert login.get_json()["user"]["email"] == payload["email"]
    assert "password" not in registration.get_json()
    assert "password_hash" not in registration.get_json()
    email.assert_called_once()


@pytest.mark.parametrize(
    "credentials",
    [
        {"email": "missing@example.test", "password": "Password1"},
        {"email": "login_user@example.test", "password": "WrongPass1"},
    ],
)
def test_login_rejects_invalid_credentials_without_account_disclosure(
    app, credentials
):
    UserFactory(email="login_user@example.test")
    db.session.commit()

    response = app.test_client().post("/auth/login", json=credentials)

    assert response.status_code == 401
    assert response.get_json() == {"message": "Invalid email or password."}


def test_inactive_user_cannot_login(app):
    user = UserFactory(email="inactive@example.test", is_active=False)
    db.session.commit()

    response = app.test_client().post(
        "/auth/login",
        json={"email": user.email, "password": "FactoryPass1"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("existing_field", "value", "expected_message"),
    [
        ("email", "duplicate@example.test", "Email is already registered."),
        ("username", "duplicate_user", "Username is already registered."),
    ],
)
def test_registration_rejects_duplicate_identifiers(
    app, existing_field, value, expected_message
):
    existing_values = {
        "email": "existing@example.test",
        "username": "existing_user",
        existing_field: value,
    }
    UserFactory(**existing_values)
    db.session.commit()
    payload = _registration_payload("new_registration")
    payload[existing_field] = value

    with patch("app.services.registration.send_welcome_email") as email:
        response = app.test_client().post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.get_json() == {"message": expected_message}
    email.assert_not_called()
