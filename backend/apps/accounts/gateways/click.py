"""
Click Merchant Payment Gateway (VC-101).
Implements the official Click Shop API (Prepare and Complete protocol) with MD5 digest verification.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any

from django.conf import settings

from apps.accounts.models import PaymentTransaction, Subscription, User
from apps.accounts.services import SubscriptionLifecycleService

from .base import BasePaymentGateway


class ClickGateway(BasePaymentGateway):
    """
    Click Merchant Shop API implementation.
    Handles Prepare (action=0) and Complete (action=1) workflows with MD5 signature validation.
    """

    ERROR_SUCCESS = 0
    ERROR_SIGN_CHECK_FAILED = -1
    ERROR_INVALID_AMOUNT = -2
    ERROR_ACTION_NOT_FOUND = -3
    ERROR_ALREADY_PAID = -4
    ERROR_USER_NOT_FOUND = -5
    ERROR_TRANSACTION_NOT_FOUND = -6
    ERROR_FAILED_UPDATE = -7
    ERROR_REQUEST_ERROR = -8
    ERROR_TRANSACTION_CANCELLED = -9

    def __init__(
        self,
        service_id: str | None = None,
        merchant_id: str | None = None,
        secret_key: str | None = None,
    ):
        self.service_id = service_id or getattr(
            settings, "CLICK_SERVICE_ID", "mock_click_service_id"
        )
        self.merchant_id = merchant_id or getattr(
            settings, "CLICK_MERCHANT_ID", "mock_click_merchant_id"
        )
        self.secret_key = secret_key or getattr(
            settings, "CLICK_SECRET_KEY", "mock_click_secret_key_test"
        )

    def generate_payment_link(
        self,
        user: User,
        plan: str,
        amount: Decimal,
        billing_cycle: str = Subscription.CYCLE_MONTHLY,
        return_url: str | None = None,
    ) -> str:
        """
        Generates checkout redirect URL for Click payment portal.
        """
        merchant_trans_id = f"{user.id}:{plan}:{billing_cycle}"
        url = (
            f"https://my.click.uz/services/pay?"
            f"service_id={self.service_id}&"
            f"merchant_id={self.merchant_id}&"
            f"amount={amount}&"
            f"transaction_param={merchant_trans_id}"
        )
        if return_url:
            url += f"&return_url={return_url}"
        return url

    def verify_request_auth(self, headers: dict[str, Any], raw_body: bytes) -> bool:
        """Click authentication is verified per request via MD5 payload digest."""
        return True

    def verify_prepare_signature(
        self,
        click_trans_id: str,
        service_id: str,
        merchant_trans_id: str,
        amount: str,
        action: str,
        sign_time: str,
        received_sign: str,
    ) -> bool:
        """
        Validates prepare signature:
        md5(click_trans_id + service_id + secret_key + merchant_trans_id + amount + action + sign_time)
        """
        payload = f"{click_trans_id}{service_id}{self.secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
        computed = hashlib.md5(payload.encode("utf-8")).hexdigest()
        return computed.lower() == received_sign.lower()

    def verify_complete_signature(
        self,
        click_trans_id: str,
        service_id: str,
        merchant_trans_id: str,
        merchant_prepare_id: str,
        amount: str,
        action: str,
        sign_time: str,
        received_sign: str,
    ) -> bool:
        """
        Validates complete signature:
        md5(click_trans_id + service_id + secret_key + merchant_trans_id + merchant_prepare_id + amount + action + sign_time)
        """
        payload = f"{click_trans_id}{service_id}{self.secret_key}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
        computed = hashlib.md5(payload.encode("utf-8")).hexdigest()
        return computed.lower() == received_sign.lower()

    def process_webhook(self, data: dict[str, Any], headers: dict[str, Any]) -> dict[str, Any]:
        """
        Processes Click incoming POST request for action=0 (Prepare) and action=1 (Complete).
        """
        action = str(data.get("action", ""))
        click_trans_id = str(data.get("click_trans_id", ""))
        merchant_trans_id = str(data.get("merchant_trans_id", ""))
        service_id = str(data.get("service_id", ""))
        amount_str = str(data.get("amount", "0"))
        sign_time = str(data.get("sign_time", ""))
        sign_string = str(data.get("sign_string", ""))
        error_code = int(data.get("error", 0))

        if action == "0":
            return self._handle_prepare(
                click_trans_id=click_trans_id,
                service_id=service_id,
                merchant_trans_id=merchant_trans_id,
                amount_str=amount_str,
                sign_time=sign_time,
                sign_string=sign_string,
            )
        elif action == "1":
            merchant_prepare_id = str(data.get("merchant_prepare_id", ""))
            return self._handle_complete(
                click_trans_id=click_trans_id,
                service_id=service_id,
                merchant_trans_id=merchant_trans_id,
                merchant_prepare_id=merchant_prepare_id,
                amount_str=amount_str,
                sign_time=sign_time,
                sign_string=sign_string,
                click_error=error_code,
            )
        else:
            return {
                "error": self.ERROR_ACTION_NOT_FOUND,
                "error_note": f"Action '{action}' is not supported.",
            }

    def _handle_prepare(
        self,
        click_trans_id: str,
        service_id: str,
        merchant_trans_id: str,
        amount_str: str,
        sign_time: str,
        sign_string: str,
    ) -> dict[str, Any]:
        if not self.verify_prepare_signature(
            click_trans_id=click_trans_id,
            service_id=service_id,
            merchant_trans_id=merchant_trans_id,
            amount=amount_str,
            action="0",
            sign_time=sign_time,
            received_sign=sign_string,
        ):
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "error": self.ERROR_SIGN_CHECK_FAILED,
                "error_note": "SIGN CHECK FAILED!",
            }

        # Parse user from merchant_trans_id (format: "{user_id}:{plan}:{cycle}" or "{user_id}")
        user_id = merchant_trans_id.split(":")[0]
        user = User.objects.filter(id=user_id).first()
        if not user:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "error": self.ERROR_USER_NOT_FOUND,
                "error_note": "User not found.",
            }

        amount = Decimal(amount_str)
        if amount <= Decimal("0.00"):
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "error": self.ERROR_INVALID_AMOUNT,
                "error_note": "Invalid amount.",
            }

        # Create or update pending PaymentTransaction
        tx, _ = PaymentTransaction.objects.get_or_create(
            provider=PaymentTransaction.PROVIDER_CLICK,
            provider_transaction_id=click_trans_id,
            defaults={
                "user": user,
                "amount": amount,
                "currency": "UZS",
                "status": PaymentTransaction.STATUS_PENDING,
                "idempotency_key": click_trans_id,
            },
        )

        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": str(tx.id),
            "error": self.ERROR_SUCCESS,
            "error_note": "Success",
        }

    def _handle_complete(
        self,
        click_trans_id: str,
        service_id: str,
        merchant_trans_id: str,
        merchant_prepare_id: str,
        amount_str: str,
        sign_time: str,
        sign_string: str,
        click_error: int,
    ) -> dict[str, Any]:
        if not self.verify_complete_signature(
            click_trans_id=click_trans_id,
            service_id=service_id,
            merchant_trans_id=merchant_trans_id,
            merchant_prepare_id=merchant_prepare_id,
            amount=amount_str,
            action="1",
            sign_time=sign_time,
            received_sign=sign_string,
        ):
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "error": self.ERROR_SIGN_CHECK_FAILED,
                "error_note": "SIGN CHECK FAILED!",
            }

        tx = PaymentTransaction.objects.filter(
            provider=PaymentTransaction.PROVIDER_CLICK,
            provider_transaction_id=click_trans_id,
        ).first()
        if not tx:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "error": self.ERROR_TRANSACTION_NOT_FOUND,
                "error_note": "Transaction not found.",
            }

        if tx.status == PaymentTransaction.STATUS_SUCCEEDED:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": str(tx.id),
                "error": self.ERROR_ALREADY_PAID,
                "error_note": "Already paid.",
            }

        # Check if Click reported an error
        if click_error < 0:
            tx.status = PaymentTransaction.STATUS_FAILED
            tx.failure_code = f"CLICK_ERROR_{click_error}"
            tx.failure_reason = "Payment rejected by Click"
            tx.save()
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "error": self.ERROR_TRANSACTION_CANCELLED,
                "error_note": "Transaction cancelled by provider.",
            }

        # Successful completion -> Activate subscription
        parts = merchant_trans_id.split(":")
        target_plan = (
            parts[1]
            if len(parts) > 1
            else (User.PLAN_PRO if tx.amount >= Decimal("199000.00") else User.PLAN_CREATOR)
        )
        billing_cycle = parts[2] if len(parts) > 2 else Subscription.CYCLE_MONTHLY

        sub, tx = SubscriptionLifecycleService.activate_subscription(
            user=tx.user,
            plan=target_plan,
            billing_cycle=billing_cycle,
            provider=PaymentTransaction.PROVIDER_CLICK,
            provider_transaction_id=click_trans_id,
            amount=tx.amount,
        )

        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": str(tx.id),
            "error": self.ERROR_SUCCESS,
            "error_note": "Success",
        }
