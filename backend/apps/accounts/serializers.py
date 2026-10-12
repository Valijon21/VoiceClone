from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Public serialized user profile including quota and subscription details (VC-100)."""

    remaining_seconds = serializers.FloatField(read_only=True)
    is_owner_or_unlimited = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_verified",
            "plan",
            "is_unlimited",
            "audio_seconds_quota",
            "audio_seconds_used",
            "remaining_seconds",
            "is_owner_or_unlimited",
            "is_staff",
            "is_superuser",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "plan",
            "is_unlimited",
            "audio_seconds_quota",
            "audio_seconds_used",
            "remaining_seconds",
            "is_owner_or_unlimited",
            "is_staff",
            "is_superuser",
            "created_at",
        ]


class UsageLedgerSerializer(serializers.ModelSerializer):
    """Immutable audit trail serializer for quota operations."""

    class Meta:
        from .models import UsageLedger

        model = UsageLedger
        fields = [
            "id",
            "operation",
            "delta_seconds",
            "balance_after_seconds",
            "job_id",
            "notes",
            "created_at",
        ]
        read_only_fields = fields


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for payment transactions and refunds (VC-102)."""

    class Meta:
        from .models import PaymentTransaction

        model = PaymentTransaction
        fields = [
            "id",
            "provider",
            "provider_transaction_id",
            "amount",
            "currency",
            "status",
            "failure_code",
            "failure_reason",
            "refund_amount",
            "refund_reason",
            "idempotency_key",
            "created_at",
        ]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    """Detailed serializer for user subscription status and lifecycle (VC-102)."""

    is_active_or_in_grace = serializers.BooleanField(read_only=True)
    transactions = PaymentTransactionSerializer(many=True, read_only=True)

    class Meta:
        from .models import Subscription

        model = Subscription
        fields = [
            "id",
            "plan",
            "status",
            "billing_cycle",
            "price_amount",
            "currency",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "grace_period_until",
            "failed_payment_count",
            "is_active_or_in_grace",
            "transactions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SubscriptionCreateSerializer(serializers.Serializer):
    """Serializer for subscribing to a plan or upgrading (VC-102)."""

    plan = serializers.ChoiceField(choices=[User.PLAN_CREATOR, User.PLAN_PRO, User.PLAN_UNLIMITED])
    billing_cycle = serializers.ChoiceField(choices=["MONTHLY", "YEARLY"], default="MONTHLY")
    provider = serializers.ChoiceField(
        choices=["MOCK", "CLICK", "PAYME", "UZUM", "STRIPE", "MANUAL"], default="MOCK"
    )
    provider_transaction_id = serializers.CharField(
        max_length=128, required=False, allow_blank=True
    )
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


class CheckoutInitiateSerializer(serializers.Serializer):
    """Serializer for generating checkout payment redirect link (VC-101)."""

    plan = serializers.ChoiceField(choices=[User.PLAN_CREATOR, User.PLAN_PRO])
    billing_cycle = serializers.ChoiceField(choices=["MONTHLY", "YEARLY"], default="MONTHLY")
    provider = serializers.ChoiceField(choices=["PAYME", "CLICK"], default="PAYME")
    return_url = serializers.URLField(required=False, allow_blank=True)


class SubscriptionCancelSerializer(serializers.Serializer):
    """Serializer for canceling a subscription (VC-102)."""

    immediate = serializers.BooleanField(default=False)
    reason = serializers.CharField(max_length=255, default="User requested cancellation")


class RefundRequestSerializer(serializers.Serializer):
    """Admin serializer for processing transaction refunds (VC-102)."""

    transaction_id = serializers.UUIDField()
    refund_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    reason = serializers.CharField(max_length=255, default="Customer requested refund")


class AdminPlanUpdateSerializer(serializers.Serializer):
    """Owner/Admin serializer to grant unlimited access, upgrade plans, or adjust quota."""

    plan = serializers.ChoiceField(choices=User.PLAN_CHOICES, required=False)
    is_unlimited = serializers.BooleanField(required=False)
    audio_seconds_quota = serializers.IntegerField(min_value=0, required=False)
    bonus_seconds = serializers.IntegerField(min_value=0, required=False)
    note = serializers.CharField(max_length=255, default="Admin quota adjustment")


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user
