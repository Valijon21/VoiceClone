"""Comprehensive unit and integration tests for Beta Operational Analytics & Telemetry (VC-090).

Validates:
- Privacy compliance (No audio or private prompt content saved)
- Percentile latency calculations (p50, p95)
- Real-Time Factor (RTF) calculations
- Structured error categorization
- API security & permissions (IsAdminUser guard)
- Time period filtering (24h, 7d, all)
"""

import os
import uuid
from datetime import timedelta

import pytest
from apps.audit.analytics import (
    calculate_percentile,
    categorize_error,
    get_beta_analytics_summary,
    record_job_metric,
)
from apps.audit.models import OperationalMetric
from apps.generations.models import GenerationJob
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def standard_user(db):
    return User.objects.create_user(
        username="beta_user",
        email="beta_user@example.com",
        password="UserPassword123!",
        is_staff=False,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="beta_admin",
        email="beta_admin@example.com",
        password="AdminPassword123!",
        is_staff=True,
    )


@pytest.mark.django_db
def test_error_categorization():
    """Verify structured error category mapping from raw messages."""
    assert categorize_error("Consent was revoked or is unverified.") == "CONSENT_DENIED"
    assert categorize_error("Timed out waiting for upstream inference.") == "TIMEOUT"
    assert categorize_error("[INFERENCE_ERROR] 503 GPU busy; all slots taken") == "GPU_BUSY_503"
    assert categorize_error("CUDA out of memory (OOM)") == "GPU_BUSY_503"
    assert categorize_error("400 Bad Request: Unsupported language") == "CLIENT_ERROR_400"
    assert categorize_error("Maximum retries exceeded.") == "MAX_RETRIES_EXCEEDED"
    assert categorize_error("Connection refused by inference service") == "INFERENCE_OFFLINE"
    assert categorize_error("") == "NONE"


def test_percentile_calculations():
    """Verify p50 (median) and p95 calculations with edge cases."""
    assert calculate_percentile([], 50.0) == 0.0
    assert calculate_percentile([120.0], 50.0) == 120.0
    assert calculate_percentile([100.0, 200.0, 300.0], 50.0) == 200.0

    # 10 sorted latency samples: 10, 20, 30, ..., 100
    samples = [float(i * 10) for i in range(1, 11)]
    p50 = calculate_percentile(samples, 50.0)
    p95 = calculate_percentile(samples, 95.0)

    assert p50 == 55.0
    assert p95 == 95.5


@pytest.mark.django_db
def test_record_job_metric_privacy_and_rtf(standard_user):
    """VC-090: Ensure metric records RTF, latencies, and STRICTLY protects user speech privacy."""
    now = timezone.now()
    created = now - timedelta(seconds=12)
    started = now - timedelta(seconds=10)
    completed = now

    job = GenerationJob.objects.create(
        user=standard_user,
        model_id="openvoice_v2",
        language="uz",
        input_text="Maxfiy shaxsiy foydalanuvchi audio matni va parollari.",
        status=GenerationJob.STATUS_SUCCEEDED,
        started_at=started,
        completed_at=completed,
    )
    # simulate creation timestamp
    GenerationJob.objects.filter(id=job.id).update(created_at=created)
    job.refresh_from_db()

    # Generate metric for 5.0 seconds of audio generated in 10.0 seconds compute
    metric = record_job_metric(job, audio_duration_sec=5.0)

    assert metric.job_id == job.id
    assert metric.user_id == standard_user.id
    assert metric.model_id == "openvoice_v2"
    assert metric.language == "uz"
    assert metric.status == "SUCCEEDED"
    assert metric.error_category == "NONE"

    # Latencies
    assert metric.queue_latency_ms >= 1900.0
    assert metric.compute_latency_ms >= 9900.0
    assert metric.total_latency_ms >= 11900.0

    # RTF = compute_sec / audio_sec = 10.0 / 5.0 = 2.0
    assert metric.rtf is not None
    assert round(metric.rtf, 1) == 2.0

    # STRICT PRIVACY CHECK: Neither the input_text nor raw audio exists in OperationalMetric
    metric_fields = [f.name for f in OperationalMetric._meta.get_fields()]
    assert "input_text" not in metric_fields
    assert "audio" not in metric_fields
    assert "audio_file" not in metric_fields
    assert metric.char_count == len("Maxfiy shaxsiy foydalanuvchi audio matni va parollari.")


@pytest.mark.django_db
def test_get_beta_analytics_summary_aggregation(standard_user):
    """VC-090: Test aggregate reporting across multiple simulated jobs and models."""
    # Create 3 metrics: 2 succeeded, 1 failed
    OperationalMetric.objects.create(
        job_id=uuid.uuid4(),
        user_id=standard_user.id,
        model_id="openvoice_v2",
        language="uz",
        status="SUCCEEDED",
        char_count=50,
        audio_duration_sec=10.0,
        compute_latency_ms=3000.0,
        total_latency_ms=3500.0,
        rtf=0.30,
        error_category="NONE",
    )
    OperationalMetric.objects.create(
        job_id=uuid.uuid4(),
        user_id=standard_user.id,
        model_id="openvoice_v2",
        language="en",
        status="SUCCEEDED",
        char_count=80,
        audio_duration_sec=8.0,
        compute_latency_ms=2400.0,
        total_latency_ms=2800.0,
        rtf=0.30,
        error_category="NONE",
    )
    OperationalMetric.objects.create(
        job_id=uuid.uuid4(),
        user_id=standard_user.id,
        model_id="anadil_uzbek_tts",
        language="uz",
        status="FAILED",
        char_count=30,
        audio_duration_sec=0.0,
        compute_latency_ms=100.0,
        total_latency_ms=500.0,
        rtf=None,
        error_category="GPU_BUSY_503",
    )

    summary = get_beta_analytics_summary(period="all")

    assert summary["total_jobs"] == 3
    assert summary["succeeded_jobs"] == 2
    assert summary["failed_jobs"] == 1
    assert summary["success_rate_percent"] == 66.7
    assert summary["failure_rate_percent"] == 33.3

    assert summary["by_language"]["uz"] == 2
    assert summary["by_language"]["en"] == 1
    assert summary["by_model"]["openvoice_v2"] == 2
    assert summary["by_model"]["anadil_uzbek_tts"] == 1
    assert summary["by_error_category"]["GPU_BUSY_503"] == 1

    # RTF
    assert summary["rtf"]["samples_count"] == 2
    assert summary["rtf"]["p50_rtf"] == 0.30

    # Privacy verification block
    assert summary["privacy_compliance"]["speech_content_logged"] is False
    assert summary["privacy_compliance"]["pii_logged"] is False


@pytest.mark.django_db
def test_beta_analytics_api_permissions_and_response(api_client, standard_user, admin_user):
    """VC-090: Verify endpoint security: Anonymous/Standard users denied, Admin granted."""
    url = "/api/v1/audit/analytics/beta/"

    # 1. Anonymous access -> Denied (401 or 403)
    resp_anon = api_client.get(url)
    assert resp_anon.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # 2. Standard user access -> 403 Forbidden
    api_client.force_authenticate(user=standard_user)
    resp_user = api_client.get(url)
    assert resp_user.status_code == status.HTTP_403_FORBIDDEN

    # 3. Admin / Staff access -> 200 OK
    api_client.force_authenticate(user=admin_user)
    resp_admin = api_client.get(url)
    assert resp_admin.status_code == status.HTTP_200_OK
    data = resp_admin.json()
    assert "total_jobs" in data
    assert "success_rate_percent" in data
    assert "latency_ms" in data
    assert "rtf" in data
    assert "privacy_compliance" in data
    assert data["privacy_compliance"]["speech_content_logged"] is False

    # 4. Filter by period query param
    resp_period = api_client.get(f"{url}?period=7d")
    assert resp_period.status_code == status.HTTP_200_OK
    assert resp_period.json()["period"] == "7d"


@pytest.mark.django_db
def test_celery_task_logs_telemetry_metric(standard_user):
    """VC-090: Verify Celery task automatically records telemetry metric on consent failure."""
    from apps.generations.tasks import process_speech_synthesis_job
    from apps.voices.models import VoiceProfile

    voice = VoiceProfile.objects.create(owner=standard_user, name="Unconsented Voice", language="uz")
    # No ConsentRecord created, has_verified_consent is False

    job = GenerationJob.objects.create(
        user=standard_user,
        voice_profile=voice,
        model_id="openvoice_v2",
        language="uz",
        input_text="Sinov matni.",
        status=GenerationJob.STATUS_PENDING,
    )

    result = process_speech_synthesis_job(str(job.id))
    assert result["status"] == "FAILED"

    # Verify an OperationalMetric was logged for this job
    metric = OperationalMetric.objects.filter(job_id=job.id).first()
    assert metric is not None
    assert metric.status == "FAILED"
    assert metric.error_category == "CONSENT_DENIED"
    assert metric.model_id == "openvoice_v2"
    assert metric.language == "uz"


@pytest.mark.django_db
def test_rate_generation_job_endpoint(api_client, standard_user, admin_user):
    """VC-091: Test beta quality rating endpoint (1-5 stars) and audit logging."""
    from apps.audio.models import AudioAsset
    from apps.audit.models import AuditEvent
    from apps.generations.models import GeneratedAudio

    # 1. Setup completed job with GeneratedAudio
    job = GenerationJob.objects.create(
        user=standard_user,
        model_id="openvoice_v2",
        language="uz",
        input_text="Baholash testi.",
        status=GenerationJob.STATUS_SUCCEEDED,
    )
    asset = AudioAsset.objects.create(
        owner=standard_user,
        original_filename="rated_audio.wav",
        file="audio/2026/10/rated_audio.wav",
        duration_sec=4.5,
        asset_type=AudioAsset.TYPE_GENERATED,
    )
    generated_audio = GeneratedAudio.objects.create(
        job=job,
        asset=asset,
        duration_sec=4.5,
    )

    rate_url = f"/api/v1/generations/jobs/{job.id}/rate/"

    # Unauthenticated -> Denied (401 or 403)
    resp_unauth = api_client.post(rate_url, {"quality_rating": 5})
    assert resp_unauth.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # Authenticated as other user (admin or stranger) -> 404 (ownership protection)
    api_client.force_authenticate(user=admin_user)
    resp_stranger = api_client.post(rate_url, {"quality_rating": 5})
    assert resp_stranger.status_code == status.HTTP_404_NOT_FOUND

    # Authenticated as owner
    api_client.force_authenticate(user=standard_user)

    # Invalid rating (out of range 1-5)
    resp_invalid = api_client.post(rate_url, {"quality_rating": 6})
    assert resp_invalid.status_code == status.HTTP_400_BAD_REQUEST
    assert resp_invalid.json()["error_code"] == "INVALID_RATING"

    # Valid rating (5 stars with notes)
    resp_valid = api_client.post(
        rate_url,
        {
            "quality_rating": 5,
            "feedback_notes": "Ovoz tembri juda tabiiy va tiniq chiqdi.",
        },
    )
    assert resp_valid.status_code == status.HTTP_200_OK
    assert resp_valid.json()["status"] == "RATED"
    assert resp_valid.json()["quality_rating"] == 5

    # Check database persistence
    generated_audio.refresh_from_db()
    assert generated_audio.quality_rating == 5

    # Check AuditEvent
    audit = AuditEvent.objects.filter(
        actor=standard_user,
        action="AUDIO_QUALITY_RATED",
        target_id=str(generated_audio.id),
    ).first()
    assert audit is not None
    assert audit.metadata["rating"] == 5
    assert audit.metadata["feedback_notes"] == "Ovoz tembri juda tabiiy va tiniq chiqdi."

