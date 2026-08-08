"""Integration tests for recipe donation creation."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import Donation, DonationStatus, RecipeStatus
from app.services.payments import FakePaymentProvider, PaymentProviderError
from tests.factories import RecipeFactory, UserFactory


def _headers(user) -> dict[str, str]:
    """Return a valid authorization header for a persisted user."""
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def _post_donation(app, recipe_id, headers, provider, amount="10.00"):
    """Post a donation while replacing the external provider."""
    with patch(
        "app.services.donations.get_payment_provider",
        return_value=provider,
    ):
        return app.test_client().post(
            f"/recipes/{recipe_id}/donations",
            json={"amount": amount, "currency": "EUR"},
            headers=headers,
        )


def test_successful_donation_creation_uses_current_users_and_provider(app):
    """An approved recipe donation stores parties and provider result."""
    with app.app_context():
        author = UserFactory(wise_recipient_id="wise-recipient")
        donor = UserFactory()
        recipe = RecipeFactory(author=author, status=RecipeStatus.APPROVED)
        recipe_id, donor_id, author_id = recipe.id, donor.id, author.id
        headers = _headers(donor)
        db.session.commit()
    provider = FakePaymentProvider()

    response = _post_donation(app, recipe_id, headers, provider)

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["amount"] == "10.00"
    assert payload["currency"] == "EUR"
    assert payload["status"] == "PROCESSING"
    assert payload["donor_id"] == donor_id
    assert payload["recipient_id"] == author_id
    assert provider.requests[0].idempotency_key == payload["idempotency_key"]
    assert provider.requests[0].recipient_reference == "wise-recipient"
    donation = db.session.get(Donation, payload["id"])
    assert donation.amount == Decimal("10.00")
    assert donation.wise_transfer_id == payload["wise_transfer_id"]


def test_donor_cannot_donate_to_own_recipe(app):
    """Recipe authors cannot create donations to themselves."""
    with app.app_context():
        author = UserFactory()
        recipe = RecipeFactory(author=author, status=RecipeStatus.APPROVED)
        recipe_id = recipe.id
        headers = _headers(author)
        db.session.commit()
    provider = FakePaymentProvider()

    response = _post_donation(app, recipe_id, headers, provider)

    assert response.status_code == 403
    assert provider.requests == []


def test_donor_cannot_donate_to_pending_recipe(app):
    """Only approved recipes can receive donations."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.PENDING)
        donor = UserFactory()
        recipe_id = recipe.id
        headers = _headers(donor)
        db.session.commit()
    provider = FakePaymentProvider()

    response = _post_donation(app, recipe_id, headers, provider)

    assert response.status_code == 409
    assert provider.requests == []


@pytest.mark.parametrize("amount", ["0", "-1.00", "0.001"])
def test_donation_amount_must_be_positive_money_value(app, amount):
    """Non-positive or over-precise amounts fail schema validation."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        donor = UserFactory()
        recipe_id = recipe.id
        headers = _headers(donor)
        db.session.commit()
    provider = FakePaymentProvider()

    response = _post_donation(app, recipe_id, headers, provider, amount=amount)

    assert response.status_code == 400
    assert provider.requests == []


def test_each_donation_attempt_gets_a_unique_idempotency_key(app):
    """Separate donation attempts use distinct stored and provider keys."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        donor = UserFactory()
        recipe_id = recipe.id
        headers = _headers(donor)
        db.session.commit()
    provider = FakePaymentProvider()

    first = _post_donation(app, recipe_id, headers, provider)
    second = _post_donation(app, recipe_id, headers, provider)

    assert first.status_code == 201
    assert second.status_code == 201
    assert (
        first.get_json()["idempotency_key"]
        != second.get_json()["idempotency_key"]
    )
    assert len({request.idempotency_key for request in provider.requests}) == 2


def test_provider_failure_preserves_failed_donation_record(app):
    """A provider error preserves the committed donation safely."""
    with app.app_context():
        recipe = RecipeFactory(status=RecipeStatus.APPROVED)
        donor = UserFactory()
        recipe_id = recipe.id
        headers = _headers(donor)
        db.session.commit()
    provider = FakePaymentProvider(
        failure=PaymentProviderError("temporary outage")
    )

    response = _post_donation(app, recipe_id, headers, provider)

    assert response.status_code == 502
    payload = response.get_json()["donation"]
    assert payload["status"] == "FAILED"
    donation = db.session.get(Donation, payload["id"])
    assert donation is not None
    assert donation.status == DonationStatus.FAILED
    assert donation.wise_transfer_id is None
    assert donation.idempotency_key == provider.requests[0].idempotency_key
