"""Enumerations persisted by the application models."""

from enum import Enum


class UserRole(str, Enum):
    """Roles available to application users."""

    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class RecipeStatus(str, Enum):
    """Moderation states available to recipes."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DonationStatus(str, Enum):
    """Processing states available to donations."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
