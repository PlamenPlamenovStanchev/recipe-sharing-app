"""Business rules for administrator-managed user accounts."""

from app.models import User, UserRole
from app.repositories.users import (
    UserPersistenceConflictError,
    count_active_admins,
    get_user,
    get_user_by_email,
    get_user_by_username,
    list_users,
    save_user,
)
from app.services.auth import DuplicateEmailError, DuplicateUsernameError


class AdminUserNotFoundError(Exception):
    """Raised when an administrator targets a missing account."""


class AdminUserValidationError(Exception):
    """Raised when an admin update contains no supported changes."""


class AdminUserSafetyError(Exception):
    """Raised when a change could lock administrators out of the system."""


def get_admin_users() -> list[User]:
    """Return the complete user administration list."""
    return list_users()


def get_admin_user(user_id: int) -> User:
    """Return one managed user or raise a service-level not-found error."""
    user = get_user(user_id)
    if user is None:
        raise AdminUserNotFoundError
    return user


def _ensure_unique_identifiers(
    *,
    email: str | None = None,
    username: str | None = None,
    exclude_user_id: int | None = None,
) -> None:
    if email is not None and get_user_by_email(email, exclude_user_id):
        raise DuplicateEmailError
    if username is not None and get_user_by_username(
        username, exclude_user_id
    ):
        raise DuplicateUsernameError


def _save_with_duplicate_mapping(
    user: User,
    *,
    email: str,
    username: str,
) -> User:
    user_id = user.id
    try:
        return save_user(user)
    except UserPersistenceConflictError as error:
        if get_user_by_email(email, user_id):
            raise DuplicateEmailError from error
        if get_user_by_username(username, user_id):
            raise DuplicateUsernameError from error
        raise


def create_admin_user(user_data: dict) -> User:
    """Create an account without invoking registration email delivery."""
    _ensure_unique_identifiers(
        email=user_data["email"],
        username=user_data["username"],
    )
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        role=user_data["role"],
        is_active=user_data["is_active"],
        password_hash="",
    )
    user.set_password(user_data["password"])
    return _save_with_duplicate_mapping(
        user,
        email=user_data["email"],
        username=user_data["username"],
    )


def _ensure_admin_will_remain(user: User, changes: dict) -> None:
    removes_active_admin = (
        user.role == UserRole.ADMIN
        and user.is_active
        and (
            changes.get("role", user.role) != UserRole.ADMIN
            or changes.get("is_active", user.is_active) is False
        )
    )
    if removes_active_admin and count_active_admins(user.id) == 0:
        raise AdminUserSafetyError(
            "At least one active administrator must remain."
        )


def update_admin_user(
    user_id: int, current_admin: User, user_data: dict
) -> User:
    """Update allowed account fields while enforcing admin safety rules."""
    if not user_data:
        raise AdminUserValidationError(
            "At least one user field must be provided."
        )
    user = get_admin_user(user_id)
    if user.id == current_admin.id:
        if user_data.get("role", UserRole.ADMIN) != UserRole.ADMIN:
            raise AdminUserSafetyError(
                "You cannot remove your own administrator role."
            )
        if user_data.get("is_active") is False:
            raise AdminUserSafetyError(
                "You cannot deactivate your own account."
            )

    _ensure_admin_will_remain(user, user_data)
    _ensure_unique_identifiers(
        email=user_data.get("email"),
        username=user_data.get("username"),
        exclude_user_id=user.id,
    )
    desired_email = user_data.get("email", user.email)
    desired_username = user_data.get("username", user.username)
    for field, value in user_data.items():
        setattr(user, field, value)
    return _save_with_duplicate_mapping(
        user,
        email=desired_email,
        username=desired_username,
    )


def deactivate_admin_user(user_id: int, current_admin: User) -> None:
    """Deactivate an account without deleting its historical relationships."""
    user = get_admin_user(user_id)
    if user.id == current_admin.id:
        raise AdminUserSafetyError("You cannot deactivate your own account.")
    _ensure_admin_will_remain(user, {"is_active": False})
    if user.is_active:
        user.is_active = False
        save_user(user)
