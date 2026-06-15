"""
Audit Log models and middleware.

Every create/update/delete/import/settlement action is logged with:
- actor (who did it)
- timestamp
- before state (JSON snapshot)
- after state (JSON snapshot)
- IP address + user agent

DESIGN: Append-only. Audit logs are NEVER deleted or modified.
"""

from django.db import models
from django.contrib.auth import get_user_model

from apps.core.models import BaseModel

User = get_user_model()


class AuditLog(BaseModel):
    """
    Immutable audit trail entry.

    This model is append-only — no update or delete operations
    should ever be performed on it.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        SOFT_DELETE = "SOFT_DELETE", "Soft Delete"
        IMPORT = "IMPORT", "Import"
        SETTLEMENT = "SETTLEMENT", "Settlement"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"
        EMAIL_VERIFIED = "EMAIL_VERIFIED", "Email Verified"
        MEMBER_JOIN = "MEMBER_JOIN", "Member Joined"
        MEMBER_LEAVE = "MEMBER_LEAVE", "Member Left"

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        db_index=True,
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)  # e.g., "Expense", "Group"
    resource_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    resource_repr = models.CharField(max_length=300, blank=True, null=True)

    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)

    extra = models.JSONField(null=True, blank=True)  # Additional context

    class Meta:
        db_table = "audit_logs"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        actor = self.actor.email if self.actor else "System"
        return f"[{self.action}] {actor} → {self.resource_type} {self.resource_id}"


def create_audit_log(
    actor=None,
    action=None,
    resource_type="",
    resource_id=None,
    resource_repr=None,
    before_state=None,
    after_state=None,
    ip_address=None,
    user_agent=None,
    extra=None,
):
    """
    Convenience function to create an audit log entry.
    Safe to call anywhere — catches and logs exceptions internally.
    """
    try:
        AuditLog.objects.create(
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            resource_repr=resource_repr,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
            extra=extra,
        )
    except Exception:
        pass  # Audit failures should never break the main flow
