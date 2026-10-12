"""
Payme Merchant Payment Gateway (VC-101).
Implements the official Payme JSON-RPC 2.0 merchant protocol for subscription payments in Uzbekistan.
"""

from __future__ import annotations

import base64
import time
from decimal import Decimal
from typing import Any

from django.conf import settings

from apps.accounts.models import PaymentTransaction, Subscription, User
from apps.accounts.services import SubscriptionLifecycleService

from .base import BasePaymentGateway


class PaymeGateway(BasePaymentGateway):
    """
    Payme JSON-RPC 2.0 Merchant implementation.
    Operates in tiyins (1 UZS = 100 tiyin).
    """

    # Payme standard error codes
    ERROR_INTERNAL = -32400
    ERROR_INSUFFICIENT_PRIVILEGE = -32504
    ERROR_INVALID_AMOUNT = -31001
    ERROR_TRANSACTION_NOT_FOUND = -31003
    ERROR_CANNOT_PERFORM = -31008
    ERROR_ACCOUNT_NOT_FOUND = -31050
    ERROR_ALREADY_DONE = -31007

    # Transaction states in Payme protocol
    STATE_CREATED = 1
    STATE_COMPLETED = 2
    STATE_CANCELLED = -1
    STATE_CANCELLED_AFTER_COMPLETE = -2

    def __init__(self, merchant_id: str | None = None, secret_key: str | None = None):
        self.merchant_id = merchant_id or getattr(
            settings, "PAYME_MERCHANT_ID", "mock_payme_merchant_id"
        )
        self.secret_key = secret_key or getattr(
            settings, "PAYME_SECRET_KEY", "mock_payme_secret_key_test"
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
        Generates checkout redirect URL using Payme merchant format.
        Base64 payload format: m={merchant_id};ac.user_id={user_id};ac.plan={plan};a={amount_tiyin}
        """
        amount_tiyin = int(amount * 100)
        params = (
            f"m={self.merchant_id};"
            f"ac.user_id={user.id};"
            f"ac.plan={plan};"
            f"ac.billing_cycle={billing_cycle};"
            f"a={amount_tiyin}"
        )
        if return_url:
            params += f";c={return_url}"

        encoded = base64.b64encode(params.encode("utf-8")).decode("utf-8")
        return f"https://checkout.paycom.uz/{encoded}"

    def verify_request_auth(self, headers: dict[str, Any], raw_body: bytes) -> bool:
        """
        Validates HTTP Basic Auth: 'Paycom:<secret_key>'
        """
        auth_header = headers.get("Authorization") or headers.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Basic "):
            return False

        try:
            encoded_credentials = auth_header.split(" ", 1)[1]
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")
            parts = decoded.split(":", 1)
            if len(parts) != 2:
                return False
            username, key = parts
            return key == self.secret_key
        except Exception:
            return False

    def process_webhook(self, data: dict[str, Any], headers: dict[str, Any]) -> dict[str, Any]:
        """
        Routes and executes JSON-RPC 2.0 methods according to Payme specification.
        """
        request_id = data.get("id")
        method = data.get("method")
        params = data.get("params", {})

        if not self.verify_request_auth(headers, b""):
            return {
                "error": {
                    "code": self.ERROR_INSUFFICIENT_PRIVILEGE,
                    "message": "Insufficient privilege or invalid Authorization header.",
                },
                "id": request_id,
            }

        handlers = {
            "CheckPerformTransaction": self._handle_check_perform_transaction,
            "CreateTransaction": self._handle_create_transaction,
            "PerformTransaction": self._handle_perform_transaction,
            "CancelTransaction": self._handle_cancel_transaction,
            "CheckTransaction": self._handle_check_transaction,
        }

        handler = handlers.get(method)
        if not handler:
            return {
                "error": {"code": -32601, "message": f"Method '{method}' not found."},
                "id": request_id,
            }

        try:
            result = handler(params)
            return {"result": result, "id": request_id}
        except PaymeException as pe:
            return {"error": {"code": pe.code, "message": pe.message}, "id": request_id}
        except Exception as exc:
            return {"error": {"code": self.ERROR_INTERNAL, "message": str(exc)}, "id": request_id}

    # -------------------------------------------------------------------------
    # JSON-RPC Handlers
    # -------------------------------------------------------------------------

    def _handle_check_perform_transaction(self, params: dict[str, Any]) -> dict[str, Any]:
        account = params.get("account", {})
        user_id = account.get("user_id")
        plan = account.get("plan", User.PLAN_CREATOR)
        amount_tiyin = params.get("amount", 0)

        user = User.objects.filter(id=user_id).first()
        if not user:
            raise PaymeException(self.ERROR_ACCOUNT_NOT_FOUND, "User account not found.")

        expected_price_uzs = Subscription.PLAN_PRICES_UZS.get(plan, 0.0)
        expected_tiyin = int(expected_price_uzs * 100)

        if amount_tiyin != expected_tiyin:
            raise PaymeException(
                self.ERROR_INVALID_AMOUNT,
                f"Amount mismatch. Expected {expected_tiyin} tiyin, got {amount_tiyin} tiyin.",
            )

        return {"allow": True}

    def _handle_create_transaction(self, params: dict[str, Any]) -> dict[str, Any]:
        payme_id = params.get("id")
        timestamp_ms = params.get("time", int(time.time() * 1000))
        amount_tiyin = params.get("amount", 0)
        account = params.get("account", {})
        user_id = account.get("user_id")

        user = User.objects.filter(id=user_id).first()
        if not user:
            raise PaymeException(self.ERROR_ACCOUNT_NOT_FOUND, "User account not found.")

        # Check if transaction already exists
        tx = PaymentTransaction.objects.filter(
            provider=PaymentTransaction.PROVIDER_PAYME, provider_transaction_id=payme_id
        ).first()
        if tx:
            if (
                tx.status == PaymentTransaction.STATUS_FAILED
                or tx.status == PaymentTransaction.STATUS_REFUNDED
            ):
                raise PaymeException(self.ERROR_CANNOT_PERFORM, "Transaction in terminated state.")
            created_ms = int(tx.created_at.timestamp() * 1000)
            state = (
                self.STATE_COMPLETED
                if tx.status == PaymentTransaction.STATUS_SUCCEEDED
                else self.STATE_CREATED
            )
            return {
                "create_time": created_ms,
                "transaction": str(tx.id),
                "state": state,
            }

        # Validate amount
        self._handle_check_perform_transaction(params)

        amount_uzs = Decimal(str(amount_tiyin)) / Decimal("100.0")
        tx = PaymentTransaction.objects.create(
            user=user,
            provider=PaymentTransaction.PROVIDER_PAYME,
            provider_transaction_id=payme_id,
            amount=amount_uzs,
            currency="UZS",
            status=PaymentTransaction.STATUS_PENDING,
            idempotency_key=payme_id,
        )

        return {
            "create_time": timestamp_ms,
            "transaction": str(tx.id),
            "state": self.STATE_CREATED,
        }

    def _handle_perform_transaction(self, params: dict[str, Any]) -> dict[str, Any]:
        payme_id = params.get("id")
        tx = PaymentTransaction.objects.filter(
            provider=PaymentTransaction.PROVIDER_PAYME, provider_transaction_id=payme_id
        ).first()
        if not tx:
            raise PaymeException(self.ERROR_TRANSACTION_NOT_FOUND, "Transaction not found.")

        now_ms = int(time.time() * 1000)

        if tx.status == PaymentTransaction.STATUS_SUCCEEDED:
            perform_ms = int(tx.updated_at.timestamp() * 1000)
            return {
                "transaction": str(tx.id),
                "perform_time": perform_ms,
                "state": self.STATE_COMPLETED,
            }

        if tx.status != PaymentTransaction.STATUS_PENDING:
            raise PaymeException(
                self.ERROR_CANNOT_PERFORM, "Cannot perform completed/canceled transaction."
            )

        # Determine target plan from user or default
        user = tx.user
        plan = User.PLAN_PRO if tx.amount >= Decimal("199000.00") else User.PLAN_CREATOR

        # Activate via SubscriptionLifecycleService
        sub, tx = SubscriptionLifecycleService.activate_subscription(
            user=user,
            plan=plan,
            billing_cycle=Subscription.CYCLE_MONTHLY,
            provider=PaymentTransaction.PROVIDER_PAYME,
            provider_transaction_id=payme_id,
            amount=tx.amount,
        )

        return {
            "transaction": str(tx.id),
            "perform_time": now_ms,
            "state": self.STATE_COMPLETED,
        }

    def _handle_cancel_transaction(self, params: dict[str, Any]) -> dict[str, Any]:
        payme_id = params.get("id")
        reason = params.get("reason", 1)

        tx = PaymentTransaction.objects.filter(
            provider=PaymentTransaction.PROVIDER_PAYME, provider_transaction_id=payme_id
        ).first()
        if not tx:
            raise PaymeException(self.ERROR_TRANSACTION_NOT_FOUND, "Transaction not found.")

        now_ms = int(time.time() * 1000)

        if tx.status == PaymentTransaction.STATUS_PENDING:
            tx.status = PaymentTransaction.STATUS_FAILED
            tx.failure_code = f"PAYME_REASON_{reason}"
            tx.failure_reason = "Cancelled prior to completion by Payme"
            tx.save()
            return {
                "transaction": str(tx.id),
                "cancel_time": now_ms,
                "state": self.STATE_CANCELLED,
            }

        if tx.status == PaymentTransaction.STATUS_SUCCEEDED:
            # Process refund safely
            SubscriptionLifecycleService.process_refund(
                transaction_obj=tx,
                refund_amount=tx.amount,
                reason=f"Payme cancellation reason {reason}",
            )
            return {
                "transaction": str(tx.id),
                "cancel_time": now_ms,
                "state": self.STATE_CANCELLED_AFTER_COMPLETE,
            }

        cancel_ms = int(tx.updated_at.timestamp() * 1000)
        state = (
            self.STATE_CANCELLED_AFTER_COMPLETE
            if tx.status == PaymentTransaction.STATUS_REFUNDED
            else self.STATE_CANCELLED
        )
        return {
            "transaction": str(tx.id),
            "cancel_time": cancel_ms,
            "state": state,
        }

    def _handle_check_transaction(self, params: dict[str, Any]) -> dict[str, Any]:
        payme_id = params.get("id")
        tx = PaymentTransaction.objects.filter(
            provider=PaymentTransaction.PROVIDER_PAYME, provider_transaction_id=payme_id
        ).first()
        if not tx:
            raise PaymeException(self.ERROR_TRANSACTION_NOT_FOUND, "Transaction not found.")

        create_ms = int(tx.created_at.timestamp() * 1000)
        perform_ms = (
            int(tx.updated_at.timestamp() * 1000)
            if tx.status == PaymentTransaction.STATUS_SUCCEEDED
            else 0
        )
        cancel_ms = (
            int(tx.updated_at.timestamp() * 1000)
            if tx.status in (PaymentTransaction.STATUS_FAILED, PaymentTransaction.STATUS_REFUNDED)
            else 0
        )

        state_map = {
            PaymentTransaction.STATUS_PENDING: self.STATE_CREATED,
            PaymentTransaction.STATUS_SUCCEEDED: self.STATE_COMPLETED,
            PaymentTransaction.STATUS_FAILED: self.STATE_CANCELLED,
            PaymentTransaction.STATUS_REFUNDED: self.STATE_CANCELLED_AFTER_COMPLETE,
        }
        state = state_map.get(tx.status, self.STATE_CREATED)

        return {
            "create_time": create_ms,
            "perform_time": perform_ms,
            "cancel_time": cancel_ms,
            "transaction": str(tx.id),
            "state": state,
            "reason": None,
        }


class PaymeException(Exception):
    """Custom exception containing Payme protocol error code."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
