"""
Currencies app models.

Supported currencies: INR (primary), USD (reference for imports/display).
Exchange rates are stored per-expense, never overwritten (auditability).
"""

from django.db import models
from apps.core.models import BaseModel


class Currency(BaseModel):
    """Supported currency definition."""

    code = models.CharField(max_length=3, unique=True, db_index=True)  # INR, USD
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "currencies"
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.symbol})"
