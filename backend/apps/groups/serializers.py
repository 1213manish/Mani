"""
Groups serializers.
"""

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserPublicSerializer
from .models import Group, GroupMembership


class GroupMembershipSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    invited_by = UserPublicSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = GroupMembership
        fields = [
            "id", "user", "role", "joined_at", "left_at",
            "is_active", "invited_by", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class GroupSerializer(serializers.ModelSerializer):
    created_by = UserPublicSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    current_user_membership = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id", "name", "description", "created_by",
            "default_currency", "is_active", "avatar_url",
            "member_count", "current_user_membership",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_member_count(self, obj):
        return obj.memberships.filter(left_at__isnull=True).count()

    def get_current_user_membership(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.memberships.filter(
            user=request.user, left_at__isnull=True
        ).first()
        if membership:
            return GroupMembershipSerializer(membership).data
        return None


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name", "description", "default_currency", "avatar_url"]

    def create(self, validated_data):
        user = self.context["request"].user
        group = Group.objects.create(created_by=user, **validated_data)
        # Creator automatically becomes an admin member
        GroupMembership.objects.create(
            group=group,
            user=user,
            joined_at=timezone.now().date(),
            role=GroupMembership.Role.ADMIN,
        )
        return group


class AddMemberSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(
        choices=GroupMembership.Role.choices,
        default=GroupMembership.Role.MEMBER,
    )
    joined_at = serializers.DateField(required=False)

    def validate(self, attrs):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(id=attrs["user_id"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "User not found."})

        group = self.context["group"]

        # Check if already an active member
        if group.memberships.filter(user=user, left_at__isnull=True).exists():
            raise serializers.ValidationError(
                {"user_id": "User is already an active member of this group."}
            )

        attrs["user"] = user
        attrs.setdefault("joined_at", timezone.now().date())
        return attrs


class LeaveMemberSerializer(serializers.Serializer):
    left_at = serializers.DateField(required=False)

    def validate_left_at(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("left_at cannot be in the future.")
        return value
