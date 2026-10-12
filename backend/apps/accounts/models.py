"""Custom User model and UsageLedger for VoiceClone identity, RBAC, and Quota Ledger (VC-100)."""

from __future__ import annotations

import uuid
from decimal import Decimal

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
    plan = models.CharField(max_length=32, choices=PLAN_CHOICES, default=PLAN_FREE, db_index=True)
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
    OPERATION_REFUND = "REFUND_ADJUSTMENT"

    OPERATION_CHOICES = (
        (OPERATION_DEBIT, "Speech Synthesis Consumption"),
        (OPERATION_CREDIT, "Plan Subscription Credit"),
        (OPERATION_OVERRIDE, "Admin / Owner Manual Adjustment"),
        (OPERATION_UNLIMITED_BYPASS, "Unlimited VIP Zero-Cost Synthesis"),
        (OPERATION_REFUND, "Payment Refund Adjustment"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="usage_ledgers",
    )
    job_id = models.UUIDField(null=True, blank=True, db_index=True)
    delta_seconds = models.FloatField(help_text="Signed seconds change (+ for credit, - for debit)")
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


class Subscription(models.Model):
    """
    Subscription entity governing billing tier, lifecycle states, grace periods,
    and automatic or manual renewals (VC-102).
    """

    STATUS_TRIALING = "TRIALING"
    STATUS_ACTIVE = "ACTIVE"
    STATUS_PAST_DUE = "PAST_DUE"
    STATUS_CANCELED = "CANCELED"
    STATUS_EXPIRED = "EXPIRED"

    STATUS_CHOICES = (
        (STATUS_TRIALING, "Trialing (Initial Evaluation)"),
        (STATUS_ACTIVE, "Active (Good Standing)"),
        (STATUS_PAST_DUE, "Past Due (Grace Period in effect)"),
        (STATUS_CANCELED, "Canceled (Pending Cycle End or Immediate)"),
        (STATUS_EXPIRED, "Expired (Access Reverted to Free)"),
    )

    CYCLE_MONTHLY = "MONTHLY"
    CYCLE_YEARLY = "YEARLY"
    CYCLE_CHOICES = (
        (CYCLE_MONTHLY, "Monthly Cycle"),
        (CYCLE_YEARLY, "Yearly Cycle (Discounted)"),
    )

    PLAN_SECONDS_MAP = {
        User.PLAN_FREE: 300,
        User.PLAN_CREATOR: 1800,  # 30 minutes
        User.PLAN_PRO: 7200,  # 120 minutes
        User.PLAN_UNLIMITED: -1,
    }

    PLAN_PRICES_UZS = {
        User.PLAN_FREE: 0.0,
        User.PLAN_CREATOR: 79000.0,
        User.PLAN_PRO: 199000.0,
        User.PLAN_UNLIMITED: 0.0,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.CharField(
        max_length=32,
        choices=User.PLAN_CHOICES,
        default=User.PLAN_CREATOR,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True,
    )
    billing_cycle = models.CharField(
        max_length=16,
        choices=CYCLE_CHOICES,
        default=CYCLE_MONTHLY,
    )
    price_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    currency = models.CharField(max_length=8, default="UZS")
    current_period_start = models.DateTimeField(db_index=True)
    current_period_end = models.DateTimeField(db_index=True)
    cancel_at_period_end = models.BooleanField(
        default=False,
        help_text="If true, will not renew and expires at current_period_end",
    )
    grace_period_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Window during which service continues despite failed renewal charge",
    )
    failed_payment_count = models.PositiveIntegerField(
        default=0,
        help_text="Consecutive failed renewal attempts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_subscription"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Subscription [{self.status}] user={self.user.username} plan={self.plan}"

    @property
    def is_active_or_in_grace(self) -> bool:
        """Check if subscription entitles user to plan benefits right now."""
        from django.utils import timezone

        now = timezone.now()
        if self.status in (self.STATUS_ACTIVE, self.STATUS_TRIALING):
            return True
        if self.status == self.STATUS_PAST_DUE and self.grace_period_until:
            return now <= self.grace_period_until
        return False


class PaymentTransaction(models.Model):
    """
    Immutable payment and refund audit ledger representing individual charges,
    settlements, failed collection attempts, and refund operations (VC-102).
    """

    PROVIDER_CLICK = "CLICK"
    PROVIDER_PAYME = "PAYME"
    PROVIDER_UZUM = "UZUM"
    PROVIDER_STRIPE = "STRIPE"
    PROVIDER_MOCK = "MOCK"
    PROVIDER_MANUAL = "MANUAL"

    PROVIDER_CHOICES = (
        (PROVIDER_CLICK, "Click Payment System"),
        (PROVIDER_PAYME, "Payme Merchant"),
        (PROVIDER_UZUM, "Uzum Bank / Pay"),
        (PROVIDER_STRIPE, "Stripe International"),
        (PROVIDER_MOCK, "Mock / Sandbox Provider"),
        (PROVIDER_MANUAL, "Manual Admin Reconciliation"),
    )

    STATUS_PENDING = "PENDING"
    STATUS_SUCCEEDED = "SUCCEEDED"
    STATUS_FAILED = "FAILED"
    STATUS_REFUNDED = "REFUNDED"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending Processing"),
        (STATUS_SUCCEEDED, "Settled / Succeeded"),
        (STATUS_FAILED, "Failed / Declined"),
        (STATUS_REFUNDED, "Refunded / Reversed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    subscription = models.ForeignKey(
        "accounts.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    provider = models.CharField(
        max_length=32,
        choices=PROVIDER_CHOICES,
        default=PROVIDER_MOCK,
        db_index=True,
    )
    provider_transaction_id = models.CharField(max_length=128, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="UZS")
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    failure_code = models.CharField(max_length=64, blank=True)
    failure_reason = models.TextField(blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    refund_reason = models.TextField(blank=True)
    idempotency_key = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_payment_transaction"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"Payment [{self.status}] {self.amount} {self.currency} "
            f"user={self.user.username} ref={self.provider_transaction_id}"
        )
