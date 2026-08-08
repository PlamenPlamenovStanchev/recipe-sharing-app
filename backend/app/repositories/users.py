"""Persistence operations for administrator-managed user accounts."""

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, UserRole


class UserPersistenceConflictError(Exception):
    """Raised when a user write violates a database constraint."""


def list_users() -> list[User]:
    """Return all users ordered newest first."""
    statement = db.select(User).order_by(
        User.created_at.desc(), User.id.desc()
    )
    return list(db.session.scalars(statement))


def get_user(user_id: int) -> User | None:
    """Return one user by primary key."""
    return db.session.get(User, user_id)


def get_user_by_email(
    email: str, exclude_user_id: int | None = None
) -> User | None:
    """Return the account using an email, optionally excluding one user."""
    statement = db.select(User).where(User.email == email)
    if exclude_user_id is not None:
        statement = statement.where(User.id != exclude_user_id)
    return db.session.scalar(statement)


def get_user_by_username(
    username: str, exclude_user_id: int | None = None
) -> User | None:
    """Return the account using a username, optionally excluding one user."""
    statement = db.select(User).where(User.username == username)
    if exclude_user_id is not None:
        statement = statement.where(User.id != exclude_user_id)
    return db.session.scalar(statement)


def count_active_admins(exclude_user_id: int | None = None) -> int:
    """Count active administrators, optionally excluding one account."""
    statement = db.select(db.func.count(User.id)).where(
        User.role == UserRole.ADMIN,
        User.is_active.is_(True),
    )
    if exclude_user_id is not None:
        statement = statement.where(User.id != exclude_user_id)
    return db.session.scalar(statement) or 0


def save_user(user: User) -> User:
    """Persist a new or changed user and normalize constraint conflicts."""
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise UserPersistenceConflictError from error
    return user
