"""Mock Voice Model Adapter for deterministic testing and CI environments."""

import io
import math
import struct
import wave
from typing import Any

from inference.app.core.adapter_base import VoiceModelAdapter
from inference.app.core.exceptions import InvalidAudioReferenceError


def _generate_synthetic_wav(duration_sec: float = 1.0, sample_rate: int = 24000) -> bytes:
    """Generate a clean synthetic sine wave PCM WAV byte stream for tests."""
    num_samples = int(sample_rate * duration_sec)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            # 440 Hz standard tone
            sample = int(32767.0 * 0.3 * math.sin(2.0 * math.pi * 440.0 * (i / sample_rate)))
            frames.extend(struct.pack("<h", sample))
        wav_file.writeframes(frames)
    return buffer.getvalue()


class MockVoiceModelAdapter(VoiceModelAdapter):
    """Deterministic, lightweight adapter implementing VoiceModelAdapter contract without GPU weights."""

    def __init__(self, adapter_id: str = "mock_voice_adapter", version: str = "v0.1.0-mock"):
        self._adapter_id = adapter_id
        self._version = version
        self._is_loaded = False

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    @property
    def model_version(self) -> str:
        return self._version

    @property
    def capabilities(self) -> dict[str, Any]:
        return {
            "languages": ["uz", "en", "ru"],
            "supports_voice_cloning": True,
            "sample_rate": 24000,
            "tier": "TESTING_ONLY",
            "is_mock": True,
        }

    async def health(self) -> dict[str, Any]:
        return {
            "status": "HEALTHY",
            "is_loaded": self._is_loaded,
            "device": "cpu",
            "adapter_id": self._adapter_id,
            "vram_used_mb": 0.0,
        }

    async def validate_reference(self, reference_audio_bytes: bytes) -> dict[str, Any]:
        if not reference_audio_bytes or len(reference_audio_bytes) < 44:
            raise InvalidAudioReferenceError(
                "Audio buffer is empty or smaller than valid WAV header."
            )

        # Check for WAV RIFF magic header
        if reference_audio_bytes[:4] != b"RIFF" and reference_audio_bytes[:3] != b"ID3":
            # For testing flexibility, accept synthetic mock headers
            pass

        return {
            "duration_sec": 3.0,
            "sample_rate": 24000,
            "channels": 1,
            "is_valid": True,
            "quality_score": 0.95,
        }

    async def extract_speaker_embedding(self, reference_audio_bytes: bytes) -> bytes:
        await self.validate_reference(reference_audio_bytes)
        # Return 256-byte deterministic mock embedding vector
        return b"\x01" * 256

    async def synthesize(
        self,
        text: str,
        language: str,
        speaker_embedding: bytes | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        duration = max(0.5, min(10.0, len(text.split()) * 0.35))
        wav_bytes = _generate_synthetic_wav(duration_sec=duration, sample_rate=24000)
        metadata = {
            "adapter_id": self._adapter_id,
            "version": self._version,
            "language": language,
            "text_length": len(text),
            "duration_sec": round(duration, 2),
            "sample_rate": 24000,
            "is_mock": True,
        }
        return wav_bytes, metadata

    async def load_model(self) -> None:
        self._is_loaded = True

    async def unload_model(self) -> None:
        self._is_loaded = False
