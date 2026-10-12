"""
Abstract Payment Gateway Base Interface (VC-101).
Provides contract for generating checkout links, signature verification, and webhook dispatch.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from apps.accounts.models import User


class BasePaymentGateway(ABC):
    """Abstract contract for payment gateway integrations."""

    @abstractmethod
    def generate_payment_link(
        self,
        user: User,
        plan: str,
        amount: Decimal,
        billing_cycle: str = "MONTHLY",
        return_url: str | None = None,
    ) -> str:
        """Generate a redirect URL or deep link for customer checkout."""
        pass

    @abstractmethod
    def verify_request_auth(self, headers: dict[str, Any], raw_body: bytes) -> bool:
        """Verify authenticity of the incoming webhook request from provider."""
        pass

    @abstractmethod
    def process_webhook(self, data: dict[str, Any], headers: dict[str, Any]) -> dict[str, Any]:
        """Process incoming provider callback and return appropriate provider-formatted response."""
        pass
