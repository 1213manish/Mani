"""
Balances views.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from apps.groups.models import Group
from .engine import BalanceEngine

User = get_user_model()


def get_member_group_or_404(user, group_id):
    return get_object_or_404(
        Group, id=group_id,
        memberships__user=user, memberships__left_at__isnull=True, is_active=True,
    )


@extend_schema(tags=["Balances"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def group_balances_view(request, group_id):
    """
    Get net balance summary for all members of a group.
    Returns: {user_id: net_balance}
    Positive = owed money, Negative = owes money.
    """
    group = get_member_group_or_404(request.user, group_id)
    engine = BalanceEngine(group)
    balances = engine.compute_group_balances()

    # Enrich with user data
    user_ids = list(balances.keys())
    users = {str(u.id): u for u in User.objects.filter(id__in=user_ids)}

    result = []
    for user_id, balance in sorted(balances.items(), key=lambda x: x[1], reverse=True):
        user = users.get(user_id)
        result.append(
            {
                "user_id": user_id,
                "user_name": user.full_name if user else "Unknown",
                "email": user.email if user else "",
                "net_balance": str(balance.quantize(Decimal("0.01"))),
                "status": "creditor" if balance > 0 else ("debtor" if balance < 0 else "settled"),
            }
        )

    return Response(
        {
            "group_id": str(group.id),
            "group_name": group.name,
            "balances": result,
        }
    )


@extend_schema(tags=["Balances"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def simplified_settlements_view(request, group_id):
    """
    Get the minimal set of transactions needed to settle all debts.
    Uses debt minimization (greedy two-heap) algorithm.
    """
    group = get_member_group_or_404(request.user, group_id)
    engine = BalanceEngine(group)
    balances = engine.compute_group_balances()
    transactions = engine.simplify_debts(balances)

    return Response(
        {
            "group_id": str(group.id),
            "group_name": group.name,
            "transactions": transactions,
            "transaction_count": len(transactions),
        }
    )


@extend_schema(tags=["Balances"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def explain_balance_view(request, group_id):
    """
    Get a full explainable breakdown of a user's balance in a group.
    Query params: ?user_id=<uuid> (defaults to current user)
    """
    group = get_member_group_or_404(request.user, group_id)

    user_id = request.query_params.get("user_id", str(request.user.id))
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found.", "code": "NOT_FOUND"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Only group members can view other members' balances
    if not group.memberships.filter(user=target_user).exists():
        return Response(
            {"error": "User has never been a member of this group."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    engine = BalanceEngine(group)
    explanation = engine.explain_balance(target_user)

    return Response(explanation)
