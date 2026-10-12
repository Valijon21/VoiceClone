"""Tests for Celery asynchronous processing, idempotency, failure mapping, and retention cleanup (Phase 05)."""

import base64
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from apps.audio.models import AudioAsset
from apps.audio.storage import AudioStorageService
from apps.generations.models import GenerationJob
from apps.generations.tasks import cleanup_expired_audio_assets, process_speech_synthesis_job
from apps.voices.models import ConsentRecord, VoiceProfile
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from inference.app.adapters.mock_adapter import _generate_synthetic_wav

User = get_user_model()


@pytest.fixture
def auth_user(db):
    return User.objects.create_user(
        username="celery_user",
        email="celery@voiceclone.ai",
        password="ValidPassword123!",
        is_verified=True,
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="intruder_user",
        email="intruder@voiceclone.ai",
        password="ValidPassword123!",
    )


@pytest.fixture
def verified_voice(auth_user):
    voice = VoiceProfile.objects.create(owner=auth_user, name="Verified Voice", language="uz")
    ConsentRecord.objects.create(
        voice_profile=voice,
        user=auth_user,
        consent_text="Legal declaration of ownership.",
        status=ConsentRecord.STATUS_VERIFIED,
    )
    return voice


@pytest.mark.django_db
def test_async_task_successful_synthesis(auth_user, verified_voice):
    """Test process_speech_synthesis_job successfully consumes inference output and saves GeneratedAudio (VC-050, VC-051)."""
    job = GenerationJob.objects.create(
        user=auth_user,
        voice_profile=verified_voice,
        model_id="openvoice_v2",
        language="uz",
        input_text="Matn asinxron sintez qilinmoqda.",
    )

    fake_wav = _generate_synthetic_wav(duration_sec=2.0)
    b64_wav = base64.b64encode(fake_wav).decode("ascii")

    # Mock httpx response from inference service
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "audio_base64": b64_wav,
        "duration_sec": 2.0,
        "sample_rate": 24000,
        "format": "WAV",
        "metadata": {"test": True},
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = process_speech_synthesis_job(str(job.id))

    assert res["status"] == "SUCCEEDED"
    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_SUCCEEDED
    assert job.progress_percent == 100
    assert hasattr(job, "result_audio")
    assert job.result_audio.duration_sec == 2.0


@pytest.mark.django_db
def test_failure_mapping_non_retryable(auth_user):
    """Test inference 400 error maps to permanent FAILED state without retrying (VC-054)."""
    job = GenerationJob.objects.create(
        user=auth_user,
        model_id="openvoice_v2",
        language="uz",
        input_text="Noto‘g‘ri matn.",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {
        "error_code": "INVALID_INPUT_TEXT",
        "message": "Input text has invalid characters.",
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = process_speech_synthesis_job(str(job.id))

    assert res["status"] == "FAILED"
    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_FAILED
    assert "INVALID_INPUT_TEXT" in job.error_message


@pytest.mark.django_db
def test_idempotency_key_prevents_duplicate_jobs(auth_user):
    """Submitting the same idempotency_key returns the same job without duplication (VC-052)."""
    client = APIClient()
    client.force_authenticate(user=auth_user)

    payload = {
        "model_id": "openvoice_v2",
        "language": "uz",
        "input_text": "Idempotent speech request.",
        "idempotency_key": "unique-request-key-9999",
    }

    resp1 = client.post("/api/v1/generations/jobs/", data=payload)
    resp2 = client.post("/api/v1/generations/jobs/", data=payload)

    assert resp1.status_code == status.HTTP_201_CREATED
    assert resp2.status_code == status.HTTP_201_CREATED
    assert resp1.data["id"] == resp2.data["id"]
    assert (
        GenerationJob.objects.filter(
            user=auth_user, idempotency_key="unique-request-key-9999"
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_user_cannot_access_other_user_job(auth_user, other_user):
    """Enforce Result Ownership: Users cannot see or download others' generation jobs (VC-055)."""
    job = GenerationJob.objects.create(
        user=auth_user,
        model_id="openvoice_v2",
        language="uz",
        input_text="Private text.",
    )

    client = APIClient()
    client.force_authenticate(user=other_user)

    resp = client.get(f"/api/v1/generations/jobs/{job.id}/")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_retention_cleanup_job(auth_user):
    """Retention job purges expired generated audio files older than threshold (VC-056)."""
    old_asset = AudioStorageService.save_audio_bytes(
        user=auth_user,
        filename="old_generated.wav",
        audio_bytes=b"RIFF" + b"\x00" * 40,
        asset_type=AudioAsset.TYPE_GENERATED,
    )
    # Manually backdate created_at to 10 days ago
    AudioAsset.objects.filter(id=old_asset.id).update(
        created_at=timezone.now() - timedelta(days=10)
    )

    fresh_asset = AudioStorageService.save_audio_bytes(
        user=auth_user,
        filename="fresh_generated.wav",
        audio_bytes=b"RIFF" + b"\x00" * 40,
        asset_type=AudioAsset.TYPE_GENERATED,
    )

    result = cleanup_expired_audio_assets(retention_days=7)
    assert result["deleted_count"] >= 1
    assert not AudioAsset.objects.filter(id=old_asset.id).exists()
    assert AudioAsset.objects.filter(id=fresh_asset.id).exists()
