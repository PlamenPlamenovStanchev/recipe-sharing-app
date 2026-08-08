"""Persistence operations for recipe donations."""

from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models.donation import Donation
from app.models.enums import DonationStatus
from app.models.mixins import utc_now


class DonationPersistenceError(Exception):
    """Raised when donation state cannot be committed."""


def create_pending_donation(
    *,
    recipe_id: int,
    donor_id: int,
    recipient_id: int,
    amount: Decimal,
    currency: str,
    idempotency_key: str,
) -> Donation:
    """Create and commit the PENDING record before provider interaction."""
    donation = Donation(
        recipe_id=recipe_id,
        donor_id=donor_id,
        recipient_id=recipient_id,
        amount=amount,
        currency=currency,
        status=DonationStatus.PENDING,
        idempotency_key=idempotency_key,
    )
    db.session.add(donation)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise DonationPersistenceError(
            "Donation could not be created."
        ) from error
    return donation


def record_transfer_result(
    donation: Donation,
    *,
    external_transfer_id: str | None,
    status: DonationStatus,
) -> Donation:
    """Persist the external transfer reference and current provider status."""
    donation.wise_transfer_id = external_transfer_id
    donation.status = status
    donation.completed_at = (
        utc_now() if status == DonationStatus.COMPLETED else None
    )
    try:
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise DonationPersistenceError(
            "Donation transfer result could not be saved."
        ) from error
    return donation


def mark_donation_failed(donation: Donation) -> Donation:
    """Persist a FAILED state after a payment provider error."""
    donation.status = DonationStatus.FAILED
    donation.completed_at = None
    try:
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise DonationPersistenceError(
            "Donation failure state could not be saved."
        ) from error
    return donation
