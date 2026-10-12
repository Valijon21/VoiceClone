"""Model Registry & License Gate for AI Inference."""

from typing import Any

from inference.app.core.adapter_base import VoiceModelAdapter
from inference.app.core.exceptions import ModelNotApprovedError, ModelNotFoundError


class ModelRegistry:
    """Central registry enforcing license audits, language coverage, and lifecycle for voice models."""

    def __init__(self, is_production: bool = False):
        self._adapters: dict[str, VoiceModelAdapter] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._is_production = is_production

    def register(
        self,
        adapter: VoiceModelAdapter,
        license_name: str,
        license_status: str,
        commercial_approved: bool,
    ) -> None:
        """Register a model adapter with license and commercial validation.

        Args:
            adapter: VoiceModelAdapter instance
            license_name: e.g. "MIT", "Apache-2.0", "CPML"
            license_status: "VERIFIED", "NEEDS_REVIEW", or "REJECTED"
            commercial_approved: True if commercially usable without restrictions
        """
        adapter_id = adapter.adapter_id

        # License Gate: In production, non-verified or unapproved models are blocked
        if self._is_production and (license_status != "VERIFIED" or not commercial_approved):
            raise ModelNotApprovedError(
                model_id=adapter_id,
                reason=(
                    f"License '{license_name}' (status: {license_status}, commercial: {commercial_approved}) "
                    f"fails production gate. Check MODEL_LICENSES.md."
                ),
            )

        self._adapters[adapter_id] = adapter
        self._metadata[adapter_id] = {
            "adapter_id": adapter_id,
            "version": adapter.model_version,
            "license": license_name,
            "license_status": license_status,
            "commercial_approved": commercial_approved,
            "capabilities": adapter.capabilities,
        }

    def get_adapter(self, adapter_id: str) -> VoiceModelAdapter:
        """Retrieve an adapter by ID or raise ModelNotFoundError."""
        if adapter_id not in self._adapters:
            raise ModelNotFoundError(model_id=adapter_id)
        return self._adapters[adapter_id]

    def list_models(self) -> list[dict[str, Any]]:
        """List all approved and registered model profiles."""
        return list(self._metadata.values())

    def get_supported_languages(self) -> set[str]:
        """Aggregate all supported language codes across active adapters."""
        languages: set[str] = set()
        for meta in self._metadata.values():
            caps = meta.get("capabilities", {})
            langs = caps.get("languages", [])
            languages.update(langs)
        return languages
