"""Database-backed JWT authentication and role authorization utilities."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db, jwt
from app.models.enums import UserRole
from app.models.user import User


def _authentication_error() -> tuple[dict[str, str], int]:
    """Return the standard response for unusable authentication."""
    return {"message": "Authentication is required."}, 401


def _authorization_error() -> tuple[dict[str, str], int]:
    """Return the standard response for insufficient permissions."""
    return {"message": "Insufficient permissions."}, 403


def configure_jwt_error_handlers() -> None:
    """Configure consistent JSON responses for JWT authentication failures."""

    @jwt.unauthorized_loader
    def missing_token(_: str) -> tuple[dict[str, str], int]:
        return _authentication_error()

    @jwt.invalid_token_loader
    def invalid_token(_: str) -> tuple[dict[str, str], int]:
        return _authentication_error()

    @jwt.expired_token_loader
    def expired_token(_: dict[str, Any], __: dict[str, Any]):
        return _authentication_error()


def get_current_authenticated_user_id() -> int | None:
    """Return the authenticated user's database ID from the JWT subject."""
    identity = get_jwt_identity()
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def get_current_authenticated_user() -> User | None:
    """Load the current user and reject deleted or inactive accounts."""
    user_id = get_current_authenticated_user_id()
    if user_id is None:
        return None

    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        return None
    return user


def is_resource_owner(
    resource: object, owner_attribute: str = "author_id"
) -> bool:
    """Return whether the authenticated active user owns ``resource``."""
    user = get_current_authenticated_user()
    owner_id = getattr(resource, owner_attribute, None)
    return user is not None and owner_id == user.id


def roles_required(*allowed_roles: UserRole) -> Callable:
    """Require an active database user with one of ``allowed_roles``."""
    if not allowed_roles:
        raise ValueError("At least one role must be provided.")
    if not all(isinstance(role, UserRole) for role in allowed_roles):
        raise TypeError("Roles must be UserRole values.")

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        @jwt_required()
        def wrapped(*args: Any, **kwargs: Any):
            user = get_current_authenticated_user()
            if user is None:
                return _authentication_error()
            if user.role not in allowed_roles:
                return _authorization_error()
            return view(*args, **kwargs)

        return wrapped

    return decorator
