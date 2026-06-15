"""
Expense serializers with split calculation logic.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserPublicSerializer
from apps.currencies.serializers import CurrencySerializer
from apps.groups.models import GroupMembership
from .models import Expense, ExpenseSplit


class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = [
            "id", "user", "share_amount", "share_percentage",
            "share_units", "owed_amount", "is_settled",
        ]


class ExpenseSplitInputSerializer(serializers.Serializer):
    """Input format for splits during expense creation."""
    user_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=4, required=False, default=Decimal("0")
    )
    percentage = serializers.DecimalField(
        max_digits=8, decimal_places=4, required=False, default=Decimal("0")
    )
    units = serializers.DecimalField(
        max_digits=10, decimal_places=4, required=False, default=Decimal("1")
    )


class ExpenseCreateSerializer(serializers.ModelSerializer):
    splits = ExpenseSplitInputSerializer(many=True, required=False)
    currency_code = serializers.CharField(write_only=True, required=False)
    exchange_rate = serializers.DecimalField(
        max_digits=20, decimal_places=8, required=False, default=Decimal("1.0")
    )

    class Meta:
        model = Expense
        fields = [
            "title", "description", "amount", "currency", "currency_code",
            "original_amount", "original_currency", "exchange_rate",
            "paid_by", "expense_date", "group", "split_type",
            "notes", "receipt_url", "category", "splits",
        ]

    def validate(self, attrs):
        group = attrs.get("group")
        expense_date = attrs.get("expense_date")
        paid_by = attrs.get("paid_by")

        # Validate paid_by is active member on expense_date
        if group and expense_date and paid_by:
            if not group.is_member(paid_by, expense_date):
                raise serializers.ValidationError(
                    {
                        "paid_by": (
                            f"User '{paid_by.email}' was not an active member "
                            f"of this group on {expense_date}."
                        )
                    }
                )

        # Set original values if not provided
        if not attrs.get("original_amount"):
            attrs["original_amount"] = attrs["amount"]
        if not attrs.get("original_currency"):
            attrs["original_currency"] = attrs["currency"]

        # Compute converted_amount
        exchange_rate = attrs.get("exchange_rate", Decimal("1.0"))
        attrs["converted_amount"] = attrs["amount"] * exchange_rate

        return attrs

    def _calculate_splits(self, expense, splits_data):
        """
        Calculate and create ExpenseSplit records based on split_type.

        EQUAL: amount / member_count, remainder goes to payer
        PERCENTAGE: verify sums to 100, compute each share
        EXACT: verify sums to total amount
        SHARES: proportional to unit weights
        """
        split_type = expense.split_type
        total = expense.amount
        group = expense.group
        expense_date = expense.expense_date

        split_objects = []

        if split_type == Expense.SplitType.EQUAL:
            # Auto-split among active members on expense_date
            active_members = group.get_active_members(expense_date)
            count = active_members.count()
            if count == 0:
                raise serializers.ValidationError("No active members in group on expense date.")

            per_person = (total / count).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            remainder = total - (per_person * count)

            for i, member in enumerate(active_members):
                amount = per_person + (remainder if i == 0 else Decimal("0"))  # Payer absorbs remainder
                split_objects.append(
                    ExpenseSplit(
                        expense=expense,
                        user=member,
                        owed_amount=amount,
                        share_amount=amount,
                        share_percentage=(Decimal("100") / count).quantize(Decimal("0.0001")),
                        share_units=Decimal("1"),
                    )
                )

        elif split_type == Expense.SplitType.PERCENTAGE:
            if not splits_data:
                raise serializers.ValidationError("Splits required for PERCENTAGE split type.")

            total_pct = sum(s.get("percentage", Decimal("0")) for s in splits_data)
            if abs(total_pct - Decimal("100")) > Decimal("0.01"):
                raise serializers.ValidationError(
                    f"Percentages must sum to 100. Got {total_pct}."
                )

            for split in splits_data:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=split["user_id"])
                pct = split.get("percentage", Decimal("0"))
                owed = (total * pct / 100).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                split_objects.append(
                    ExpenseSplit(
                        expense=expense, user=user,
                        share_percentage=pct, owed_amount=owed, share_amount=owed,
                    )
                )

        elif split_type == Expense.SplitType.EXACT:
            if not splits_data:
                raise serializers.ValidationError("Splits required for EXACT split type.")

            total_exact = sum(s.get("amount", Decimal("0")) for s in splits_data)
            if abs(total_exact - total) > Decimal("0.01"):
                raise serializers.ValidationError(
                    f"Exact amounts must sum to expense total ({total}). Got {total_exact}."
                )

            for split in splits_data:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=split["user_id"])
                owed = split.get("amount", Decimal("0"))
                split_objects.append(
                    ExpenseSplit(
                        expense=expense, user=user,
                        owed_amount=owed, share_amount=owed,
                    )
                )

        elif split_type == Expense.SplitType.SHARES:
            if not splits_data:
                raise serializers.ValidationError("Splits required for SHARES split type.")

            total_units = sum(s.get("units", Decimal("1")) for s in splits_data)

            for split in splits_data:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=split["user_id"])
                units = split.get("units", Decimal("1"))
                owed = (total * units / total_units).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
                split_objects.append(
                    ExpenseSplit(
                        expense=expense, user=user,
                        share_units=units, owed_amount=owed, share_amount=owed,
                    )
                )

        ExpenseSplit.objects.bulk_create(split_objects)

    def create(self, validated_data):
        splits_data = validated_data.pop("splits", [])
        validated_data["created_by"] = self.context["request"].user
        expense = Expense.objects.create(**validated_data)
        self._calculate_splits(expense, splits_data)
        return expense


class ExpenseSerializer(serializers.ModelSerializer):
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    paid_by = UserPublicSerializer(read_only=True)
    currency = CurrencySerializer(read_only=True)
    original_currency = CurrencySerializer(read_only=True)
    created_by = UserPublicSerializer(read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id", "title", "description",
            "amount", "currency",
            "original_amount", "original_currency", "exchange_rate", "converted_amount",
            "paid_by", "expense_date", "group", "split_type",
            "notes", "receipt_url", "category",
            "is_deleted", "created_by",
            "created_at", "updated_at",
            "splits",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]
