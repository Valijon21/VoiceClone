"""
Unit and integration tests for Payment Provider Integrations: Payme & Click (VC-101).
Tests JSON-RPC 2.0 protocol, MD5 digest verification, subscription activation on settlement,
and payment failure handling.
"""

import base64
import hashlib
from decimal import Decimal

import pytest
from apps.accounts.gateways import ClickGateway, PaymeGateway
from apps.accounts.models import PaymentTransaction, Subscription, User
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    """Standard user for checkout and payment testing."""
    return User.objects.create_user(
        username="checkout_payer",
        email="payer@voiceclone.local",
        password="ValidPassword123!",
        plan=User.PLAN_FREE,
        audio_seconds_quota=300,
        audio_seconds_used=0.0,
    )


@pytest.fixture
def payme_gateway():
    return PaymeGateway(merchant_id="test_merchant_id", secret_key="test_secret_key_123")


@pytest.fixture
def click_gateway():
    return ClickGateway(
        service_id="12345",
        merchant_id="67890",
        secret_key="click_test_secret_key",
    )


def make_payme_auth_header(secret_key: str = "test_secret_key_123") -> dict[str, str]:
    raw = f"Paycom:{secret_key}"
    encoded = base64.b64encode(raw.encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {encoded}"}


# =========================================================================
# 1. Payme JSON-RPC 2.0 Gateway Tests
# =========================================================================


@pytest.mark.django_db
def test_payme_auth_failure_returns_error(payme_gateway):
    """Missing or invalid Authorization header returns error -32504."""
    payload = {
        "method": "CheckPerformTransaction",
        "params": {"amount": 7900000},
        "id": 101,
    }
    # No auth
    resp = payme_gateway.process_webhook(payload, {})
    assert "error" in resp
    assert resp["error"]["code"] == PaymeGateway.ERROR_INSUFFICIENT_PRIVILEGE

    # Bad auth
    resp_bad = payme_gateway.process_webhook(payload, {"Authorization": "Basic bad_encoded_creds"})
    assert resp_bad["error"]["code"] == PaymeGateway.ERROR_INSUFFICIENT_PRIVILEGE


@pytest.mark.django_db
def test_payme_check_perform_transaction_valid(payme_gateway, test_user):
    """CheckPerformTransaction validates user and amount (79,000 UZS = 7,900,000 tiyin)."""
    headers = make_payme_auth_header()
    payload = {
        "method": "CheckPerformTransaction",
        "params": {
            "amount": 7900000,
            "account": {"user_id": str(test_user.id), "plan": "CREATOR"},
        },
        "id": 102,
    }
    resp = payme_gateway.process_webhook(payload, headers)
    assert "result" in resp
    assert resp["result"]["allow"] is True


@pytest.mark.django_db
def test_payme_check_perform_transaction_invalid_user_or_amount(payme_gateway, test_user):
    """CheckPerformTransaction rejects unknown user or wrong amount."""
    headers = make_payme_auth_header()

    # Unknown user
    resp_no_user = payme_gateway.process_webhook(
        {
            "method": "CheckPerformTransaction",
            "params": {
                "amount": 7900000,
                "account": {"user_id": "00000000-0000-0000-0000-000000000000"},
            },
            "id": 103,
        },
        headers,
    )
    assert resp_no_user["error"]["code"] == PaymeGateway.ERROR_ACCOUNT_NOT_FOUND

    # Invalid amount (e.g. 1000 tiyin instead of 7,900,000)
    resp_bad_amount = payme_gateway.process_webhook(
        {
            "method": "CheckPerformTransaction",
            "params": {
                "amount": 1000,
                "account": {"user_id": str(test_user.id), "plan": "CREATOR"},
            },
            "id": 104,
        },
        headers,
    )
    assert resp_bad_amount["error"]["code"] == PaymeGateway.ERROR_INVALID_AMOUNT


@pytest.mark.django_db
def test_payme_create_and_perform_transaction_activates_sub(payme_gateway, test_user):
    """
    Full Payme lifecycle:
    1. CreateTransaction creates state=1 pending record.
    2. PerformTransaction settles payment, transitions to state=2, and activates 1800s Creator quota.
    """
    headers = make_payme_auth_header()
    payme_tx_id = "payme_trans_auto_999"

    # Step 1: CreateTransaction
    create_payload = {
        "method": "CreateTransaction",
        "params": {
            "id": payme_tx_id,
            "time": 1720000000000,
            "amount": 7900000,
            "account": {"user_id": str(test_user.id), "plan": "CREATOR"},
        },
        "id": 201,
    }
    resp_create = payme_gateway.process_webhook(create_payload, headers)
    assert "result" in resp_create
    assert resp_create["result"]["state"] == PaymeGateway.STATE_CREATED

    tx = PaymentTransaction.objects.get(provider_transaction_id=payme_tx_id)
    assert tx.status == PaymentTransaction.STATUS_PENDING
    assert tx.amount == Decimal("79000.00")

    # Step 2: PerformTransaction
    perform_payload = {
        "method": "PerformTransaction",
        "params": {"id": payme_tx_id},
        "id": 202,
    }
    resp_perform = payme_gateway.process_webhook(perform_payload, headers)
    assert "result" in resp_perform
    assert resp_perform["result"]["state"] == PaymeGateway.STATE_COMPLETED

    # Verify User & Subscription state
    test_user.refresh_from_db()
    assert test_user.plan == User.PLAN_CREATOR
    assert test_user.audio_seconds_quota == 1800

    sub = Subscription.objects.get(user=test_user)
    assert sub.status == Subscription.STATUS_ACTIVE
    assert sub.plan == User.PLAN_CREATOR


@pytest.mark.django_db
def test_payme_cancel_transaction_before_and_after_perform(payme_gateway, test_user):
    """
    CancelTransaction cancels pending transaction (state -1)
    or safely refunds already completed transaction (state -2).
    """
    headers = make_payme_auth_header()

    # 1. Cancel on pending
    tx_pending_id = "payme_cancel_pending_11"
    payme_gateway.process_webhook(
        {
            "method": "CreateTransaction",
            "params": {
                "id": tx_pending_id,
                "time": 1720000000000,
                "amount": 7900000,
                "account": {"user_id": str(test_user.id), "plan": "CREATOR"},
            },
            "id": 301,
        },
        headers,
    )
    resp_cancel_pend = payme_gateway.process_webhook(
        {"method": "CancelTransaction", "params": {"id": tx_pending_id, "reason": 1}, "id": 302},
        headers,
    )
    assert resp_cancel_pend["result"]["state"] == PaymeGateway.STATE_CANCELLED

    # 2. Cancel on completed (Refund)
    tx_done_id = "payme_cancel_done_22"
    payme_gateway.process_webhook(
        {
            "method": "CreateTransaction",
            "params": {
                "id": tx_done_id,
                "time": 1720000000000,
                "amount": 7900000,
                "account": {"user_id": str(test_user.id), "plan": "CREATOR"},
            },
            "id": 303,
        },
        headers,
    )
    payme_gateway.process_webhook(
        {"method": "PerformTransaction", "params": {"id": tx_done_id}, "id": 304},
        headers,
    )
    resp_cancel_done = payme_gateway.process_webhook(
        {"method": "CancelTransaction", "params": {"id": tx_done_id, "reason": 2}, "id": 305},
        headers,
    )
    assert resp_cancel_done["result"]["state"] == PaymeGateway.STATE_CANCELLED_AFTER_COMPLETE

    tx_done = PaymentTransaction.objects.get(provider_transaction_id=tx_done_id)
    assert tx_done.status == PaymentTransaction.STATUS_REFUNDED


# =========================================================================
# 2. Click Merchant Shop API Gateway Tests
# =========================================================================


@pytest.mark.django_db
def test_click_prepare_and_complete_lifecycle(click_gateway, test_user):
    """
    Click Prepare (action=0) validates signature and order.
    Click Complete (action=1) validates complete signature and settles plan quota.
    """
    click_trans_id = "click_tx_555"
    service_id = "12345"
    merchant_trans_id = f"{test_user.id}:CREATOR:MONTHLY"
    amount = "79000.00"
    sign_time = "2026-10-12 12:00:00"

    # 1. Prepare (action=0)
    prep_raw = f"{click_trans_id}{service_id}{click_gateway.secret_key}{merchant_trans_id}{amount}0{sign_time}"
    prep_sign = hashlib.md5(prep_raw.encode("utf-8")).hexdigest()

    prep_data = {
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "merchant_trans_id": merchant_trans_id,
        "amount": amount,
        "action": "0",
        "error": "0",
        "sign_time": sign_time,
        "sign_string": prep_sign,
    }
    prep_resp = click_gateway.process_webhook(prep_data, {})
    assert prep_resp["error"] == 0
    merchant_prepare_id = prep_resp["merchant_prepare_id"]
    assert merchant_prepare_id is not None

    # 2. Complete (action=1)
    comp_raw = f"{click_trans_id}{service_id}{click_gateway.secret_key}{merchant_trans_id}{merchant_prepare_id}{amount}1{sign_time}"
    comp_sign = hashlib.md5(comp_raw.encode("utf-8")).hexdigest()

    comp_data = {
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": merchant_prepare_id,
        "amount": amount,
        "action": "1",
        "error": "0",
        "sign_time": sign_time,
        "sign_string": comp_sign,
    }
    comp_resp = click_gateway.process_webhook(comp_data, {})
    assert comp_resp["error"] == 0

    # Verify User & Subscription upgraded
    test_user.refresh_from_db()
    assert test_user.plan == User.PLAN_CREATOR
    assert test_user.audio_seconds_quota == 1800


@pytest.mark.django_db
def test_click_prepare_invalid_signature_rejected(click_gateway, test_user):
    """Click Prepare with forged or incorrect MD5 signature returns error -1."""
    prep_data = {
        "click_trans_id": "click_bad_sign_1",
        "service_id": "12345",
        "merchant_trans_id": f"{test_user.id}:CREATOR:MONTHLY",
        "amount": "79000.00",
        "action": "0",
        "sign_time": "2026-10-12 12:00:00",
        "sign_string": "invalid_forged_md5_signature",
    }
    resp = click_gateway.process_webhook(prep_data, {})
    assert resp["error"] == ClickGateway.ERROR_SIGN_CHECK_FAILED


# =========================================================================
# 3. Checkout & Webhook API Endpoints Tests
# =========================================================================


@pytest.mark.django_db
def test_checkout_initiate_endpoint_payme_and_click(api_client, test_user):
    """POST /api/v1/accounts/payments/checkout/ returns valid provider checkout link."""
    api_client.force_authenticate(user=test_user)

    # 1. Payme checkout
    resp_payme = api_client.post(
        "/api/v1/accounts/payments/checkout/",
        {"plan": "CREATOR", "billing_cycle": "MONTHLY", "provider": "PAYME"},
        format="json",
    )
    assert resp_payme.status_code == status.HTTP_200_OK
    data_payme = resp_payme.json()
    assert data_payme["provider"] == "PAYME"
    assert "https://checkout.paycom.uz/" in data_payme["payment_url"]

    # 2. Click checkout
    resp_click = api_client.post(
        "/api/v1/accounts/payments/checkout/",
        {"plan": "PRO", "billing_cycle": "MONTHLY", "provider": "CLICK"},
        format="json",
    )
    assert resp_click.status_code == status.HTTP_200_OK
    data_click = resp_click.json()
    assert data_click["provider"] == "CLICK"
    assert "https://my.click.uz/services/pay" in data_click["payment_url"]


@pytest.mark.django_db
def test_webhook_endpoints_routing(api_client, test_user):
    """
    Verify public access and response format of:
    - POST /api/v1/accounts/payments/payme/webhook/
    - POST /api/v1/accounts/payments/click/webhook/
    """
    # Payme webhook (anonymous call)
    resp_payme = api_client.post(
        "/api/v1/accounts/payments/payme/webhook/",
        {"method": "CheckPerformTransaction", "params": {}, "id": 1},
        format="json",
    )
    assert resp_payme.status_code == status.HTTP_200_OK
    assert "error" in resp_payme.json()  # Auth failed as expected

    # Click webhook (anonymous call)
    resp_click = api_client.post(
        "/api/v1/accounts/payments/click/webhook/",
        {"action": "99"},
        format="json",
    )
    assert resp_click.status_code == status.HTTP_200_OK
    assert resp_click.json()["error"] == ClickGateway.ERROR_ACTION_NOT_FOUND
