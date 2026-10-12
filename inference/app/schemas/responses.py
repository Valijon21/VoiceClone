"""Response schemas for FastAPI Inference endpoints."""

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health status and hardware metrics."""

    status: str
    service_version: str
    device: str
    vram_free_mb: float | None = None
    registered_models: list[dict[str, Any]]


class SynthesisResponse(BaseModel):
    """Output payload containing generated audio and playback metadata."""

    audio_base64: str
    duration_sec: float
    sample_rate: int
    format: str = "WAV"
    metadata: dict[str, Any]


class SpeakerResponse(BaseModel):
    """Output payload from speaker feature extraction."""

    embedding_base64: str
    duration_sec: float
    sample_rate: int
    channels: int


class ErrorResponse(BaseModel):
    """Structured error payload returned on exceptions."""

    error_code: str
    message: str
    details: dict[str, Any] | None = None
