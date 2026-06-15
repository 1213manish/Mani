from rest_framework import serializers
from django.utils import timezone

from apps.accounts.serializers import UserPublicSerializer
from apps.currencies.serializers import CurrencySerializer
from .models import Settlement


class SettlementSerializer(serializers.ModelSerializer):
    payer = UserPublicSerializer(read_only=True)
    receiver = UserPublicSerializer(read_only=True)
    currency = CurrencySerializer(read_only=True)
    created_by = UserPublicSerializer(read_only=True)

    class Meta:
        model = Settlement
        fields = [
            "id", "group", "payer", "receiver",
            "amount", "currency", "settlement_date",
            "notes", "created_by", "created_at",
        ]
        read_only_fields = ["id", "created_at", "created_by"]


class SettlementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = [
            "payer", "receiver", "amount", "currency",
            "settlement_date", "notes",
        ]

    def validate(self, attrs):
        if attrs["payer"] == attrs["receiver"]:
            raise serializers.ValidationError(
                "Payer and receiver cannot be the same person."
            )
        if attrs["amount"] <= 0:
            raise serializers.ValidationError("Settlement amount must be positive.")

        # Validate both users are/were members of the group
        group = self.context["group"]
        date = attrs.get("settlement_date", timezone.now().date())

        for role, user in [("payer", attrs["payer"]), ("receiver", attrs["receiver"])]:
            if not group.memberships.filter(user=user).exists():
                raise serializers.ValidationError(
                    {role: f"User '{user.email}' has never been a member of this group."}
                )

        return attrs

    def create(self, validated_data):
        validated_data["group"] = self.context["group"]
        validated_data["created_by"] = self.context["request"].user
        return Settlement.objects.create(**validated_data)
