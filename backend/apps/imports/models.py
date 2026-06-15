"""
Imports app models: ImportJob and ImportAnomaly.

DESIGN:
- ImportJob tracks the full lifecycle of a CSV import.
- ImportAnomaly records each detected issue with full context.
- Nothing is deleted automatically — all actions require user approval.
- The original file is NEVER modified.
"""

from django.db import models
from django.contrib.auth import get_user_model

from apps.core.models import BaseModel

User = get_user_model()


class ImportJob(BaseModel):
    """Tracks a CSV import from upload to completion."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARSING = "PARSING", "Parsing"
        AWAITING_APPROVAL = "AWAITING_APPROVAL", "Awaiting Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="import_jobs",
        db_index=True,
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="import_jobs",
    )
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_hash = models.CharField(max_length=64, db_index=True)  # SHA-256

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Parsing stats
    rows_total = models.IntegerField(default=0)
    rows_imported = models.IntegerField(default=0)
    rows_skipped = models.IntegerField(default=0)
    anomalies_count = models.IntegerField(default=0)

    # Error message if status=FAILED
    error_message = models.TextField(blank=True, null=True)

    # Report file path (generated after import)
    report_path = models.CharField(max_length=500, blank=True, null=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "import_jobs"
        verbose_name = "Import Job"
        verbose_name_plural = "Import Jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Import #{self.id} ({self.file_name}) — {self.status}"


class ImportAnomaly(BaseModel):
    """
    Records a single detected anomaly in an import job.

    Every anomaly has:
    - type: what kind of anomaly
    - severity: ERROR (blocks import) | WARNING (ask approval) | INFO (informational)
    - recommendation: what the system suggests
    - action_taken: what was done (null until resolved)
    - status: PENDING | APPROVED | REJECTED | AUTO_RESOLVED
    """

    class AnomalyType(models.TextChoices):
        DUPLICATE_EXACT = "DUPLICATE_EXACT", "Exact Duplicate"
        DUPLICATE_POSSIBLE = "DUPLICATE_POSSIBLE", "Possible Duplicate"
        NEGATIVE_VALUE = "NEGATIVE_VALUE", "Negative Value"
        SETTLEMENT_AS_EXPENSE = "SETTLEMENT_AS_EXPENSE", "Settlement Recorded as Expense"
        MISSING_PAYER = "MISSING_PAYER", "Missing Payer"
        INVALID_DATE = "INVALID_DATE", "Invalid Date"
        FUTURE_DATE = "FUTURE_DATE", "Future Date"
        CURRENCY_MISMATCH = "CURRENCY_MISMATCH", "Currency Mismatch"
        UNKNOWN_MEMBER = "UNKNOWN_MEMBER", "Unknown Member"
        MEMBER_NOT_ACTIVE = "MEMBER_NOT_ACTIVE", "Member Not Active on Expense Date"
        INCONSISTENT_SPLIT = "INCONSISTENT_SPLIT", "Inconsistent Split Total"
        MALFORMED_ROW = "MALFORMED_ROW", "Malformed Row"
        BLANK_MANDATORY_FIELD = "BLANK_MANDATORY_FIELD", "Blank Mandatory Field"
        CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE", "Conflicting Duplicate Entry"
        AMOUNT_OUTLIER = "AMOUNT_OUTLIER", "Amount Outlier"

    class Severity(models.TextChoices):
        ERROR = "ERROR", "Error"
        WARNING = "WARNING", "Warning"
        INFO = "INFO", "Info"

    class AnomalyStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        AUTO_RESOLVED = "AUTO_RESOLVED", "Auto Resolved"

    import_job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name="anomalies",
        db_index=True,
    )
    row_number = models.IntegerField()
    raw_data = models.JSONField()  # Original CSV row data
    anomaly_type = models.CharField(max_length=30, choices=AnomalyType.choices, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, db_index=True)
    description = models.TextField()
    recommendation = models.TextField()
    action_taken = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=15,
        choices=AnomalyStatus.choices,
        default=AnomalyStatus.PENDING,
        db_index=True,
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_anomalies",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "import_anomalies"
        verbose_name = "Import Anomaly"
        verbose_name_plural = "Import Anomalies"
        ordering = ["row_number", "severity"]

    def __str__(self):
        return f"[{self.severity}] Row {self.row_number}: {self.anomaly_type}"
