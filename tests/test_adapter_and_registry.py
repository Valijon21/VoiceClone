"""Tests for VoiceModelAdapter interface contract and ModelRegistry License Gate."""

import pytest

from inference.app.adapters.mock_adapter import MockVoiceModelAdapter, _generate_synthetic_wav
from inference.app.core.adapter_base import VoiceModelAdapter
from inference.app.core.exceptions import (
    InvalidAudioReferenceError,
    ModelNotApprovedError,
    ModelNotFoundError,
)
from inference.app.core.registry import ModelRegistry


@pytest.mark.asyncio
async def test_mock_adapter_satisfies_contract():
    """Verify that MockVoiceModelAdapter adheres to all VoiceModelAdapter contract requirements."""
    adapter = MockVoiceModelAdapter()
    assert isinstance(adapter, VoiceModelAdapter)
    assert adapter.adapter_id == "mock_voice_adapter"
    assert "languages" in adapter.capabilities
    assert adapter.capabilities["is_mock"] is True

    # Health check
    health_info = await adapter.health()
    assert health_info["status"] == "HEALTHY"
    assert health_info["device"] == "cpu"

    # Reference validation
    valid_wav = _generate_synthetic_wav(duration_sec=2.0)
    validation = await adapter.validate_reference(valid_wav)
    assert validation["is_valid"] is True

    # Invalid reference
    with pytest.raises(InvalidAudioReferenceError):
        await adapter.validate_reference(b"too_short")

    # Speaker extraction
    embedding = await adapter.extract_speaker_embedding(valid_wav)
    assert isinstance(embedding, bytes)
    assert len(embedding) == 256

    # Synthesis
    wav_bytes, meta = await adapter.synthesize(
        text="Salom, bu test sintez audiosi.",
        language="uz",
        speaker_embedding=embedding,
    )
    assert isinstance(wav_bytes, bytes)
    assert wav_bytes.startswith(b"RIFF")
    assert meta["language"] == "uz"
    assert meta["is_mock"] is True


def test_registry_dev_mode_allows_testing_adapter():
    """Development registry allows registering testing adapters."""
    registry = ModelRegistry(is_production=False)
    adapter = MockVoiceModelAdapter()

    registry.register(
        adapter=adapter,
        license_name="MIT",
        license_status="VERIFIED",
        commercial_approved=True,
    )

    retrieved = registry.get_adapter("mock_voice_adapter")
    assert retrieved is adapter
    assert "uz" in registry.get_supported_languages()


def test_registry_production_gate_blocks_unapproved_model():
    """Production registry rejects models with non-verified or unapproved licenses."""
    registry = ModelRegistry(is_production=True)
    adapter = MockVoiceModelAdapter(adapter_id="unapproved_model")

    # Attempting to register an unapproved model in production mode must fail
    with pytest.raises(ModelNotApprovedError) as exc_info:
        registry.register(
            adapter=adapter,
            license_name="CC-BY-NC",
            license_status="REJECTED",
            commercial_approved=False,
        )

    assert "MODEL_LICENSE_NOT_APPROVED" in str(exc_info.value.error_code)


def test_registry_not_found_raises():
    """Querying an unknown adapter raises ModelNotFoundError."""
    registry = ModelRegistry(is_production=False)
    with pytest.raises(ModelNotFoundError):
        registry.get_adapter("non_existent_adapter_id")
