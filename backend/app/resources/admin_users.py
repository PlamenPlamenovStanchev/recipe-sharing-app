"""ADMIN-only HTTP resources for user account management."""

from flask import request
from flask_restful import Resource
from marshmallow import ValidationError

from app.authorization import get_current_authenticated_user, roles_required
from app.models.enums import UserRole
from app.schemas.admin_users import (
    AdminUserCreateSchema,
    AdminUserOutputSchema,
    AdminUserUpdateSchema,
)
from app.services.admin_users import (
    AdminUserNotFoundError,
    AdminUserSafetyError,
    AdminUserValidationError,
    create_admin_user,
    deactivate_admin_user,
    get_admin_user,
    get_admin_users,
    update_admin_user,
)
from app.services.auth import DuplicateEmailError, DuplicateUsernameError


def _validation_error(error: ValidationError) -> tuple[dict, int]:
    return {"message": "Validation failed.", "errors": error.messages}, 400


def _not_found() -> tuple[dict, int]:
    return {"message": "User not found."}, 404


def _conflict_response(error: Exception) -> tuple[dict, int]:
    if isinstance(error, DuplicateEmailError):
        return {"message": "Email is already registered."}, 409
    if isinstance(error, DuplicateUsernameError):
        return {"message": "Username is already registered."}, 409
    return {"message": str(error)}, 409


class AdminUserListResource(Resource):
    """List accounts or create an explicitly validated account."""

    @roles_required(UserRole.ADMIN)
    def get(self):
        return AdminUserOutputSchema(many=True).dump(get_admin_users()), 200

    @roles_required(UserRole.ADMIN)
    def post(self):
        try:
            user_data = AdminUserCreateSchema().load(
                request.get_json(silent=True) or {}
            )
            user = create_admin_user(user_data)
        except ValidationError as error:
            return _validation_error(error)
        except (DuplicateEmailError, DuplicateUsernameError) as error:
            return _conflict_response(error)
        return AdminUserOutputSchema().dump(user), 201


class AdminUserDetailResource(Resource):
    """Read, update, or deactivate one managed account."""

    @roles_required(UserRole.ADMIN)
    def get(self, user_id: int):
        try:
            user = get_admin_user(user_id)
        except AdminUserNotFoundError:
            return _not_found()
        return AdminUserOutputSchema().dump(user), 200

    @roles_required(UserRole.ADMIN)
    def put(self, user_id: int):
        try:
            user_data = AdminUserUpdateSchema().load(
                request.get_json(silent=True) or {}
            )
            user = update_admin_user(
                user_id,
                get_current_authenticated_user(),
                user_data,
            )
        except ValidationError as error:
            return _validation_error(error)
        except AdminUserNotFoundError:
            return _not_found()
        except AdminUserValidationError as error:
            return {"message": str(error)}, 400
        except (
            DuplicateEmailError,
            DuplicateUsernameError,
            AdminUserSafetyError,
        ) as error:
            return _conflict_response(error)
        return AdminUserOutputSchema().dump(user), 200

    @roles_required(UserRole.ADMIN)
    def delete(self, user_id: int):
        try:
            deactivate_admin_user(
                user_id,
                get_current_authenticated_user(),
            )
        except AdminUserNotFoundError:
            return _not_found()
        except AdminUserSafetyError as error:
            return _conflict_response(error)
        return "", 204
