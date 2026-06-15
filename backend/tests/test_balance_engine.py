"""
Tests for the Balance Engine — the core financial calculation module.

Tests cover:
1. Basic net balance calculation
2. Debt minimization (greedy algorithm correctness)
3. Membership timeline enforcement
4. Settlement application
5. Explainability completeness
6. Zero-sum invariant
"""

import pytest
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.currencies.models import Currency
from apps.groups.models import Group, GroupMembership
from apps.expenses.models import Expense, ExpenseSplit
from apps.settlements.models import Settlement
from apps.balances.engine import BalanceEngine

User = get_user_model()


@pytest.mark.django_db
class TestBalanceEngine(TestCase):
    def setUp(self):
        self.inr = Currency.objects.create(code="INR", name="Indian Rupee", symbol="₹")

        self.alice = User.objects.create_user(
            email="alice@test.com", username="alice",
            first_name="Alice", last_name="A", password="test"
        )
        self.bob = User.objects.create_user(
            email="bob@test.com", username="bob",
            first_name="Bob", last_name="B", password="test"
        )
        self.charlie = User.objects.create_user(
            email="charlie@test.com", username="charlie",
            first_name="Charlie", last_name="C", password="test"
        )

        self.group = Group.objects.create(
            name="Test Group", created_by=self.alice, default_currency=self.inr
        )
        for user in [self.alice, self.bob, self.charlie]:
            GroupMembership.objects.create(
                group=self.group, user=user, joined_at=date(2024, 1, 1)
            )

    def _create_expense(self, title, amount, paid_by, expense_date, splits):
        """Helper: create expense and splits."""
        expense = Expense.objects.create(
            title=title, amount=amount, currency=self.inr,
            original_amount=amount, original_currency=self.inr,
            exchange_rate=Decimal("1.0"), converted_amount=amount,
            paid_by=paid_by, expense_date=expense_date, group=self.group,
            split_type=Expense.SplitType.EQUAL, created_by=paid_by,
        )
        for user, owed in splits:
            ExpenseSplit.objects.create(
                expense=expense, user=user,
                owed_amount=owed, share_amount=owed,
            )
        return expense

    def test_zero_sum_invariant(self):
        """Sum of all net balances must always equal zero."""
        self._create_expense(
            "Dinner", Decimal("300"), self.alice, date(2024, 2, 1),
            [(self.alice, Decimal("100")), (self.bob, Decimal("100")), (self.charlie, Decimal("100"))]
        )
        engine = BalanceEngine(self.group)
        balances = engine.compute_group_balances()
        total = sum(balances.values())
        self.assertAlmostEqual(float(total), 0.0, places=2)

    def test_alice_paid_bob_and_charlie_owe(self):
        """Alice paid 300 for 3. Bob and Charlie each owe Alice 100."""
        self._create_expense(
            "Lunch", Decimal("300"), self.alice, date(2024, 2, 1),
            [(self.alice, Decimal("100")), (self.bob, Decimal("100")), (self.charlie, Decimal("100"))]
        )
        engine = BalanceEngine(self.group)
        balances = engine.compute_group_balances()

        alice_id = str(self.alice.id)
        bob_id = str(self.bob.id)
        charlie_id = str(self.charlie.id)

        self.assertEqual(balances[alice_id], Decimal("200"))  # Alice is owed 200
        self.assertEqual(balances[bob_id], Decimal("-100"))   # Bob owes 100
        self.assertEqual(balances[charlie_id], Decimal("-100"))

    def test_simplified_debts_minimization(self):
        """Simplified debts should reduce transactions to minimum."""
        # Alice paid 300, Bob paid 0, Charlie paid 0
        self._create_expense(
            "Expense", Decimal("300"), self.alice, date(2024, 2, 1),
            [(self.alice, Decimal("100")), (self.bob, Decimal("100")), (self.charlie, Decimal("100"))]
        )
        engine = BalanceEngine(self.group)
        balances = engine.compute_group_balances()
        transactions = engine.simplify_debts(balances)

        # Should have exactly 2 transactions (Bob → Alice, Charlie → Alice)
        self.assertEqual(len(transactions), 2)
        for t in transactions:
            self.assertEqual(t["to_user_id"], str(self.alice.id))
            self.assertEqual(t["amount"], Decimal("100.00"))

    def test_settlement_reduces_debt(self):
        """A settlement should reduce the debtor's net balance."""
        self._create_expense(
            "Expense", Decimal("300"), self.alice, date(2024, 2, 1),
            [(self.alice, Decimal("100")), (self.bob, Decimal("100")), (self.charlie, Decimal("100"))]
        )

        # Bob settles 50 with Alice
        Settlement.objects.create(
            group=self.group, payer=self.bob, receiver=self.alice,
            amount=Decimal("50"), currency=self.inr,
            settlement_date=date(2024, 2, 5), created_by=self.bob,
        )

        engine = BalanceEngine(self.group)
        balances = engine.compute_group_balances()

        bob_id = str(self.bob.id)
        alice_id = str(self.alice.id)

        # Bob still owes 50 (100 - 50 settlement)
        self.assertEqual(balances[bob_id], Decimal("-50"))
        # Alice is owed 150 (200 - 50 received)
        self.assertEqual(balances[alice_id], Decimal("150"))

    def test_full_settlement_zero_balance(self):
        """After full settlement, all balances should be zero."""
        self._create_expense(
            "Expense", Decimal("200"), self.alice, date(2024, 2, 1),
            [(self.alice, Decimal("100")), (self.bob, Decimal("100"))]
        )
        Settlement.objects.create(
            group=self.group, payer=self.bob, receiver=self.alice,
            amount=Decimal("100"), currency=self.inr,
            settlement_date=date(2024, 2, 10), created_by=self.bob,
        )

        engine = BalanceEngine(self.group)
        balances = engine.compute_group_balances()
        for balance in balances.values():
            self.assertAlmostEqual(float(balance), 0.0, places=2)

    def test_explain_balance_no_magic_numbers(self):
        """explain_balance must account for every cent."""
        self._create_expense(
            "Hotel", Decimal("900"), self.alice, date(2024, 2, 1),
            [(self.alice, Decimal("300")), (self.bob, Decimal("300")), (self.charlie, Decimal("300"))]
        )

        engine = BalanceEngine(self.group)
        explanation = engine.explain_balance(self.alice)

        # Net balance should match sum of expense contributions
        net = Decimal(explanation["net_balance"])
        you_owed = Decimal(explanation["you_are_owed"])
        you_owe = Decimal(explanation["you_owe"])
        self.assertEqual(net, you_owed - you_owe)

    def test_complex_debt_minimization(self):
        """
        Test complex scenario:
        Alice → Bob: 100 (Bob owes Alice)
        Bob → Charlie: 200 (Charlie owes Bob)
        Charlie → Alice: 150 (Alice owes Charlie)
        Should simplify to minimal transactions.
        """
        # Alice paid 200 for Alice+Bob
        self._create_expense(
            "E1", Decimal("200"), self.alice, date(2024, 2, 1),
            [(self.alice, Decimal("100")), (self.bob, Decimal("100"))]
        )
        # Bob paid 400 for Bob+Charlie
        self._create_expense(
            "E2", Decimal("400"), self.bob, date(2024, 2, 2),
            [(self.bob, Decimal("200")), (self.charlie, Decimal("200"))]
        )
        # Charlie paid 300 for Charlie+Alice
        self._create_expense(
            "E3", Decimal("300"), self.charlie, date(2024, 2, 3),
            [(self.charlie, Decimal("150")), (self.alice, Decimal("150"))]
        )

        engine = BalanceEngine(self.group)
        balances = engine.compute_group_balances()

        # Verify zero-sum
        total = sum(balances.values())
        self.assertAlmostEqual(float(total), 0.0, places=2)

        # Verify simplification
        transactions = engine.simplify_debts(balances)
        # Simplified should be ≤ n-1 transactions
        self.assertLessEqual(len(transactions), 2)


@pytest.mark.django_db
class TestMembershipTimeline(TestCase):
    """Tests for membership timeline enforcement."""

    def setUp(self):
        self.inr = Currency.objects.create(code="INR_T", name="Indian Rupee T", symbol="₹")
        self.admin = User.objects.create_user(
            email="admin@test.com", username="admin_t",
            first_name="Admin", last_name="T", password="test"
        )
        self.late_joiner = User.objects.create_user(
            email="late@test.com", username="late_t",
            first_name="Late", last_name="T", password="test"
        )
        self.early_leaver = User.objects.create_user(
            email="early@test.com", username="early_t",
            first_name="Early", last_name="T", password="test"
        )

        self.group = Group.objects.create(
            name="Timeline Test Group", created_by=self.admin, default_currency=self.inr
        )
        GroupMembership.objects.create(
            group=self.group, user=self.admin, joined_at=date(2024, 1, 1)
        )
        GroupMembership.objects.create(
            group=self.group, user=self.late_joiner, joined_at=date(2024, 4, 15)
        )
        GroupMembership.objects.create(
            group=self.group, user=self.early_leaver,
            joined_at=date(2024, 1, 1), left_at=date(2024, 3, 31)
        )

    def test_early_leaver_not_active_after_leave_date(self):
        """Member who left March 31 should not be active on April 1."""
        self.assertFalse(self.group.is_member(self.early_leaver, date(2024, 4, 1)))

    def test_early_leaver_active_before_leave_date(self):
        """Member who left March 31 should be active on March 30."""
        self.assertTrue(self.group.is_member(self.early_leaver, date(2024, 3, 30)))

    def test_late_joiner_not_active_before_join_date(self):
        """Member who joined April 15 should not be active on April 14."""
        self.assertFalse(self.group.is_member(self.late_joiner, date(2024, 4, 14)))

    def test_late_joiner_active_on_join_date(self):
        """Member who joined April 15 should be active on April 15."""
        self.assertTrue(self.group.is_member(self.late_joiner, date(2024, 4, 15)))

    def test_get_active_members_on_date(self):
        """get_active_members should return correct members for a given date."""
        # On March 15: admin + early_leaver (late_joiner not yet joined)
        members = list(self.group.get_active_members(date(2024, 3, 15)))
        member_ids = {str(m.id) for m in members}
        self.assertIn(str(self.admin.id), member_ids)
        self.assertIn(str(self.early_leaver.id), member_ids)
        self.assertNotIn(str(self.late_joiner.id), member_ids)
