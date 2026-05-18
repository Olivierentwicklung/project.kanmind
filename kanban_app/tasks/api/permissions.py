from rest_framework.permissions import BasePermission


class IsTaskBoardMemberOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user_profile = request.user.userprofile
        board = obj.board

        return (
            board.owner == user_profile
            or board.members.filter(id=user_profile.id).exists()
        )
