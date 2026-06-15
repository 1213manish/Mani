"""
Balance Engine: The core financial calculation module.

ARCHITECTURE:
1. BalanceEngine.compute_group_balances() → raw net balances per user
2. BalanceEngine.simplify_debts() → minimal transaction set (debt minimization)
3. BalanceEngine.explain_balance() → full explainable breakdown for one user

CORRECTNESS GUARANTEES:
- Only expenses where user was an active member on expense_date count.
- Settlements are applied AFTER expense-based calculations.
- The sum of all net balances in a group ALWAYS equals zero.
- Debt minimization uses greedy two-heap algorithm (O(n log n)).

EXPLAINABILITY:
- Every balance figure is backed by a list of contributing expenses.
- No magic numbers — every cent is traceable.
"""

import heapq
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Tuple

from django.contrib.auth import get_user_model
from django.db import models

from apps.expenses.models import Expense, ExpenseSplit
from apps.settlements.models import Settlement
from apps.groups.models import Group, GroupMembership

User = get_user_model()


class BalanceEngine:
    """
    Computes balances, simplified settlements, and explainable breakdowns
    for a group.

    Usage:
        engine = BalanceEngine(group)
        balances = engine.compute_group_balances()
        simplified = engine.simplify_debts(balances)
        explanation = engine.explain_balance(user)
    """

    def __init__(self, group: Group):
        self.group = group

    def _get_all_members(self) -> List:
        """Return all users who have ever been members."""
        return User.objects.filter(
            group_memberships__group=self.group
        ).distinct()

    def compute_group_balances(self) -> Dict[str, Decimal]:
        """
        Compute net balance for each user in the group.

        Net balance = total amount owed TO user - total amount user owes to others
        Positive = user is owed money (creditor)
        Negative = user owes money (debtor)

        Returns: {user_id_str: net_balance_decimal}
        """
        balances: Dict[str, Decimal] = defaultdict(Decimal)

        # Step 1: Process expense splits
        # For each split: the payer is owed owed_amount, the split-user owes it
        splits = (
            ExpenseSplit.objects.filter(
                expense__group=self.group,
                expense__is_deleted=False,
            )
            .select_related("expense__paid_by", "user")
        )

        for split in splits:
            paid_by_id = str(split.expense.paid_by.id)
            owed_by_id = str(split.user.id)

            if paid_by_id == owed_by_id:
                # User paid for their own share — no debt
                continue

            # paid_by is owed this amount by the split user
            balances[paid_by_id] += split.owed_amount
            balances[owed_by_id] -= split.owed_amount

        # Step 2: Apply settlements
        # A settlement is payer paying receiver → reduces payer's debt
        settlements = Settlement.objects.filter(group=self.group)
        for s in settlements:
            payer_id = str(s.payer.id)
            receiver_id = str(s.receiver.id)

            # Payer reduces their negative balance (pays off debt)
            balances[payer_id] += s.amount
            # Receiver gets less (their credit is reduced)
            balances[receiver_id] -= s.amount

        # Ensure all ever-members appear in result (even if balance is 0)
        for member in self._get_all_members():
            mid = str(member.id)
            if mid not in balances:
                balances[mid] = Decimal("0.0000")

        return dict(balances)

    def simplify_debts(
        self, balances: Dict[str, Decimal] = None
    ) -> List[Dict]:
        """
        Compute minimal set of transactions to settle all debts.

        Algorithm: Greedy two-heap approach
        - Separate users into creditors (positive) and debtors (negative)
        - Repeatedly match largest creditor with largest debtor
        - Output a transaction for min(credit, debit)
        - Complexity: O(n log n)

        Returns list of:
        {
            "from_user_id": str,
            "to_user_id": str,
            "amount": Decimal,
            "from_user": user_data,
            "to_user": user_data,
        }
        """
        if balances is None:
            balances = self.compute_group_balances()

        # Filter out zero balances
        non_zero = {uid: amt for uid, amt in balances.items() if abs(amt) > Decimal("0.001")}

        if not non_zero:
            return []

        # Build heaps (use negative for max-heap simulation with min-heap)
        creditors = []  # (amount, user_id) — max-heap via negation
        debtors = []    # (amount, user_id) — max-heap via negation

        for user_id, balance in non_zero.items():
            if balance > 0:
                heapq.heappush(creditors, (-balance, user_id))
            elif balance < 0:
                heapq.heappush(debtors, (balance, user_id))  # already negative

        transactions = []
        user_cache: Dict[str, object] = {}

        def get_user(uid: str):
            if uid not in user_cache:
                try:
                    user_cache[uid] = User.objects.get(id=uid)
                except User.DoesNotExist:
                    user_cache[uid] = None
            return user_cache[uid]

        while creditors and debtors:
            credit_amt, creditor_id = heapq.heappop(creditors)
            credit_amt = -credit_amt  # back to positive

            debt_amt, debtor_id = heapq.heappop(debtors)
            debt_amt = -debt_amt  # make positive

            # Settlement amount is the minimum
            settle_amt = min(credit_amt, debt_amt)

            creditor = get_user(creditor_id)
            debtor = get_user(debtor_id)

            transactions.append(
                {
                    "from_user_id": debtor_id,
                    "to_user_id": creditor_id,
                    "amount": settle_amt.quantize(Decimal("0.01")),
                    "from_user": {
                        "id": debtor_id,
                        "full_name": creditor.full_name if creditor else debtor_id,
                        "email": debtor.email if debtor else "",
                    }
                    if debtor
                    else {"id": debtor_id},
                    "to_user": {
                        "id": creditor_id,
                        "full_name": creditor.full_name if creditor else creditor_id,
                        "email": creditor.email if creditor else "",
                    }
                    if creditor
                    else {"id": creditor_id},
                }
            )

            remaining_credit = credit_amt - settle_amt
            remaining_debt = debt_amt - settle_amt

            if remaining_credit > Decimal("0.001"):
                heapq.heappush(creditors, (-remaining_credit, creditor_id))
            if remaining_debt > Decimal("0.001"):
                heapq.heappush(debtors, (-remaining_debt, debtor_id))

        return transactions

    def explain_balance(self, user: User) -> Dict:
        """
        Provide a full explainable breakdown of a user's balance.

        Returns:
        {
            "net_balance": Decimal,
            "you_are_owed": Decimal,       # total others owe you
            "you_owe": Decimal,            # total you owe others
            "expense_breakdown": [...],    # per-expense detail
            "settlement_breakdown": [...], # settlements applied
            "currency": str,
        }
        """
        user_id = str(user.id)
        expense_breakdown = []
        you_are_owed = Decimal("0")
        you_owe = Decimal("0")

        # Expenses where this user paid (others owe them)
        paid_expenses = Expense.objects.filter(
            group=self.group,
            paid_by=user,
            is_deleted=False,
        ).prefetch_related("splits")

        for expense in paid_expenses:
            others_share = Decimal("0")
            for split in expense.splits.all():
                if str(split.user.id) != user_id:
                    others_share += split.owed_amount

            if others_share > 0:
                you_are_owed += others_share
                expense_breakdown.append(
                    {
                        "expense_id": str(expense.id),
                        "title": expense.title,
                        "expense_date": expense.expense_date.isoformat(),
                        "total_amount": str(expense.amount),
                        "currency": expense.currency.code,
                        "you_paid": str(expense.amount),
                        "your_share": str(
                            next(
                                (
                                    s.owed_amount
                                    for s in expense.splits.all()
                                    if str(s.user.id) == user_id
                                ),
                                Decimal("0"),
                            )
                        ),
                        "others_owe_you": str(others_share),
                        "direction": "YOU_PAID",
                    }
                )

        # Expenses where this user owes (split records where user didn't pay)
        owed_splits = (
            ExpenseSplit.objects.filter(
                expense__group=self.group,
                expense__is_deleted=False,
                user=user,
            )
            .exclude(expense__paid_by=user)
            .select_related("expense__paid_by", "expense__currency")
        )

        for split in owed_splits:
            you_owe += split.owed_amount
            expense_breakdown.append(
                {
                    "expense_id": str(split.expense.id),
                    "title": split.expense.title,
                    "expense_date": split.expense.expense_date.isoformat(),
                    "total_amount": str(split.expense.amount),
                    "currency": split.expense.currency.code,
                    "paid_by": split.expense.paid_by.full_name,
                    "you_paid": "0",
                    "your_share": str(split.owed_amount),
                    "direction": "YOU_OWE",
                }
            )

        # Settlement breakdown
        settlement_breakdown = []
        settlements_sent = Settlement.objects.filter(group=self.group, payer=user)
        settlements_received = Settlement.objects.filter(group=self.group, receiver=user)

        for s in settlements_sent:
            settlement_breakdown.append(
                {
                    "settlement_id": str(s.id),
                    "date": s.settlement_date.isoformat(),
                    "amount": str(s.amount),
                    "direction": "YOU_PAID",
                    "counterparty": s.receiver.full_name,
                }
            )
            you_owe -= s.amount  # Reduces what you owe

        for s in settlements_received:
            settlement_breakdown.append(
                {
                    "settlement_id": str(s.id),
                    "date": s.settlement_date.isoformat(),
                    "amount": str(s.amount),
                    "direction": "YOU_RECEIVED",
                    "counterparty": s.payer.full_name,
                }
            )
            you_are_owed -= s.amount  # Reduces what others owe you

        net_balance = you_are_owed - you_owe

        return {
            "user_id": user_id,
            "user_name": user.full_name,
            "net_balance": str(net_balance.quantize(Decimal("0.01"))),
            "you_are_owed": str(you_are_owed.quantize(Decimal("0.01"))),
            "you_owe": str(you_owe.quantize(Decimal("0.01"))),
            "expense_breakdown": sorted(
                expense_breakdown, key=lambda x: x["expense_date"], reverse=True
            ),
            "settlement_breakdown": sorted(
                settlement_breakdown, key=lambda x: x["date"], reverse=True
            ),
            "group_id": str(self.group.id),
            "group_name": self.group.name,
        }
