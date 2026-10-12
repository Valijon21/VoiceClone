"""Comprehensive tests for Django Domain Models, Consent Gate, State Machine, and REST API (Phase 04)."""

import os

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_user(db):
    user = User.objects.create_user(
        username="testuser",
        email="testuser@voiceclone.ai",
        password="ValidPassword123!",
        is_verified=True,
    )
    return user


@pytest.fixture
def authed_client(api_client, auth_user):
    api_client.force_authenticate(user=auth_user)
    return api_client


@pytest.mark.django_db
def test_user_registration(api_client):
    """Verify user registration endpoint creates accounts with unique emails (VC-041)."""
    payload = {
        "username": "new_author",
        "email": "author@example.com",
        "password": "SecurePassword987!",
    }
    response = api_client.post("/api/v1/accounts/register/", data=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(email="author@example.com").exists()


@pytest.mark.django_db
def test_consent_gate_blocks_generation_without_consent(authed_client, auth_user):
    """Enforce Consent Gate: A voice profile without verified consent CANNOT be synthesized (VC-042)."""
    from apps.voices.models import VoiceProfile

    # 1. Create a voice profile without consent
    voice = VoiceProfile.objects.create(
        owner=auth_user,
        name="My Personal Voice",
        language="uz",
    )
    assert voice.has_verified_consent is False

    # 2. Attempt to create a generation job
    payload = {
        "voice_profile": str(voice.id),
        "model_id": "openvoice_v2",
        "language": "uz",
        "input_text": "Sinov audiosi yaratish.",
    }
    response = authed_client.post("/api/v1/generations/jobs/", data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "consent" in str(response.data)


@pytest.mark.django_db
def test_consent_gate_permits_generation_after_verification(authed_client, auth_user):
    """Once legal consent is recorded, speech synthesis job is accepted (VC-042, VC-044)."""
    from apps.voices.models import VoiceProfile

    voice = VoiceProfile.objects.create(owner=auth_user, name="Verified Voice", language="uz")

    # Record verified consent
    consent_resp = authed_client.post(
        f"/api/v1/voices/{voice.id}/consent/",
        data={"consent_text": "Men o‘z ovozimdan foydalanishga to‘liq rozilik beraman."},
    )
    assert consent_resp.status_code == status.HTTP_201_CREATED
    voice.refresh_from_db()
    assert voice.has_verified_consent is True

    # Dispatch generation job
    job_payload = {
        "voice_profile": str(voice.id),
        "model_id": "openvoice_v2",
        "language": "uz",
        "input_text": "Assalomu alaykum, rozilik tekshirildi.",
    }
    job_resp = authed_client.post("/api/v1/generations/jobs/", data=job_payload)
    assert job_resp.status_code == status.HTTP_201_CREATED
    assert job_resp.data["status"] == "PENDING"


@pytest.mark.django_db
def test_model_license_gate_rejects_unapproved_model(authed_client):
    """Unapproved models must fail the license gate (VC-045)."""
    payload = {
        "model_id": "unapproved_proprietary_model",
        "language": "uz",
        "input_text": "Matn sintezi.",
    }
    response = authed_client.post("/api/v1/generations/jobs/", data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "MODEL_LICENSES.md" in str(response.data)


@pytest.mark.django_db
def test_state_machine_transitions(auth_user):
    """State machine prevents illegal status transitions (VC-044)."""
    from apps.generations.models import GenerationJob
    from apps.generations.state_machine import InvalidStateTransitionError

    job = GenerationJob.objects.create(
        user=auth_user,
        model_id="openvoice_v2",
        language="uz",
        input_text="Test transition",
    )
    assert job.status == "PENDING"

    # Legal: PENDING -> RUNNING
    job.transition_to("RUNNING")
    assert job.status == "RUNNING"
    assert job.started_at is not None

    # Legal: RUNNING -> SUCCEEDED
    job.transition_to("SUCCEEDED")
    assert job.status == "SUCCEEDED"
    assert job.completed_at is not None

    # Illegal: SUCCEEDED -> RUNNING must raise
    with pytest.raises(InvalidStateTransitionError):
        job.transition_to("RUNNING")


@pytest.mark.django_db
def test_audio_storage_service(auth_user):
    """Storage service computes SHA256 checksum and abstracts disk writes (VC-043)."""
    from apps.audio.models import AudioAsset
    from apps.audio.storage import AudioStorageService

    dummy_audio = b"RIFF" + b"\x00" * 40
    asset = AudioStorageService.save_audio_bytes(
        user=auth_user,
        filename="test_sample.wav",
        audio_bytes=dummy_audio,
        duration_sec=1.5,
        asset_type=AudioAsset.TYPE_REFERENCE,
    )
    assert asset.owner == auth_user
    assert len(asset.sha256_checksum) == 64
    assert asset.size_bytes == len(dummy_audio)


@pytest.mark.django_db
def test_openapi_schema_endpoint(api_client):
    """OpenAPI schema is exposed at /api/schema/ (VC-047)."""
    response = api_client.get("/api/schema/")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"] == "3.1.0"
    assert "/api/v1/voices/" in data["paths"]
