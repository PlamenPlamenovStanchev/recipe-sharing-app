"""Payment provider abstractions for recipe donations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from flask import current_app

from app.models.enums import DonationStatus


class PaymentProviderError(Exception):
    """Raised when a payment provider cannot complete an operation."""


class PaymentProviderNotConfiguredError(PaymentProviderError):
    """Raised while a real provider remains unavailable or unconfigured."""


@dataclass(frozen=True)
class TransferRequest:
    """Provider-neutral data needed to create a donation transfer."""

    amount: Decimal
    currency: str
    donor_id: int
    recipient_id: int
    recipient_reference: str | None
    idempotency_key: str


@dataclass(frozen=True)
class TransferResult:
    """Provider-neutral result returned after transfer creation."""

    external_transfer_id: str | None
    status: DonationStatus = DonationStatus.PROCESSING


class PaymentProvider(ABC):
    """Interface implemented by donation payment providers."""

    @abstractmethod
    def create_transfer(self, request: TransferRequest) -> TransferResult:
        """Create or recover an idempotent external transfer."""

    @abstractmethod
    def get_transfer_status(self, external_transfer_id: str) -> DonationStatus:
        """Return the provider's current transfer status."""


class WisePaymentProvider(PaymentProvider):
    """Configurable shell for the pending real Wise API integration."""

    def __init__(
        self,
        *,
        api_token: str | None = None,
        profile_id: str | None = None,
    ) -> None:
        self.api_token = api_token
        self.profile_id = profile_id

    @classmethod
    def from_app_config(cls) -> WisePaymentProvider:
        """Build the provider from optional application configuration."""
        return cls(
            api_token=current_app.config.get("WISE_API_TOKEN"),
            profile_id=current_app.config.get("WISE_PROFILE_ID"),
        )

    def create_transfer(self, request: TransferRequest) -> TransferResult:
        """Raise until verified Wise credentials and API flow are supplied."""
        raise PaymentProviderNotConfiguredError(
            "Wise transfer integration is pending configuration."
        )

    def get_transfer_status(self, external_transfer_id: str) -> DonationStatus:
        """Raise until verified Wise status integration is supplied."""
        raise PaymentProviderNotConfiguredError(
            "Wise transfer integration is pending configuration."
        )


class FakePaymentProvider(PaymentProvider):
    """Deterministic in-memory provider for tests and local orchestration."""

    def __init__(
        self,
        *,
        result_status: DonationStatus = DonationStatus.PROCESSING,
        failure: PaymentProviderError | None = None,
    ) -> None:
        self.result_status = result_status
        self.failure = failure
        self.requests: list[TransferRequest] = []
        self._results: dict[str, TransferResult] = {}

    def create_transfer(self, request: TransferRequest) -> TransferResult:
        """Return the same result whenever an idempotency key is reused."""
        self.requests.append(request)
        if self.failure is not None:
            raise self.failure
        if request.idempotency_key not in self._results:
            self._results[request.idempotency_key] = TransferResult(
                external_transfer_id=f"fake-{uuid4().hex}",
                status=self.result_status,
            )
        return self._results[request.idempotency_key]

    def get_transfer_status(self, external_transfer_id: str) -> DonationStatus:
        """Return the configured fake status for a known fake transfer."""
        if not any(
            result.external_transfer_id == external_transfer_id
            for result in self._results.values()
        ):
            raise PaymentProviderError("Fake transfer was not found.")
        return self.result_status


def get_payment_provider() -> PaymentProvider:
    """Return the configured provider without making an external API call."""
    provider_name = current_app.config.get("PAYMENT_PROVIDER", "wise")
    if provider_name == "wise":
        return WisePaymentProvider.from_app_config()
    raise PaymentProviderNotConfiguredError(
        "Configured payment provider is not supported."
    )
