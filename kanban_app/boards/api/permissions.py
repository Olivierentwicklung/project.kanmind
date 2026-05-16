from rest_framework.permissions import BasePermission


class IsBoardMemberOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user_profile = request.user.userprofile

        return (
            obj.owner == user_profile or obj.members.filter(id=user_profile.id).exists()
        )
