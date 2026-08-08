"""Post-commit workflow for new user registration."""

from flask import current_app

from app.models.user import User
from app.services.auth import register_user
from app.services.email import EmailServiceError, send_welcome_email


def register_user_with_welcome_email(user_data: dict[str, str]) -> User:
    """Persist a user, then attempt non-critical welcome email delivery."""
    user = register_user(user_data)
    try:
        send_welcome_email(user)
    except EmailServiceError:
        current_app.logger.warning(
            "Welcome email delivery failed for user_id=%s.", user.id
        )
    return user
