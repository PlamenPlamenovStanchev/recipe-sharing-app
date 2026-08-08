"""Authenticated recipe donation API resource."""

from flask import request
from flask_restful import Resource
from marshmallow import ValidationError

from app.authorization import get_current_authenticated_user, roles_required
from app.models.enums import UserRole
from app.repositories.donations import DonationPersistenceError
from app.schemas.donations import DonationInputSchema, DonationOutputSchema
from app.services.donations import (
    DonationPaymentError,
    DonationRecipeNotFoundError,
    DonationRecipeStatusError,
    SelfDonationError,
    create_donation,
)

_AUTHENTICATED_ROLES = (UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN)


class RecipeDonationResource(Resource):
    """Create a donation for an approved recipe."""

    @roles_required(*_AUTHENTICATED_ROLES)
    def post(self, recipe_id: int):
        """Validate and create a donation for the current user."""
        try:
            donation_data = DonationInputSchema().load(
                request.get_json(silent=True) or {}
            )
        except ValidationError as error:
            return {
                "message": "Validation failed.",
                "errors": error.messages,
            }, 400

        donor = get_current_authenticated_user()
        if donor is None:
            return {"message": "Authentication is required."}, 401

        try:
            donation = create_donation(recipe_id, donor, donation_data)
        except DonationRecipeNotFoundError:
            return {"message": "Recipe not found."}, 404
        except DonationRecipeStatusError:
            return {"message": "Donations require an approved recipe."}, 409
        except SelfDonationError:
            return {"message": "You cannot donate to your own recipe."}, 403
        except DonationPaymentError as error:
            return {
                "message": str(error),
                "donation": DonationOutputSchema().dump(error.donation),
            }, 502
        except DonationPersistenceError:
            return {"message": "Donation could not be saved."}, 500

        return DonationOutputSchema().dump(donation), 201
