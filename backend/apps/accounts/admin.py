"""Django admin configuration for accounts app (VC-100, VC-104)."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import PaymentTransaction, Subscription, UsageLedger, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin supporting plan management, quota controls, and VIP unlimited toggle."""

    list_display = (
        "username",
        "email",
        "plan",
        "is_unlimited",
        "audio_seconds_quota",
        "audio_seconds_used",
        "is_staff",
        "is_superuser",
        "created_at",
    )
    list_filter = ("plan", "is_unlimited", "is_staff", "is_superuser", "is_verified")
    search_fields = ("username", "email")
    ordering = ("-created_at",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "VoiceClone SaaS & Quota (VC-100)",
            {
                "fields": (
                    "plan",
                    "is_unlimited",
                    "audio_seconds_quota",
                    "audio_seconds_used",
                    "is_verified",
                ),
                "description": "Control subscription plans and VIP unlimited bypass for this user.",
            },
        ),
    )


@admin.register(UsageLedger)
class UsageLedgerAdmin(admin.ModelAdmin):
    """Immutable usage ledger records for financial and quota audit."""

    list_display = (
        "id",
        "user",
        "operation",
        "delta_seconds",
        "balance_after_seconds",
        "job_id",
        "created_at",
    )
    list_filter = ("operation", "created_at")
    search_fields = ("user__username", "user__email", "job_id", "notes")
    readonly_fields = (
        "id",
        "user",
        "operation",
        "delta_seconds",
        "balance_after_seconds",
        "job_id",
        "notes",
        "created_at",
    )
    ordering = ("-created_at",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin inspection and management of subscription lifecycles."""

    list_display = (
        "id",
        "user",
        "plan",
        "status",
        "billing_cycle",
        "price_amount",
        "current_period_end",
        "cancel_at_period_end",
        "failed_payment_count",
    )
    list_filter = ("status", "plan", "billing_cycle", "cancel_at_period_end")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Audit and administrative ledger of payment transactions and refunds."""

    list_display = (
        "id",
        "user",
        "provider",
        "amount",
        "currency",
        "status",
        "provider_transaction_id",
        "created_at",
    )
    list_filter = ("status", "provider", "currency")
    search_fields = ("user__username", "user__email", "provider_transaction_id", "idempotency_key")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
