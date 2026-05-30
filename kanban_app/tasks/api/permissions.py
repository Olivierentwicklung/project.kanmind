from rest_framework.permissions import SAFE_METHODS, BasePermission


class TaskPermission(BasePermission):
    """
    Object-level permission class for Task objects.
    """

    def has_object_permission(self, request, view, obj):  # type: ignore
        """
        Check whether the current user can read, update, or delete this task.
        """

        user_profile = getattr(request.user, 'userprofile', None)

        if not user_profile:
            return False

        board = obj.board

        is_board_owner = board.owner == user_profile
        is_board_member = board.members.filter(id=user_profile.id).exists()
        is_task_author = obj.author == user_profile

        if request.method in SAFE_METHODS:
            return is_board_owner or is_board_member

        if request.method in ['PATCH', 'PUT']:
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
