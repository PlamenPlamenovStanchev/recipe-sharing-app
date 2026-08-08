"""Business logic and payment orchestration for recipe donations."""

from uuid import uuid4

from app.models.donation import Donation
from app.models.enums import RecipeStatus
from app.models.user import User
from app.repositories.donations import (
    DonationPersistenceError,
    create_pending_donation,
    mark_donation_failed,
    record_transfer_result,
)
from app.repositories.recipes import get_recipe
from app.services.payments import (
    PaymentProvider,
    PaymentProviderError,
    TransferRequest,
    get_payment_provider,
)


class DonationRecipeNotFoundError(Exception):
    """Raised when the target recipe does not exist."""


class DonationRecipeStatusError(Exception):
    """Raised when the target recipe is not approved."""


class SelfDonationError(Exception):
    """Raised when a recipe author attempts to donate to themselves."""


class DonationPaymentError(Exception):
    """Raised after a provider failure has been handled safely."""

    def __init__(self, donation: Donation) -> None:
        super().__init__("Payment provider could not create the transfer.")
        self.donation = donation


def create_donation(
    recipe_id: int,
    donor: User,
    donation_data: dict,
    provider: PaymentProvider | None = None,
) -> Donation:
    """Create a donation and coordinate its external payment transfer."""
    recipe = get_recipe(recipe_id)
    if recipe is None:
        raise DonationRecipeNotFoundError
    if recipe.status != RecipeStatus.APPROVED:
        raise DonationRecipeStatusError
    if recipe.author_id == donor.id:
        raise SelfDonationError

    idempotency_key = uuid4().hex
    donation = create_pending_donation(
        recipe_id=recipe.id,
        donor_id=donor.id,
        recipient_id=recipe.author_id,
        amount=donation_data["amount"],
        currency=donation_data["currency"],
        idempotency_key=idempotency_key,
    )
    transfer_request = TransferRequest(
        amount=donation.amount,
        currency=donation.currency,
        donor_id=donation.donor_id,
        recipient_id=donation.recipient_id,
        recipient_reference=recipe.author.wise_recipient_id,
        idempotency_key=donation.idempotency_key,
    )
    selected_provider = (
        provider if provider is not None else get_payment_provider()
    )

    try:
        result = selected_provider.create_transfer(transfer_request)
    except PaymentProviderError as error:
        try:
            mark_donation_failed(donation)
        except DonationPersistenceError:
            pass
        raise DonationPaymentError(donation) from error

    return record_transfer_result(
        donation,
        external_transfer_id=result.external_transfer_id,
        status=result.status,
    )
