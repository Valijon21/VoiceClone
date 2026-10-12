"""
Subscription and Payment Lifecycle Service (VC-102).
Guarantees financial state machine transitions, grace periods, safe refunds,
and the critical invariant: "Payment failures never corrupt user quotas or ledgers".
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import PaymentTransaction, Subscription, UsageLedger, User


class SubscriptionLifecycleService:
    """Service encapsulating all subscription state transitions, payments, and refunds."""

    GRACE_PERIOD_DAYS = 3
    DEFAULT_CYCLE_DAYS = 30
    YEARLY_CYCLE_DAYS = 365

    @classmethod
    @transaction.atomic
    def activate_subscription(
        cls,
        user: User,
        plan: str,
        billing_cycle: str = Subscription.CYCLE_MONTHLY,
        provider: str = PaymentTransaction.PROVIDER_MOCK,
        provider_transaction_id: str | None = None,
        idempotency_key: str | None = None,
        amount: Decimal | None = None,
    ) -> tuple[Subscription, PaymentTransaction]:
        """
        Activates or renews a subscription, grants plan quota, and logs immutable ledger credit.
        """
        if plan not in dict(User.PLAN_CHOICES):
            raise ValueError(f"Invalid plan '{plan}' specified.")

        now = timezone.now()
        duration_days = (
            cls.YEARLY_CYCLE_DAYS
            if billing_cycle == Subscription.CYCLE_YEARLY
            else cls.DEFAULT_CYCLE_DAYS
        )
        period_end = now + datetime.timedelta(days=duration_days)

        default_price = Decimal(str(Subscription.PLAN_PRICES_UZS.get(plan, 0.0)))
        if billing_cycle == Subscription.CYCLE_YEARLY:
            default_price = default_price * Decimal("10.0")  # 2 months discount for yearly

        charged_amount = amount if amount is not None else default_price
        tx_id = provider_transaction_id or f"tx_{uuid.uuid4().hex[:16]}"

        # Check idempotency on payment transaction if provided
        if idempotency_key:
            existing_tx = PaymentTransaction.objects.filter(idempotency_key=idempotency_key).first()
            if existing_tx and existing_tx.subscription:
                return existing_tx.subscription, existing_tx

        # Find existing active or past-due subscription for this user, or create new
        sub = (
            Subscription.objects.filter(user=user)
            .exclude(status__in=[Subscription.STATUS_EXPIRED, Subscription.STATUS_CANCELED])
            .first()
        )
        if sub is None:
            sub = Subscription(user=user)

        sub.plan = plan
        sub.status = Subscription.STATUS_ACTIVE
        sub.billing_cycle = billing_cycle
        sub.price_amount = charged_amount
        sub.currency = "UZS"
        sub.current_period_start = now
        sub.current_period_end = period_end
        sub.cancel_at_period_end = False
        sub.grace_period_until = None
        sub.failed_payment_count = 0
        sub.save()

        # Update existing pending transaction or create settled PaymentTransaction
        payment_tx = PaymentTransaction.objects.filter(
            provider=provider,
            provider_transaction_id=tx_id,
        ).first()

        if payment_tx:
            payment_tx.subscription = sub
            payment_tx.status = PaymentTransaction.STATUS_SUCCEEDED
            payment_tx.amount = charged_amount
            if idempotency_key:
                payment_tx.idempotency_key = idempotency_key
            payment_tx.save()
        else:
            payment_tx = PaymentTransaction.objects.create(
                user=user,
                subscription=sub,
                provider=provider,
                provider_transaction_id=tx_id,
                amount=charged_amount,
                currency="UZS",
                status=PaymentTransaction.STATUS_SUCCEEDED,
                idempotency_key=idempotency_key,
            )

        # Apply plan quota & reset usage for the fresh billing cycle
        plan_seconds = Subscription.PLAN_SECONDS_MAP.get(plan, 300)
        old_quota = user.audio_seconds_quota
        user.plan = plan

        if plan == User.PLAN_UNLIMITED:
            user.is_unlimited = True
            delta_seconds = 0.0
        else:
            user.audio_seconds_quota = plan_seconds
            user.audio_seconds_used = 0.0  # Reset counter for new billing cycle
            delta_seconds = float(plan_seconds) - float(old_quota)

        user.save()

        # Immutable ledger record
        UsageLedger.objects.create(
            user=user,
            operation=UsageLedger.OPERATION_CREDIT,
            delta_seconds=delta_seconds,
            balance_after_seconds=user.remaining_seconds,
            notes=f"Subscription activated: {plan} ({billing_cycle}) via {provider} tx={tx_id}",
        )

        return sub, payment_tx

    @classmethod
    @transaction.atomic
    def handle_payment_failure(
        cls,
        subscription: Subscription,
        failure_reason: str = "Payment charge declined by card issuer",
        failure_code: str = "INSUFFICIENT_FUNDS",
        provider: str = PaymentTransaction.PROVIDER_MOCK,
        provider_transaction_id: str | None = None,
        amount: Decimal | None = None,
    ) -> PaymentTransaction:
        """
        Handles failed recurring payment or renewal attempt.
        CRITICAL INVARIANT (VC-102):
        Payment failures MUST NOT corrupt user quota, nor subtract remaining seconds.
        Puts active subscription into PAST_DUE with a 3-day grace period.
        """
        now = timezone.now()
        tx_id = provider_transaction_id or f"fail_{uuid.uuid4().hex[:16]}"
        charged_amount = amount if amount is not None else subscription.price_amount

        # Record failed transaction in audit log
        payment_tx = PaymentTransaction.objects.create(
            user=subscription.user,
            subscription=subscription,
            provider=provider,
            provider_transaction_id=tx_id,
            amount=charged_amount,
            currency=subscription.currency,
            status=PaymentTransaction.STATUS_FAILED,
            failure_code=failure_code,
            failure_reason=failure_reason,
        )

        subscription.failed_payment_count += 1

        # If currently active or trialing, enter PAST_DUE with grace period
        if subscription.status in (Subscription.STATUS_ACTIVE, Subscription.STATUS_TRIALING):
            subscription.status = Subscription.STATUS_PAST_DUE
            subscription.grace_period_until = now + datetime.timedelta(days=cls.GRACE_PERIOD_DAYS)

        subscription.save()

        # Notice: User quota and audio_seconds_used remain 100% UNTOUCHED!
        return payment_tx

    @classmethod
    @transaction.atomic
    def handle_grace_period_expiry(cls, subscription: Subscription) -> bool:
        """
        Checks if a PAST_DUE subscription's grace period has expired.
        If expired, downgrades subscription to EXPIRED and user to FREE tier safely.
        Returns True if expired and downgraded, False otherwise.
        """
        now = timezone.now()
        if subscription.status != Subscription.STATUS_PAST_DUE:
            return False

        if not subscription.grace_period_until or now <= subscription.grace_period_until:
            return False  # Still within grace period

        subscription.status = Subscription.STATUS_EXPIRED
        subscription.save()

        user = subscription.user
        old_plan = user.plan
        user.plan = User.PLAN_FREE
        user.audio_seconds_quota = Subscription.PLAN_SECONDS_MAP[User.PLAN_FREE]
        # Keep accumulated usage or cap it safely
        user.save()

        UsageLedger.objects.create(
            user=user,
            operation=UsageLedger.OPERATION_OVERRIDE,
            delta_seconds=0.0,
            balance_after_seconds=user.remaining_seconds,
            notes=f"Grace period expired. Plan downgraded from {old_plan} to FREE (VC-102).",
        )
        return True

    @classmethod
    @transaction.atomic
    def cancel_subscription(
        cls,
        subscription: Subscription,
        immediate: bool = False,
        reason: str = "User requested cancellation",
    ) -> Subscription:
        """
        Cancels a subscription.
        - immediate=False: sets cancel_at_period_end=True. User keeps benefits until current_period_end.
        - immediate=True: immediate termination, downgrades user to FREE.
        """
        subscription.cancel_at_period_end = True

        if immediate:
            subscription.status = Subscription.STATUS_CANCELED
            subscription.save()

            user = subscription.user
            old_plan = user.plan
            user.plan = User.PLAN_FREE
            user.audio_seconds_quota = Subscription.PLAN_SECONDS_MAP[User.PLAN_FREE]
            user.save()

            UsageLedger.objects.create(
                user=user,
                operation=UsageLedger.OPERATION_OVERRIDE,
                delta_seconds=0.0,
                balance_after_seconds=user.remaining_seconds,
                notes=f"Subscription cancelled immediately ({old_plan} -> FREE): {reason}",
            )
        else:
            subscription.save()

        return subscription

    @classmethod
    @transaction.atomic
    def process_refund(
        cls,
        transaction_obj: PaymentTransaction,
        refund_amount: Decimal | None = None,
        reason: str = "Customer requested refund",
    ) -> PaymentTransaction:
        """
        Processes full or partial refund for a settled transaction.
        Guarantees quota rollback is safe and never creates negative balances or corrupts records.
        """
        if transaction_obj.status != PaymentTransaction.STATUS_SUCCEEDED:
            raise ValueError(
                f"Cannot refund transaction with status '{transaction_obj.status}'. "
                "Only SUCCEEDED transactions are refundable."
            )

        max_refundable = Decimal(str(transaction_obj.amount)) - Decimal(
            str(transaction_obj.refund_amount)
        )
        actual_refund = Decimal(str(refund_amount)) if refund_amount is not None else max_refundable

        if actual_refund <= Decimal("0.00"):
            raise ValueError("Refund amount must be greater than zero.")
        if actual_refund > max_refundable:
            raise ValueError(
                f"Requested refund ({actual_refund}) exceeds refundable amount ({max_refundable})."
            )

        transaction_obj.refund_amount = Decimal(str(transaction_obj.refund_amount)) + actual_refund
        transaction_obj.refund_reason = reason
        if transaction_obj.refund_amount >= Decimal(str(transaction_obj.amount)):
            transaction_obj.status = PaymentTransaction.STATUS_REFUNDED
        transaction_obj.save()

        # If full refund on a subscription transaction, cancel subscription and reset plan safely
        sub = transaction_obj.subscription
        if sub and transaction_obj.status == PaymentTransaction.STATUS_REFUNDED:
            sub.status = Subscription.STATUS_CANCELED
            sub.cancel_at_period_end = True
            sub.save()

            user = transaction_obj.user
            old_quota = user.audio_seconds_quota
            user.plan = User.PLAN_FREE
            user.audio_seconds_quota = Subscription.PLAN_SECONDS_MAP[User.PLAN_FREE]
            # Ensure used does not exceed new quota
            if user.audio_seconds_used > float(user.audio_seconds_quota):
                user.audio_seconds_used = float(user.audio_seconds_quota)
            user.save()

            delta = float(user.audio_seconds_quota) - float(old_quota)
            UsageLedger.objects.create(
                user=user,
                operation=UsageLedger.OPERATION_REFUND,
                delta_seconds=delta,
                balance_after_seconds=user.remaining_seconds,
                notes=f"Refund processed for tx={transaction_obj.provider_transaction_id}: {actual_refund} UZS ({reason})",
            )

        return transaction_obj
