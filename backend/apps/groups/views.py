"""
Groups views: CRUD for groups and membership management.
"""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import Group, GroupMembership
from .serializers import (
    GroupSerializer,
    GroupCreateSerializer,
    GroupMembershipSerializer,
    AddMemberSerializer,
    LeaveMemberSerializer,
)
from .permissions import IsGroupMember, IsGroupAdmin


@extend_schema(tags=["Groups"])
class GroupListCreateView(generics.ListCreateAPIView):
    """List all groups the user belongs to, or create a new group."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GroupCreateSerializer
        return GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            memberships__user=self.request.user,
            memberships__left_at__isnull=True,
            is_active=True,
        ).select_related("created_by", "default_currency").distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(
            GroupSerializer(group, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Groups"])
class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or (soft-)delete a group."""

    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            memberships__user=self.request.user,
            memberships__left_at__isnull=True,
        ).distinct()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return GroupCreateSerializer
        return GroupSerializer

    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        # Check admin permission
        if not GroupMembership.objects.filter(
            group=group, user=request.user,
            role=GroupMembership.Role.ADMIN, left_at__isnull=True,
        ).exists():
            return Response(
                {"error": "Only group admins can delete a group."},
                status=status.HTTP_403_FORBIDDEN,
            )
        group.is_active = False
        group.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Groups"])
class GroupMemberListView(generics.ListAPIView):
    """List all members (current and historical) of a group."""

    serializer_class = GroupMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs["pk"]
        # Ensure requester is a member
        try:
            group = Group.objects.get(
                id=group_id,
                memberships__user=self.request.user,
                memberships__left_at__isnull=True,
            )
        except Group.DoesNotExist:
            return GroupMembership.objects.none()
        return GroupMembership.objects.filter(
            group=group
        ).select_related("user", "invited_by").order_by("-joined_at")


@extend_schema(tags=["Groups"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_member_view(request, pk):
    """Add a new member to the group."""
    try:
        group = Group.objects.get(
            id=pk,
            memberships__user=request.user,
            memberships__left_at__isnull=True,
        )
    except Group.DoesNotExist:
        return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    # Only admins can add members
    if not GroupMembership.objects.filter(
        group=group, user=request.user,
        role=GroupMembership.Role.ADMIN, left_at__isnull=True,
    ).exists():
        return Response(
            {"error": "Only group admins can add members."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = AddMemberSerializer(
        data=request.data, context={"group": group, "request": request}
    )
    serializer.is_valid(raise_exception=True)

    membership = GroupMembership.objects.create(
        group=group,
        user=serializer.validated_data["user"],
        joined_at=serializer.validated_data["joined_at"],
        role=serializer.validated_data["role"],
        invited_by=request.user,
    )

    return Response(
        GroupMembershipSerializer(membership).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(tags=["Groups"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def leave_group_view(request, pk):
    """Leave a group (set left_at on membership)."""
    try:
        group = Group.objects.get(id=pk)
        membership = GroupMembership.objects.get(
            group=group, user=request.user, left_at__isnull=True
        )
    except (Group.DoesNotExist, GroupMembership.DoesNotExist):
        return Response(
            {"error": "Active membership not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = LeaveMemberSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    left_at = serializer.validated_data.get("left_at") or timezone.now().date()
    membership.left_at = left_at
    membership.save(update_fields=["left_at"])

    return Response(
        {"message": f"You have left the group as of {left_at}."},
        status=status.HTTP_200_OK,
    )


@extend_schema(tags=["Groups"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_member_view(request, pk, user_id):
    """Admin removes a member from the group."""
    try:
        group = Group.objects.get(id=pk)
    except Group.DoesNotExist:
        return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    # Only admins can remove members
    if not GroupMembership.objects.filter(
        group=group, user=request.user,
        role=GroupMembership.Role.ADMIN, left_at__isnull=True,
    ).exists():
        return Response(
            {"error": "Only group admins can remove members."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        membership = GroupMembership.objects.get(
            group=group, user_id=user_id, left_at__isnull=True
        )
    except GroupMembership.DoesNotExist:
        return Response(
            {"error": "Active membership not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    membership.left_at = timezone.now().date()
    membership.save(update_fields=["left_at"])

    return Response({"message": "Member removed successfully."}, status=status.HTTP_200_OK)
