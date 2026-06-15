"""
Settlements app models.

CRITICAL DESIGN: Settlements are SEPARATE from expenses.
They represent actual money transfers to settle debts.
A settlement is NEVER treated as an expense in balance calculations.
"""

from django.db import models
from django.contrib.auth import get_user_model

from apps.core.models import BaseModel

User = get_user_model()


class Settlement(BaseModel):
    """
    Records an actual money transfer between two group members.

    payer → pays money → receiver
    This reduces payer's debt to receiver.
    """

    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="settlements",
        db_index=True,
    )
    payer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="payments_made",
        db_index=True,
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="payments_received",
        db_index=True,
    )
    amount = models.DecimalField(max_digits=15, decimal_places=4)
    currency = models.ForeignKey(
        "currencies.Currency",
        on_delete=models.PROTECT,
        related_name="settlements",
    )
    settlement_date = models.DateField(db_index=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_settlements",
    )

    class Meta:
        db_table = "settlements"
        verbose_name = "Settlement"
        verbose_name_plural = "Settlements"
        ordering = ["-settlement_date", "-created_at"]

    def __str__(self):
        return (
            f"{self.payer.email} → {self.receiver.email}: "
            f"{self.currency.code} {self.amount} on {self.settlement_date}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.payer == self.receiver:
            raise ValidationError("Payer and receiver cannot be the same person.")
        if self.amount <= 0:
            raise ValidationError("Settlement amount must be positive.")
