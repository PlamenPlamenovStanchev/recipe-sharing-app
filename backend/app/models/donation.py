"""Donation database model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import DonationStatus
from app.models.mixins import utc_now

if TYPE_CHECKING:
    from app.models.recipe import Recipe
    from app.models.user import User


class Donation(db.Model):
    """A financial contribution associated with a recipe and recipient."""

    __tablename__ = "donations"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_donations_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    donor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[DonationStatus] = mapped_column(
        Enum(DonationStatus, name="donation_status"),
        default=DonationStatus.PENDING,
        nullable=False,
    )
    wise_transfer_id: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    donor: Mapped[User] = relationship(
        "User",
        foreign_keys=[donor_id],
        back_populates="donations_sent",
    )
    recipient: Mapped[User] = relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="donations_received",
    )
    recipe: Mapped[Recipe] = relationship(back_populates="donations")
