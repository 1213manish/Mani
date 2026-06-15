"""
Groups permissions: ensure only members can access group data.
"""

from rest_framework.permissions import BasePermission
from .models import GroupMembership


class IsGroupMember(BasePermission):
    """Allow access only to current active members of the group."""

    message = "You must be an active member of this group."

    def has_object_permission(self, request, view, obj):
        from .models import Group
        if isinstance(obj, Group):
            return obj.is_member(request.user)
        return False


class IsGroupAdmin(BasePermission):
    """Allow access only to group admins."""

    message = "You must be a group admin to perform this action."

    def has_object_permission(self, request, view, obj):
        from .models import Group
        if isinstance(obj, Group):
            return GroupMembership.objects.filter(
                group=obj,
                user=request.user,
                role=GroupMembership.Role.ADMIN,
                left_at__isnull=True,
            ).exists()
        return False
