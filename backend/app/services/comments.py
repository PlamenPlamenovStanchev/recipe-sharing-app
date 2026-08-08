"""Business logic for listing and managing recipe comments."""

from app.extensions import db
from app.models.comment import Comment
from app.models.enums import RecipeStatus, UserRole
from app.models.recipe import Recipe
from app.models.user import User
from app.repositories.comments import get_active_comment, list_active_comments
from app.repositories.recipes import get_recipe


class CommentNotFoundError(Exception):
    """Raised when a recipe or active comment is unavailable."""


class CommentPermissionError(Exception):
    """Raised when a user may not perform a comment operation."""


class CommentRecipeStatusError(Exception):
    """Raised when comments cannot be created for a recipe's state."""


def _may_view_recipe(recipe: Recipe, user: User | None) -> bool:
    """Return whether the viewer may list a recipe's comments."""
    if recipe.status == RecipeStatus.APPROVED:
        return True
    if user is None:
        return False
    return recipe.author_id == user.id or user.role in {
        UserRole.MODERATOR,
        UserRole.ADMIN,
    }


def get_comments_for_recipe(
    recipe_id: int, viewer: User | None
) -> list[Comment]:
    """Return visible, active comments for an accessible recipe."""
    recipe = get_recipe(recipe_id)
    if recipe is None or not _may_view_recipe(recipe, viewer):
        raise CommentNotFoundError
    return list_active_comments(recipe.id)


def create_comment(recipe_id: int, author: User, content: str) -> Comment:
    """Create a comment on an approved recipe for the current user."""
    recipe = get_recipe(recipe_id)
    if recipe is None:
        raise CommentNotFoundError
    if recipe.status != RecipeStatus.APPROVED:
        raise CommentRecipeStatusError(
            "Comments can only be created for approved recipes."
        )

    comment = Comment(content=content, user=author, recipe=recipe)
    db.session.add(comment)
    db.session.commit()
    return comment


def _get_editable_comment(comment_id: int, user: User) -> Comment:
    """Load a comment and enforce ownership or staff permissions."""
    comment = get_active_comment(comment_id)
    if comment is None:
        raise CommentNotFoundError
    if comment.user_id != user.id and user.role not in {
        UserRole.MODERATOR,
        UserRole.ADMIN,
    }:
        raise CommentPermissionError
    return comment


def update_comment(comment_id: int, user: User, content: str) -> Comment:
    """Update an active comment when the current user is permitted."""
    comment = _get_editable_comment(comment_id, user)
    comment.content = content
    db.session.commit()
    return comment


def delete_comment(comment_id: int, user: User) -> None:
    """Soft-delete a comment when the current user is permitted."""
    comment = _get_editable_comment(comment_id, user)
    comment.is_deleted = True
    db.session.commit()
