"""User database model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import UserRole
from app.models.mixins import TimestampMixin
from app.services.password import (
    hash_password,
    password_needs_rehash,
    verify_password,
)

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.donation import Donation
    from app.models.recipe import Recipe
    from app.models.recipe_like import RecipeLike


class User(TimestampMixin, db.Model):
    """An account that can author recipes and interact with content."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_username", "username", unique=True),
        Index("ix_users_role", "role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    wise_recipient_id: Mapped[str | None] = mapped_column(String(255))

    authored_recipes: Mapped[list[Recipe]] = relationship(
        "Recipe",
        foreign_keys="Recipe.author_id",
        back_populates="author",
        passive_deletes="all",
    )
    approved_recipes: Mapped[list[Recipe]] = relationship(
        "Recipe",
        foreign_keys="Recipe.approved_by_id",
        back_populates="approved_by",
        passive_deletes="all",
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="user",
        passive_deletes="all",
    )
    recipe_likes: Mapped[list[RecipeLike]] = relationship(
        back_populates="user",
        passive_deletes="all",
    )
    donations_sent: Mapped[list[Donation]] = relationship(
        "Donation",
        foreign_keys="Donation.donor_id",
        back_populates="donor",
        passive_deletes="all",
    )
    donations_received: Mapped[list[Donation]] = relationship(
        "Donation",
        foreign_keys="Donation.recipient_id",
        back_populates="recipient",
        passive_deletes="all",
    )

    def set_password(self, plain_password: str) -> None:
        """Validate and securely hash a password for storage."""
        self.password_hash = hash_password(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """Return whether a password matches this user's stored hash."""
        return verify_password(self.password_hash, plain_password)

    def password_needs_rehash(self) -> bool:
        """Return whether this user's hash needs updated Argon2 parameters."""
        return password_needs_rehash(self.password_hash)

    def __repr__(self) -> str:
        """Return a safe representation that excludes credential material."""
        return f"<User id={self.id} username={self.username!r}>"
