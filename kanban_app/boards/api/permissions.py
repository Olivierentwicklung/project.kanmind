from rest_framework.permissions import SAFE_METHODS, BasePermission


class BoardPermission(BasePermission):
    message = 'You do not have permission for this board.'

    def has_object_permission(self, request, view, obj):  # type:ignore
        user = request.user

        is_owner = obj.owner.user == user
        is_member = obj.members.filter(user=user).exists()

        if request.method in SAFE_METHODS:
            return is_owner or is_member

        if request.method in ['PATCH', 'PUT']:
            return is_owner or is_member

        if request.method == 'DELETE':
            return is_owner

        return False
