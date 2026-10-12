"""Audio processing, validation, inspection, and concatenation engine."""

import io
import struct
import wave
from typing import Any

from inference.app.core.exceptions import InvalidAudioReferenceError


def inspect_wav_audio(audio_bytes: bytes) -> dict[str, Any]:
    """Inspect WAV audio bytes and extract structural metadata without external heavy libraries."""
    if not audio_bytes or len(audio_bytes) < 44:
        raise InvalidAudioReferenceError("Audio buffer is empty or smaller than valid WAV header.")

    if not audio_bytes.startswith(b"RIFF") or b"WAVE" not in audio_bytes[:12]:
        raise InvalidAudioReferenceError("Audio format is not a valid RIFF/WAVE stream.")

    try:
        buffer = io.BytesIO(audio_bytes)
        with wave.open(buffer, "rb") as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            duration_sec = n_frames / float(framerate) if framerate > 0 else 0.0

            # Read a sample block to check for silence or extreme clipping
            raw_frames = wf.readframes(min(n_frames, 48000))
            is_silent = True
            if sample_width == 2:
                for i in range(0, len(raw_frames) - 1, 2):
                    val = struct.unpack("<h", raw_frames[i : i + 2])[0]
                    if abs(val) > 200:  # Noise threshold above true silence
                        is_silent = False
                        break

            return {
                "format": "WAV",
                "channels": channels,
                "sample_width": sample_width,
                "sample_rate": framerate,
                "frame_count": n_frames,
                "duration_sec": round(duration_sec, 3),
                "is_silent": is_silent,
            }
    except Exception as exc:
        raise InvalidAudioReferenceError(f"Failed to parse audio wave data: {exc}") from exc


def validate_reference_audio(
    audio_bytes: bytes,
    max_size_mb: float = 15.0,
    min_duration_sec: float = 1.0,
    max_duration_sec: float = 30.0,
) -> dict[str, Any]:
    """Validate user-uploaded reference audio against duration, file size, and quality limits."""
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise InvalidAudioReferenceError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb:.1f} MB)."
        )

    info = inspect_wav_audio(audio_bytes)
    duration = info["duration_sec"]

    if duration < min_duration_sec:
        raise InvalidAudioReferenceError(
            f"Audio duration ({duration:.2f}s) is shorter than required minimum ({min_duration_sec:.1f}s)."
        )

    if duration > max_duration_sec:
        raise InvalidAudioReferenceError(
            f"Audio duration ({duration:.2f}s) exceeds maximum allowed ({max_duration_sec:.1f}s)."
        )

    if info["is_silent"]:
        raise InvalidAudioReferenceError(
            "Audio appears to be completely silent or below audible threshold."
        )

    return info


def concatenate_wav_chunks(wav_chunks: list[bytes]) -> bytes:
    """Concatenate multiple single-channel or dual-channel WAV streams into one seamless WAV."""
    if not wav_chunks:
        return b""
    if len(wav_chunks) == 1:
        return wav_chunks[0]

    all_frames = bytearray()
    first_info = inspect_wav_audio(wav_chunks[0])
    channels = first_info["channels"]
    sample_width = first_info["sample_width"]
    sample_rate = first_info["sample_rate"]

    for chunk in wav_chunks:
        buffer = io.BytesIO(chunk)
        with wave.open(buffer, "rb") as wf:
            all_frames.extend(wf.readframes(wf.getnframes()))

    output_buffer = io.BytesIO()
    with wave.open(output_buffer, "wb") as out_wf:
        out_wf.setnchannels(channels)
        out_wf.setsampwidth(sample_width)
        out_wf.setframerate(sample_rate)
        out_wf.writeframes(all_frames)

    return output_buffer.getvalue()
