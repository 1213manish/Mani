"""
Expenses app models: Expense and ExpenseSplit.

KEY DESIGN DECISIONS:
1. All 4 split types (EQUAL, PERCENTAGE, EXACT, SHARES) stored explicitly in ExpenseSplit.
2. Original currency/amount are NEVER overwritten — auditability.
3. Exchange rate is stored at time of expense creation.
4. Membership timeline is validated on save (expense_date must fall in payer's active window).
5. Soft delete — expenses are never hard deleted.
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.core.models import BaseModel

User = get_user_model()


class Expense(BaseModel):
    """
    A shared expense within a group.

    IMMUTABILITY: original_amount and original_currency are write-once.
    AUDITABILITY: All changes tracked via AuditLog.
    TIMELINE: expense_date is validated against group membership for paid_by user.
    """

    class SplitType(models.TextChoices):
        EQUAL = "EQUAL", "Equal"
        PERCENTAGE = "PERCENTAGE", "Percentage"
        EXACT = "EXACT", "Exact Amount"
        SHARES = "SHARES", "Shares"

    # Core fields
    title = models.CharField(max_length=300, db_index=True)
    description = models.TextField(blank=True, null=True)

    # Amount fields — multi-currency aware
    amount = models.DecimalField(max_digits=15, decimal_places=4)
    currency = models.ForeignKey(
        "currencies.Currency",
        on_delete=models.PROTECT,
        related_name="expenses",
    )

    # Original values — NEVER modified after creation
    original_amount = models.DecimalField(max_digits=15, decimal_places=4)
    original_currency = models.ForeignKey(
        "currencies.Currency",
        on_delete=models.PROTECT,
        related_name="original_expenses",
    )
    exchange_rate = models.DecimalField(
        max_digits=20, decimal_places=8, default=Decimal("1.00000000")
    )
    converted_amount = models.DecimalField(max_digits=15, decimal_places=4)

    # Expense metadata
    paid_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="paid_expenses",
        db_index=True,
    )
    expense_date = models.DateField(db_index=True)
    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="expenses",
        db_index=True,
    )
    split_type = models.CharField(
        max_length=10,
        choices=SplitType.choices,
        default=SplitType.EQUAL,
        db_index=True,
    )

    # Optional extras
    notes = models.TextField(blank=True, null=True)
    receipt_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    # Soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_expenses",
    )

    # Creator
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_expenses",
    )

    # Import tracking
    import_job = models.ForeignKey(
        "imports.ImportJob",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imported_expenses",
    )

    class Meta:
        db_table = "expenses"
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ["-expense_date", "-created_at"]
        indexes = [
            models.Index(fields=["group", "expense_date"]),
            models.Index(fields=["group", "is_deleted"]),
            models.Index(fields=["paid_by", "expense_date"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.currency.code} {self.amount}"


class ExpenseSplit(BaseModel):
    """
    A single user's share of an expense.

    Every expense must have splits that sum to the expense total.
    The split_type determines which fields are populated:
    - EQUAL: owed_amount = expense.amount / member_count
    - PERCENTAGE: share_percentage is set, owed_amount derived
    - EXACT: owed_amount is directly set
    - SHARES: share_units is set, owed_amount derived

    AUDITABILITY: All splits are stored explicitly; no on-the-fly calculation.
    """

    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="splits",
        db_index=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="expense_splits",
        db_index=True,
    )

    # Split detail (populated based on split_type)
    share_amount = models.DecimalField(
        max_digits=15, decimal_places=4, default=Decimal("0.0000"),
        help_text="Raw split input value (percentage, shares, or exact amount)"
    )
    share_percentage = models.DecimalField(
        max_digits=8, decimal_places=4, default=Decimal("0.0000")
    )
    share_units = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0.0000")
    )

    # The final computed amount this user owes
    owed_amount = models.DecimalField(
        max_digits=15, decimal_places=4,
        help_text="Final amount this user owes for this expense"
    )

    is_settled = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "expense_splits"
        verbose_name = "Expense Split"
        verbose_name_plural = "Expense Splits"
        unique_together = [["expense", "user"]]

    def __str__(self):
        return f"{self.user.email} owes {self.owed_amount} for {self.expense.title}"
