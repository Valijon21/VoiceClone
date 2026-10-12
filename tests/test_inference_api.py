"""Tests for FastAPI AI Inference Service Endpoints (VC-032, VC-038, VC-039)."""

import base64

import pytest
from httpx import ASGITransport, AsyncClient

from inference.app.adapters.mock_adapter import _generate_synthetic_wav
from inference.app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify GET /health returns service version and registered models."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert "service_version" in data
        assert isinstance(data["registered_models"], list)


@pytest.mark.asyncio
async def test_synthesize_endpoint_success():
    """Verify POST /synthesize returns Base64 WAV audio and metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "Salom, O‘zbekiston! Bu ovoz sintezi testi.",
            "language": "uz",
            "speed": 1.0,
        }
        response = await client.post("/synthesize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "WAV"
        assert data["duration_sec"] > 0
        assert data["sample_rate"] == 24000

        # Decode and verify WAV header
        raw_audio = base64.b64decode(data["audio_base64"])
        assert raw_audio.startswith(b"RIFF")


@pytest.mark.asyncio
async def test_synthesize_with_reference_voice():
    """Verify POST /synthesize works with user-supplied reference audio."""
    valid_wav = _generate_synthetic_wav(duration_sec=2.0)
    b64_ref = base64.b64encode(valid_wav).decode("ascii")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "Ovoz klonlash rejimi tekshirilmoqda.",
            "language": "uz",
            "reference_audio_base64": b64_ref,
        }
        response = await client.post("/synthesize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "WAV"


@pytest.mark.asyncio
async def test_synthesize_empty_text_returns_structured_error():
    """Verify empty text validation fails with structured JSON error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "   ",
            "language": "uz",
        }
        response = await client.post("/synthesize", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_INPUT_TEXT"


@pytest.mark.asyncio
async def test_extract_speaker_endpoint():
    """Verify POST /extract-speaker returns valid embedding vector."""
    valid_wav = _generate_synthetic_wav(duration_sec=2.0)
    b64_ref = base64.b64encode(valid_wav).decode("ascii")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"audio_base64": b64_ref}
        response = await client.post("/extract-speaker", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "embedding_base64" in data
        assert data["duration_sec"] > 0
