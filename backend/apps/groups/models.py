"""
Groups app models: Group and GroupMembership (timeline-aware).

KEY DESIGN DECISIONS:
- GroupMembership stores exact join/leave dates.
- left_at = NULL means currently active.
- Expense validity is checked against this timeline:
    expense_date >= joined_at AND (left_at IS NULL OR expense_date <= left_at)
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import BaseModel

User = get_user_model()


class Group(BaseModel):
    """
    An expense-sharing group.

    A group has a name, description, and a default currency.
    Members join and leave via GroupMembership timeline records.
    """

    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_groups",
    )
    default_currency = models.ForeignKey(
        "currencies.Currency",
        on_delete=models.PROTECT,
        related_name="groups",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    avatar_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "groups"
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_active_members(self, as_of_date=None):
        """Return users who are active members on or at a given date."""
        if as_of_date is None:
            as_of_date = timezone.now().date()
        return User.objects.filter(
            group_memberships__group=self,
            group_memberships__joined_at__lte=as_of_date,
        ).filter(
            models.Q(group_memberships__left_at__isnull=True)
            | models.Q(group_memberships__left_at__gte=as_of_date)
        ).distinct()

    def is_member(self, user, as_of_date=None):
        """Check if user is an active member on a given date."""
        if as_of_date is None:
            as_of_date = timezone.now().date()
        return GroupMembership.objects.filter(
            group=self,
            user=user,
            joined_at__lte=as_of_date,
        ).filter(
            models.Q(left_at__isnull=True) | models.Q(left_at__gte=as_of_date)
        ).exists()


class GroupMembership(BaseModel):
    """
    Tracks membership timeline for a user in a group.

    INVARIANTS:
    - A user cannot have two overlapping active memberships in the same group.
    - left_at must be >= joined_at.
    - left_at = NULL means currently active.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
        db_index=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="group_memberships",
        db_index=True,
    )
    joined_at = models.DateField(db_index=True)
    left_at = models.DateField(null=True, blank=True, db_index=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_memberships",
    )

    class Meta:
        db_table = "group_memberships"
        verbose_name = "Group Membership"
        verbose_name_plural = "Group Memberships"
        ordering = ["joined_at"]
        constraints = [
            # A user can only be an active (left_at=NULL) member once per group
            models.UniqueConstraint(
                fields=["group", "user"],
                condition=models.Q(left_at__isnull=True),
                name="unique_active_membership",
            )
        ]

    def __str__(self):
        status = "active" if self.left_at is None else f"left {self.left_at}"
        return f"{self.user.email} in {self.group.name} ({status})"

    @property
    def is_active(self):
        if self.left_at is None:
            return True
        return self.left_at >= timezone.now().date()

    def clean(self):
        if self.left_at and self.joined_at and self.left_at < self.joined_at:
            raise ValidationError("left_at cannot be before joined_at.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
