"""
Accounts app: Custom User model, email verification, password reset tokens.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDModel, TimeStampedModel


class User(UUIDModel, AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    - Uses UUID pk instead of integer
    - Email is unique and used as primary identifier
    - Adds email verification and avatar support
    """

    email = models.EmailField(unique=True, db_index=True)
    is_email_verified = models.BooleanField(default=False)
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True, max_length=500)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Remove username uniqueness — we use email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    @property
    def full_name(self):
        return self.get_full_name() or self.username


class EmailVerificationToken(UUIDModel, TimeStampedModel):
    """Token used for email verification flow."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_token",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = "email_verification_tokens"

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class PasswordResetToken(UUIDModel, TimeStampedModel):
    """Token used for password reset flow."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_tokens"

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
