"""Abstract Base Class for Voice Model Adapters in VoiceClone."""

from abc import ABC, abstractmethod
from typing import Any


class VoiceModelAdapter(ABC):
    """Unified interface decoupling speech synthesis models from web API delivery."""

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        """Unique identifier for this model adapter (e.g., 'openvoice_v2')."""
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Checkpoint or release version (e.g., 'v2.0.0-mit')."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Declared model capabilities.

        Example:
        {
            "languages": ["uz", "en"],
            "supports_voice_cloning": True,
            "sample_rate": 24000,
            "license": "MIT",
            "tier": "PRODUCTION_APPROVED"
        }
        """
        pass

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Check hardware health, model load status, and device statistics."""
        pass

    @abstractmethod
    async def validate_reference(self, reference_audio_bytes: bytes) -> dict[str, Any]:
        """Inspect reference audio for duration, noise level, sample rate, and voice quality.

        Returns metadata dict or raises InvalidAudioReferenceError.
        """
        pass

    @abstractmethod
    async def extract_speaker_embedding(self, reference_audio_bytes: bytes) -> bytes:
        """Extract tone color or speaker embedding bytes from reference audio."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str,
        speaker_embedding: bytes | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        """Synthesize normalized text into raw WAV audio bytes.

        Returns:
            tuple[bytes, dict[str, Any]]: (wav_bytes, metadata_dict)
        """
        pass

    @abstractmethod
    async def load_model(self) -> None:
        """Load checkpoint weights into device memory."""
        pass

    @abstractmethod
    async def unload_model(self) -> None:
        """Safely release weights and free GPU VRAM / system RAM."""
        pass
