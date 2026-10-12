"""Custom User model and UsageLedger for VoiceClone identity, RBAC, and Quota Ledger (VC-100)."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Primary user identity with UUID identifier, plan tier, unlimited bypass, and quota ledger."""

    PLAN_FREE = "FREE"
    PLAN_CREATOR = "CREATOR"
    PLAN_PRO = "PRO"
    PLAN_UNLIMITED = "UNLIMITED"

    PLAN_CHOICES = (
        (PLAN_FREE, "Free Trial (5 min)"),
        (PLAN_CREATOR, "Creator Tier (30 min/month)"),
        (PLAN_PRO, "Pro Studio Tier (120 min/month)"),
        (PLAN_UNLIMITED, "Unlimited VIP / Owner Access"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Email Address")
    is_verified = models.BooleanField(
        default=False, help_text="Email ownership verification status"
    )
    plan = models.CharField(
        max_length=32, choices=PLAN_CHOICES, default=PLAN_FREE, db_index=True
    )
    is_unlimited = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Bypass all quotas, throttling, and duration limits (Owner / VIP / Whitelist)",
    )
    audio_seconds_quota = models.PositiveIntegerField(
        default=300,  # 5 minutes free trial
        help_text="Total allowed seconds in current billing cycle",
    )
    audio_seconds_used = models.FloatField(
        default=0.0,
        help_text="Accumulated audio seconds consumed in current cycle",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.username} [{self.plan}] <{self.email}>"

    @property
    def is_owner_or_unlimited(self) -> bool:
        """Check if user has permanent unlimited permissions (Owner or whitelisted)."""
        return bool(
            self.is_superuser
            or self.is_staff
            or self.is_unlimited
            or self.plan == self.PLAN_UNLIMITED
        )

    def has_available_quota(self, estimated_seconds: float = 5.0) -> bool:
        """Check whether user has enough remaining quota to generate speech."""
        if self.is_owner_or_unlimited:
            return True
        return (self.audio_seconds_used + estimated_seconds) <= float(self.audio_seconds_quota)

    @property
    def remaining_seconds(self) -> float:
        """Remaining audio generation quota in seconds (-1.0 for unlimited)."""
        if self.is_owner_or_unlimited:
            return -1.0
        return max(0.0, float(self.audio_seconds_quota) - self.audio_seconds_used)


class UsageLedger(models.Model):
    """
    Immutable audit ledger recording every credit, debit, or bypass of user quota (VC-100).
    Guarantees financial integrity and verifiable usage accounting.
    """

    OPERATION_DEBIT = "SYNTHESIS_DEBIT"
    OPERATION_CREDIT = "PLAN_CREDIT"
    OPERATION_OVERRIDE = "ADMIN_OVERRIDE"
    OPERATION_UNLIMITED_BYPASS = "UNLIMITED_BYPASS"

    OPERATION_CHOICES = (
        (OPERATION_DEBIT, "Speech Synthesis Consumption"),
        (OPERATION_CREDIT, "Plan Subscription Credit"),
        (OPERATION_OVERRIDE, "Admin / Owner Manual Adjustment"),
        (OPERATION_UNLIMITED_BYPASS, "Unlimited VIP Zero-Cost Synthesis"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="usage_ledgers",
    )
    job_id = models.UUIDField(null=True, blank=True, db_index=True)
    delta_seconds = models.FloatField(
        help_text="Signed seconds change (+ for credit, - for debit)"
    )
    balance_after_seconds = models.FloatField(
        help_text="Remaining seconds balance after operation (-1 for unlimited)"
    )
    operation = models.CharField(max_length=32, choices=OPERATION_CHOICES, db_index=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "accounts_usage_ledger"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Ledger [{self.operation}] user={self.user.username} delta={self.delta_seconds}s"
