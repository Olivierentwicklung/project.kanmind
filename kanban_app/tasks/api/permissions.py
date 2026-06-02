from django.shortcuts import get_object_or_404
from rest_framework.permissions import SAFE_METHODS, BasePermission

from kanban_app.boards.models import Board


class TaskPermission(BasePermission):
    """
    Permission class for Task objects.

    Rules:
    - Creating a task:
        The user must be the board owner or a board member.
    - Retrieving a task:
        The user must be the board owner or a board member.
    - Updating a task:
        The user must be the board owner or a board member.
    - Deleting a task:
        The user must be the board owner or the task author.
    """

    message = 'You do not have permission for this task.'

    def has_permission(self, request, view):  # type: ignore
        """
        Validate permissions for task creation.

        For POST requests, verifies that the provided board exists
        and that the authenticated user's profile belongs to the
        board as either the owner or a member.

        Returns:
            bool: True if the user is allowed to create tasks on
                the specified board, otherwise False.
        """
        if request.method != 'POST':
            return True

        board_id = request.data.get('board')

        if board_id is None:
            return True

        board = get_object_or_404(
            Board.objects.prefetch_related('members'),
            pk=board_id,
        )

        profile = request.user.userprofile

        return (
            board.owner_id == profile.id or board.members.filter(id=profile.id).exists()  # type:ignore
        )

    def has_object_permission(self, request, view, obj):  # type: ignore
        """
        Validate permissions for an existing task.

        Permissions:
        - GET, HEAD, OPTIONS, POST:
            Board owner or board member.
        - PUT, PATCH:
            Board owner or board member.
        - DELETE:
            Board owner or task author.

        Args:
            obj (Task): The task being accessed.

        Returns:
            bool: True if the user has permission to perform the
                requested action on the task.
        """
        profile = request.user.userprofile
        board = obj.board

        is_board_owner = board.owner_id == profile.id
        is_board_member = board.members.filter(id=profile.id).exists()
        is_task_author = obj.author_id == profile.id

        if request.method in SAFE_METHODS or request.method == 'POST':
            return is_board_owner or is_board_member

        if request.method in ('PUT', 'PATCH'):
            return is_board_owner or is_board_member

        if request.method == 'DELETE':
            return is_board_owner or is_task_author

        return False


class CommentPermission(BasePermission):
    message = 'Only the comment author can delete this comment.'

    def has_object_permission(self, request, view, obj):  # type: ignore
        user_profile = request.user.userprofile

        if request.method == 'DELETE':
            return obj.author == user_profile

        return False
