"""
Payment Gateways package (VC-101).
Exports Payme and Click gateways for Uzbekistan merchant integrations.
"""

from .base import BasePaymentGateway
from .click import ClickGateway
from .payme import PaymeGateway

__all__ = ["BasePaymentGateway", "PaymeGateway", "ClickGateway"]
