"""Request schemas for FastAPI Inference endpoints."""

from pydantic import BaseModel, Field


class SynthesisRequest(BaseModel):
    """Payload for text-to-speech synthesis with optional voice cloning."""

    text: str = Field(
        ..., min_length=1, max_length=5000, description="Text to synthesize into speech."
    )
    language: str = Field(default="uz", description="Target language code: 'uz', 'en', or 'ru'.")
    adapter_id: str | None = Field(default=None, description="Requested model adapter identifier.")
    reference_audio_base64: str | None = Field(
        default=None,
        description="Base64-encoded reference WAV audio for voice color cloning.",
    )
    speed: float = Field(
        default=1.0, ge=0.5, le=2.0, description="Speech rate playback multiplier."
    )


class ExtractSpeakerRequest(BaseModel):
    """Payload for speaker embedding extraction from reference audio."""

    audio_base64: str = Field(..., min_length=44, description="Base64-encoded WAV audio.")
    adapter_id: str | None = Field(default=None, description="Requested model adapter identifier.")
