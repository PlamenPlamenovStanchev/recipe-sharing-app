"""Registration workflow tests with mocked welcome email delivery."""

from unittest.mock import patch

from app.extensions import db
from app.models import User
from app.services.email import EmailDeliveryError


def _registration_payload(username: str) -> dict[str, str]:
    """Return valid account registration data."""
    return {
        "email": f"{username}@example.test",
        "username": username,
        "password": "Password1",
        "first_name": "New",
        "last_name": "Cook",
    }


def test_successful_registration_calls_welcome_email_service(app):
    """The post-commit workflow calls email delivery with the created user."""
    payload = _registration_payload("email_success")

    with patch("app.services.registration.send_welcome_email") as send_welcome:
        response = app.test_client().post("/auth/register", json=payload)

    assert response.status_code == 201
    send_welcome.assert_called_once()
    delivered_user = send_welcome.call_args.args[0]
    assert delivered_user.id == response.get_json()["id"]
    assert delivered_user.email == payload["email"]


def test_ses_failure_does_not_rollback_registration(app, caplog):
    """A delivery outage is logged safely while the user remains committed."""
    payload = _registration_payload("email_failure")

    with patch(
        "app.services.registration.send_welcome_email",
        side_effect=EmailDeliveryError("provider detail"),
    ):
        response = app.test_client().post("/auth/register", json=payload)

    assert response.status_code == 201
    user = db.session.scalar(
        db.select(User).where(User.email == payload["email"])
    )
    assert user is not None
    assert user.id == response.get_json()["id"]
    assert "Welcome email delivery failed for user_id=" in caplog.text
    assert payload["password"] not in caplog.text
    assert payload["email"] not in caplog.text
    assert "provider detail" not in caplog.text
