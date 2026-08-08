"""Unit tests for provider-neutral payment behavior."""

from decimal import Decimal

from app.services.payments import FakePaymentProvider, TransferRequest


def test_fake_provider_reuses_result_for_same_idempotency_key():
    """Repeated provider calls with one key represent one external transfer."""
    provider = FakePaymentProvider()
    request = TransferRequest(
        amount=Decimal("10.00"),
        currency="EUR",
        donor_id=1,
        recipient_id=2,
        recipient_reference="recipient-ref",
        idempotency_key="stable-key",
    )

    first_result = provider.create_transfer(request)
    second_result = provider.create_transfer(request)

    assert first_result == second_result
    assert first_result.external_transfer_id is not None
