"""Tests for audio processing, validation, and chunk concatenation (VC-033, VC-037)."""

import pytest

from inference.app.adapters.mock_adapter import _generate_synthetic_wav
from inference.app.core.audio_processor import (
    concatenate_wav_chunks,
    inspect_wav_audio,
    validate_reference_audio,
)
from inference.app.core.exceptions import InvalidAudioReferenceError


def test_inspect_valid_wav():
    """Verify inspection extracts correct sample rate, channels, and duration."""
    wav_bytes = _generate_synthetic_wav(duration_sec=1.5, sample_rate=24000)
    info = inspect_wav_audio(wav_bytes)

    assert info["format"] == "WAV"
    assert info["sample_rate"] == 24000
    assert info["channels"] == 1
    assert 1.4 <= info["duration_sec"] <= 1.6
    assert info["is_silent"] is False


def test_validate_audio_rejects_empty_or_corrupt():
    """Verify non-WAV data raises InvalidAudioReferenceError."""
    with pytest.raises(InvalidAudioReferenceError):
        inspect_wav_audio(b"not_a_wav_file")

    with pytest.raises(InvalidAudioReferenceError):
        inspect_wav_audio(b"")


def test_validate_audio_duration_limits():
    """Verify audio under 1s or over 30s is rejected."""
    short_wav = _generate_synthetic_wav(duration_sec=0.4)
    with pytest.raises(InvalidAudioReferenceError) as exc_info:
        validate_reference_audio(short_wav, min_duration_sec=1.0)
    assert "shorter than required minimum" in str(exc_info.value)


def test_concatenate_wav_chunks():
    """Verify concatenating two 1.0s chunks results in a ~2.0s valid WAV."""
    chunk1 = _generate_synthetic_wav(duration_sec=1.0, sample_rate=24000)
    chunk2 = _generate_synthetic_wav(duration_sec=1.0, sample_rate=24000)

    combined = concatenate_wav_chunks([chunk1, chunk2])
    info = inspect_wav_audio(combined)

    assert info["sample_rate"] == 24000
    assert 1.9 <= info["duration_sec"] <= 2.1
