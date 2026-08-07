"""Business logic for account registration and login."""

from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, UserRole


class DuplicateEmailError(Exception):
    """Raised when an email address already belongs to a user."""


class DuplicateUsernameError(Exception):
    """Raised when a username already belongs to a user."""


class InvalidCredentialsError(Exception):
    """Raised when supplied login credentials cannot authenticate a user."""


def register_user(user_data: dict[str, str]) -> User:
    """Create a standard user after checking unique account identifiers."""
    if db.session.scalar(
        db.select(User).where(User.email == user_data["email"])
    ):
        raise DuplicateEmailError
    if db.session.scalar(
        db.select(User).where(User.username == user_data["username"])
    ):
        raise DuplicateUsernameError

    user = User(
        email=user_data["email"],
        username=user_data["username"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        role=UserRole.USER,
        password_hash="",
    )
    user.set_password(user_data["password"])
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        if db.session.scalar(
            db.select(User).where(User.email == user_data["email"])
        ):
            raise DuplicateEmailError from error
        raise DuplicateUsernameError from error

    return user


def login_user(credentials: dict[str, str]) -> tuple[str, User]:
    """Authenticate an active user and create an access token."""
    user = db.session.scalar(
        db.select(User).where(User.email == credentials["email"])
    )
    if not user or not user.is_active or not user.check_password(
        credentials["password"]
    ):
        raise InvalidCredentialsError

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role.value},
    )
    return access_token, user
