"""Security, Consent Gate, Throttling, Quotas, and Abuse Reporting Tests (VC-070 to VC-079)."""

import pytest
from apps.audit.models import AuditEvent
from apps.voices.models import ConsentRecord, VoiceProfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def test_user():
    return User.objects.create_user(
        username="sec_user_1",
        email="sec1@example.com",
        password="TestPassword123!",
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        username="sec_user_2",
        email="sec2@example.com",
        password="TestPassword123!",
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username="sec_admin",
        email="admin@example.com",
        password="AdminPassword123!",
    )


@pytest.fixture
def client_user(test_user):
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client


@pytest.mark.django_db
def test_consent_gate_strictly_enforced_on_backend(client_user, test_user, other_user):
    """VC-070: Verify generation strictly fails if voice lacks consent or belongs to another user."""
    # 1. Voice profile without consent
    unconsented_voice = VoiceProfile.objects.create(
        owner=test_user,
        name="Unconsented Voice",
        language="uz",
    )

    resp = client_user.post(
        "/api/v1/generations/jobs/",
        {
            "input_text": "Salom dunyo",
            "language": "uz",
            "model_id": "openvoice_v2",
            "voice_profile": str(unconsented_voice.id),
        },
    )
    assert resp.status_code == 400
    details = resp.data.get("details", resp.data)
    assert "voice_profile" in details

    # 2. Voice profile owned by another user
    other_voice = VoiceProfile.objects.create(
        owner=other_user,
        name="Other Voice",
        language="uz",
    )
    ConsentRecord.objects.create(
        voice_profile=other_voice,
        user=other_user,
        consent_text="Other user consent",
        status=ConsentRecord.STATUS_VERIFIED,
    )

    resp2 = client_user.post(
        "/api/v1/generations/jobs/",
        {
            "input_text": "Salom dunyo",
            "language": "uz",
            "model_id": "openvoice_v2",
            "voice_profile": str(other_voice.id),
        },
    )
    assert resp2.status_code == 400
    details2 = resp2.data.get("details", resp2.data)
    assert "voice_profile" in details2


@pytest.mark.django_db
def test_audio_upload_validation_and_malformed_rejection(client_user):
    """VC-072: Verify upload rejects malformed WAV, tiny files, and oversized files."""
    # 1. Tiny file (< 44 bytes)
    tiny_file = SimpleUploadedFile("tiny.wav", b"too small", content_type="audio/wav")
    resp_tiny = client_user.post("/api/v1/audio/", {"file": tiny_file}, format="multipart")
    assert resp_tiny.status_code == 400
    assert resp_tiny.data["error_code"] == "MALFORMED_AUDIO_FILE"

    # 2. Malformed WAV header (not starting with RIFF/WAVE)
    fake_wav_data = b"DUMMY_HEADER" + b"\x00" * 50
    fake_wav = SimpleUploadedFile("fake.wav", fake_wav_data, content_type="audio/wav")
    resp_fake = client_user.post("/api/v1/audio/", {"file": fake_wav}, format="multipart")
    assert resp_fake.status_code == 400
    assert resp_fake.data["error_code"] == "MALFORMED_AUDIO_FILE"

    # 3. Invalid extension and MIME
    invalid_txt = SimpleUploadedFile(
        "malicious.exe", b"A" * 100, content_type="application/octet-stream"
    )
    resp_inv = client_user.post("/api/v1/audio/", {"file": invalid_txt}, format="multipart")
    assert resp_inv.status_code == 415

    # 4. Valid WAV format (passes validation)
    valid_wav_header = (
        b"RIFF"
        + b"\x24\x00\x00\x00"
        + b"WAVE"
        + b"fmt "
        + b"\x10\x00\x00\x00"
        + b"\x01\x00\x01\x00"
        + b"\x44\xac\x00\x00"
        + b"\x88\x58\x01\x00"
        + b"\x02\x00\x10\x00"
        + b"data"
        + b"\x00\x00\x00\x00"
    )
    valid_file = SimpleUploadedFile("valid.wav", valid_wav_header, content_type="audio/wav")
    resp_valid = client_user.post("/api/v1/audio/", {"file": valid_file}, format="multipart")
    assert resp_valid.status_code == 201


@pytest.mark.django_db
def test_text_input_boundaries_and_sanitization(client_user):
    """VC-072: Verify text boundaries (whitespace-only and > 1000 chars are rejected)."""
    # 1. Whitespace only
    resp_empty = client_user.post(
        "/api/v1/generations/jobs/",
        {
            "input_text": "     \n\t  ",
            "language": "uz",
            "model_id": "openvoice_v2",
        },
    )
    assert resp_empty.status_code == 400
    details_empty = resp_empty.data.get("details", resp_empty.data)
    assert "input_text" in details_empty

    # 2. Text exceeding 1000 characters
    long_text = "A" * 1050
    resp_long = client_user.post(
        "/api/v1/generations/jobs/",
        {
            "input_text": long_text,
            "language": "uz",
            "model_id": "openvoice_v2",
        },
    )
    assert resp_long.status_code == 400
    details_long = resp_long.data.get("details", resp_long.data)
    assert "input_text" in details_long


@pytest.mark.django_db
def test_ai_generated_provenance_headers(client_user):
    """VC-076: Verify AI disclosure headers are set on generation requests."""
    resp = client_user.post(
        "/api/v1/generations/jobs/",
        {
            "input_text": "Valid test text for synthesis provenance.",
            "language": "en",
            "model_id": "openvoice_v2",
        },
    )
    assert resp.status_code == 201
    assert resp.headers.get("X-AI-Generated") == "true"
    assert resp.headers.get("X-VoiceClone-Ethical-Gate") == "STRICT"


@pytest.mark.django_db
def test_abuse_reporting_and_audit_event_logging(client_user, test_user, admin_user):
    """VC-073, VC-074: Verify filing abuse complaints and recording audit events."""
    # 1. User submits an abuse report
    resp = client_user.post(
        "/api/v1/audit/reports/",
        {
            "reason": "Suspicious voice impersonation attempt",
            "details": "This profile appears to impersonate a public official without consent.",
            "reported_voice_id": "test_voice_123",
        },
    )
    assert resp.status_code == 201
    report_id = resp.data["id"]

    # 2. Verify AuditEvent is created
    audit_event = AuditEvent.objects.filter(
        actor=test_user,
        action=AuditEvent.ACTION_REPORT_SUBMITTED,
        target_id=str(report_id),
    ).first()
    assert audit_event is not None
    assert audit_event.metadata["reason"] == "Suspicious voice impersonation attempt"

    # 3. User can view their own reports
    list_resp = client_user.get("/api/v1/audit/reports/")
    assert list_resp.status_code == 200
    assert any(r["id"] == report_id for r in list_resp.data["results"])

    # 4. Standard user cannot resolve report
    patch_resp = client_user.patch(f"/api/v1/audit/reports/{report_id}/", {"status": "RESOLVED"})
    assert patch_resp.status_code == 403

    # 5. Admin can resolve report
    admin_client = APIClient()
    admin_client.force_authenticate(user=admin_user)
    admin_resp = admin_client.patch(
        f"/api/v1/audit/reports/{report_id}/",
        {"status": "RESOLVED", "resolution_notes": "Profile investigated and revoked."},
    )
    assert admin_resp.status_code == 200
    assert admin_resp.data["status"] == "RESOLVED"

    # 6. Verify resolution audit event
    resolve_audit = AuditEvent.objects.filter(
        actor=admin_user,
        action=AuditEvent.ACTION_REPORT_RESOLVED,
        target_id=str(report_id),
    ).first()
    assert resolve_audit is not None
    assert resolve_audit.metadata["status"] == "RESOLVED"
