from rest_framework.permissions import BasePermission


class IsTaskBoardMemberOrOwner(BasePermission):
    """
    Allow access only to task board owners or board members.
    """

    def has_object_permission(self, request, view, obj):
        """
        Allow access only to task board owners or board members.
        """
        user_profile = request.user.userprofile
        board = obj.board

        return (
            board.owner == user_profile
            or board.members.filter(id=user_profile.id).exists()
        )
