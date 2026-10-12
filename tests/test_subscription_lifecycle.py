"""
Unit and integration tests for Subscription Lifecycle, Failed Payments, and Refunds (VC-102).
Verifies state machine transitions, grace periods, cancellation, safe refunds,
and the core invariant: "Payment failures never corrupt user quotas or ledgers".
"""

import datetime
from decimal import Decimal

import pytest
from apps.accounts.models import PaymentTransaction, Subscription, UsageLedger, User
from apps.accounts.services import SubscriptionLifecycleService
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def standard_user(db):
    """Standard free user with initial 300s quota."""
    return User.objects.create_user(
        username="sub_user_test",
        email="sub_user@voiceclone.local",
        password="ValidPassword123!",
        plan=User.PLAN_FREE,
        audio_seconds_quota=300,
        audio_seconds_used=0.0,
    )


@pytest.fixture
def active_creator_user(db, standard_user):
    """User with active Creator subscription (1800s quota)."""
    sub, tx = SubscriptionLifecycleService.activate_subscription(
        user=standard_user,
        plan=User.PLAN_CREATOR,
        billing_cycle=Subscription.CYCLE_MONTHLY,
        provider=PaymentTransaction.PROVIDER_CLICK,
        provider_transaction_id="click_init_12345",
    )
    return standard_user, sub, tx


@pytest.fixture
def admin_user(db):
    """Staff/Superuser admin for processing refunds and viewing financials."""
    return User.objects.create_superuser(
        username="admin_billing_owner",
        email="billing_owner@voiceclone.local",
        password="OwnerSuperPassword123!",
    )


# =========================================================================
# 1. Subscription Activation & Quota Allocation Tests
# =========================================================================


@pytest.mark.django_db
def test_subscription_activation_creator_tier(standard_user):
    """Activating Creator tier sets status ACTIVE, grants 1800s, and logs ledger credit."""
    sub, tx = SubscriptionLifecycleService.activate_subscription(
        user=standard_user,
        plan=User.PLAN_CREATOR,
        billing_cycle=Subscription.CYCLE_MONTHLY,
        provider=PaymentTransaction.PROVIDER_CLICK,
        provider_transaction_id="clk_98765",
    )

    assert sub.status == Subscription.STATUS_ACTIVE
    assert sub.plan == User.PLAN_CREATOR
    assert sub.price_amount == Decimal("79000.00")
    assert sub.is_active_or_in_grace is True
    assert sub.failed_payment_count == 0

    assert tx.status == PaymentTransaction.STATUS_SUCCEEDED
    assert tx.amount == Decimal("79000.00")
    assert tx.provider == PaymentTransaction.PROVIDER_CLICK

    standard_user.refresh_from_db()
    assert standard_user.plan == User.PLAN_CREATOR
    assert standard_user.audio_seconds_quota == 1800
    assert standard_user.audio_seconds_used == 0.0
    assert standard_user.remaining_seconds == 1800.0

    ledger = UsageLedger.objects.filter(
        user=standard_user, operation=UsageLedger.OPERATION_CREDIT
    ).first()
    assert ledger is not None
    assert ledger.delta_seconds == 1500.0  # 1800 - 300
    assert ledger.balance_after_seconds == 1800.0


@pytest.mark.django_db
def test_subscription_activation_pro_tier_yearly(standard_user):
    """Activating Pro tier with yearly cycle applies discount and sets 7200s quota."""
    sub, tx = SubscriptionLifecycleService.activate_subscription(
        user=standard_user,
        plan=User.PLAN_PRO,
        billing_cycle=Subscription.CYCLE_YEARLY,
        provider=PaymentTransaction.PROVIDER_PAYME,
    )

    assert sub.plan == User.PLAN_PRO
    assert sub.billing_cycle == Subscription.CYCLE_YEARLY
    # Yearly price: 199,000 * 10 = 1,990,000 UZS
    assert sub.price_amount == Decimal("1990000.00")

    standard_user.refresh_from_db()
    assert standard_user.plan == User.PLAN_PRO
    assert standard_user.audio_seconds_quota == 7200


@pytest.mark.django_db
def test_subscription_activation_idempotency(standard_user):
    """Replaying subscription activation with the same idempotency key returns existing objects."""
    key = "idem_sub_unique_abc_999"
    sub1, tx1 = SubscriptionLifecycleService.activate_subscription(
        user=standard_user,
        plan=User.PLAN_CREATOR,
        idempotency_key=key,
    )
    sub2, tx2 = SubscriptionLifecycleService.activate_subscription(
        user=standard_user,
        plan=User.PLAN_CREATOR,
        idempotency_key=key,
    )

    assert sub1.id == sub2.id
    assert tx1.id == tx2.id
    assert PaymentTransaction.objects.filter(idempotency_key=key).count() == 1


# =========================================================================
# 2. Failed Payments & Quota Invariant ("To‘lov xatolari quota’ni buzmaydi")
# =========================================================================


@pytest.mark.django_db
def test_payment_failure_does_not_corrupt_quota(active_creator_user):
    """
    CRITICAL ACCEPTANCE CRITERION:
    When a recurring payment charge fails, user quota is NOT corrupted,
    seconds are NOT deducted, and subscription enters PAST_DUE with a 3-day grace period.
    """
    user, sub, _ = active_creator_user

    # Simulate user has consumed 120 seconds of audio legitimately
    user.audio_seconds_used = 120.0
    user.save()
    initial_remaining = user.remaining_seconds  # 1800 - 120 = 1680.0

    # Recurring payment attempt fails (e.g. Card expired or insufficient funds)
    failed_tx = SubscriptionLifecycleService.handle_payment_failure(
        subscription=sub,
        failure_reason="Insufficient balance on Uzcard/Humo card",
        failure_code="INSUFFICIENT_FUNDS",
        provider=PaymentTransaction.PROVIDER_CLICK,
    )

    assert failed_tx.status == PaymentTransaction.STATUS_FAILED
    assert failed_tx.failure_code == "INSUFFICIENT_FUNDS"

    sub.refresh_from_db()
    assert sub.status == Subscription.STATUS_PAST_DUE
    assert sub.failed_payment_count == 1
    assert sub.grace_period_until is not None
    # User is in active grace period
    assert sub.is_active_or_in_grace is True

    # VERIFY QUOTA INTEGRITY: Absolutely untouched!
    user.refresh_from_db()
    assert user.audio_seconds_quota == 1800
    assert user.audio_seconds_used == 120.0
    assert user.remaining_seconds == initial_remaining
    assert user.plan == User.PLAN_CREATOR


@pytest.mark.django_db
def test_grace_period_expiry_downgrades_safely(active_creator_user):
    """
    When grace period elapses without payment, subscription expires
    and user plan is safely downgraded to FREE tier without corrupting data.
    """
    user, sub, _ = active_creator_user

    # Put in PAST_DUE with grace period in the past
    sub.status = Subscription.STATUS_PAST_DUE
    sub.grace_period_until = timezone.now() - datetime.timedelta(hours=2)
    sub.save()

    assert sub.is_active_or_in_grace is False

    downgraded = SubscriptionLifecycleService.handle_grace_period_expiry(sub)
    assert downgraded is True

    sub.refresh_from_db()
    assert sub.status == Subscription.STATUS_EXPIRED

    user.refresh_from_db()
    assert user.plan == User.PLAN_FREE
    assert user.audio_seconds_quota == 300

    ledger = UsageLedger.objects.filter(user=user, operation=UsageLedger.OPERATION_OVERRIDE).first()
    assert ledger is not None
    assert "Grace period expired" in ledger.notes


# =========================================================================
# 3. Subscription Cancellation Tests
# =========================================================================


@pytest.mark.django_db
def test_cancellation_at_period_end_preserves_access(active_creator_user):
    """Canceling with immediate=False sets cancel_at_period_end=True, keeping access active."""
    user, sub, _ = active_creator_user

    sub = SubscriptionLifecycleService.cancel_subscription(
        subscription=sub,
        immediate=False,
        reason="Will not renew next month",
    )

    assert sub.cancel_at_period_end is True
    assert sub.status == Subscription.STATUS_ACTIVE
    assert sub.is_active_or_in_grace is True

    user.refresh_from_db()
    assert user.plan == User.PLAN_CREATOR


@pytest.mark.django_db
def test_immediate_cancellation_terminates_plan(active_creator_user):
    """Canceling with immediate=True immediately reverts user to FREE tier."""
    user, sub, _ = active_creator_user

    sub = SubscriptionLifecycleService.cancel_subscription(
        subscription=sub,
        immediate=True,
        reason="Immediate termination requested",
    )

    assert sub.status == Subscription.STATUS_CANCELED
    assert sub.cancel_at_period_end is True

    user.refresh_from_db()
    assert user.plan == User.PLAN_FREE
    assert user.audio_seconds_quota == 300


# =========================================================================
# 4. Refunds & Ledger Reversal Tests
# =========================================================================


@pytest.mark.django_db
def test_refund_succeeded_transaction_cancels_sub_and_rolls_back_quota(active_creator_user):
    """
    Processing full refund marks transaction REFUNDED, cancels subscription,
    and safely rolls back quota with a REFUND_ADJUSTMENT ledger entry.
    """
    user, sub, tx = active_creator_user

    refunded_tx = SubscriptionLifecycleService.process_refund(
        transaction_obj=tx,
        refund_amount=Decimal("79000.00"),
        reason="Customer requested chargeback within 24h",
    )

    assert refunded_tx.status == PaymentTransaction.STATUS_REFUNDED
    assert refunded_tx.refund_amount == Decimal("79000.00")

    sub.refresh_from_db()
    assert sub.status == Subscription.STATUS_CANCELED

    user.refresh_from_db()
    assert user.plan == User.PLAN_FREE
    assert user.audio_seconds_quota == 300

    ledger = UsageLedger.objects.filter(user=user, operation=UsageLedger.OPERATION_REFUND).first()
    assert ledger is not None
    assert "Refund processed" in ledger.notes
    assert ledger.balance_after_seconds >= 0.0


@pytest.mark.django_db
def test_cannot_refund_failed_transaction(active_creator_user):
    """Attempting to refund a failed transaction raises ValueError."""
    _, sub, _ = active_creator_user
    failed_tx = SubscriptionLifecycleService.handle_payment_failure(subscription=sub)

    with pytest.raises(ValueError, match="Only SUCCEEDED transactions are refundable"):
        SubscriptionLifecycleService.process_refund(failed_tx)


# =========================================================================
# 5. REST API Endpoints Tests
# =========================================================================


@pytest.mark.django_db
def test_api_subscription_detail_default_free(api_client, standard_user):
    """GET /api/v1/accounts/subscription/ returns FREE_TRIAL status for standard user."""
    api_client.force_authenticate(user=standard_user)
    resp = api_client.get("/api/v1/accounts/subscription/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["status"] == "FREE_TRIAL"
    assert data["plan"] == "FREE"


@pytest.mark.django_db
def test_api_subscription_create_upgrade(api_client, standard_user):
    """POST /api/v1/accounts/subscription/ subscribes user to CREATOR tier."""
    api_client.force_authenticate(user=standard_user)
    payload = {
        "plan": "CREATOR",
        "billing_cycle": "MONTHLY",
        "provider": "CLICK",
    }
    resp = api_client.post("/api/v1/accounts/subscription/", payload, format="json")
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["status"] == "success"
    assert data["subscription"]["plan"] == "CREATOR"
    assert data["subscription"]["status"] == "ACTIVE"


@pytest.mark.django_db
def test_api_subscription_cancel(api_client, active_creator_user):
    """POST /api/v1/accounts/subscription/cancel/ cancels active subscription."""
    user, _, _ = active_creator_user
    api_client.force_authenticate(user=user)

    resp = api_client.post(
        "/api/v1/accounts/subscription/cancel/",
        {"immediate": False, "reason": "Moving to another platform"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["subscription"]["cancel_at_period_end"] is True


@pytest.mark.django_db
def test_api_payment_transactions_list(api_client, active_creator_user):
    """GET /api/v1/accounts/subscription/transactions/ returns transaction history."""
    user, _, _ = active_creator_user
    api_client.force_authenticate(user=user)

    resp = api_client.get("/api/v1/accounts/subscription/transactions/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    results = data["results"] if isinstance(data, dict) and "results" in data else data
    assert len(results) >= 1
    assert results[0]["status"] == "SUCCEEDED"


@pytest.mark.django_db
def test_api_simulate_payment_failure_endpoint(api_client, active_creator_user):
    """POST /api/v1/accounts/subscription/simulate-failure/ confirms quota safety via API."""
    user, _, _ = active_creator_user
    api_client.force_authenticate(user=user)

    resp = api_client.post(
        "/api/v1/accounts/subscription/simulate-failure/",
        {"reason": "Card blocked", "code": "CARD_BLOCKED"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["status"] == "failure_simulated"
    assert data["subscription_status"] == "PAST_DUE"
    assert "Quota remains uncorrupted" in data["detail"]


@pytest.mark.django_db
def test_api_admin_refund_endpoint(api_client, admin_user, active_creator_user):
    """POST /api/v1/accounts/subscription/refund/ requires admin privileges."""
    user, _, tx = active_creator_user

    # 1. Non-admin forbidden
    api_client.force_authenticate(user=user)
    resp_forbid = api_client.post(
        "/api/v1/accounts/subscription/refund/",
        {"transaction_id": str(tx.id)},
        format="json",
    )
    assert resp_forbid.status_code == status.HTTP_403_FORBIDDEN

    # 2. Admin authorized
    api_client.force_authenticate(user=admin_user)
    resp_admin = api_client.post(
        "/api/v1/accounts/subscription/refund/",
        {"transaction_id": str(tx.id), "reason": "Admin refund pass"},
        format="json",
    )
    assert resp_admin.status_code == status.HTTP_200_OK
    assert resp_admin.json()["transaction"]["status"] == "REFUNDED"
