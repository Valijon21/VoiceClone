"""Unit and integration tests for Plan, Quota, Usage Ledger, and Owner Unlimited Bypass (VC-100)."""

from unittest.mock import MagicMock, patch

import pytest
from apps.accounts.models import UsageLedger, User
from apps.generations.models import GenerationJob
from apps.voices.models import ConsentRecord, VoiceProfile
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def standard_user(db):
    """Standard free trial user with 300s quota."""
    return User.objects.create_user(
        username="standard_user_quota",
        email="quota_user@voiceclone.local",
        password="ValidPassword123!",
        plan=User.PLAN_FREE,
        audio_seconds_quota=300,
        audio_seconds_used=0.0,
    )


@pytest.fixture
def exhausted_user(db):
    """User who has consumed all their available quota."""
    return User.objects.create_user(
        username="exhausted_user",
        email="exhausted@voiceclone.local",
        password="ValidPassword123!",
        plan=User.PLAN_FREE,
        audio_seconds_quota=300,
        audio_seconds_used=300.0,
    )


@pytest.fixture
def vip_unlimited_user(db):
    """Whitelisted friend / VIP user with permanent unlimited access."""
    return User.objects.create_user(
        username="vip_friend",
        email="vip@voiceclone.local",
        password="ValidPassword123!",
        plan=User.PLAN_UNLIMITED,
        is_unlimited=True,
    )


@pytest.fixture
def owner_admin_user(db):
    """Platform owner superuser with unrestricted access."""
    return User.objects.create_superuser(
        username="platform_owner",
        email="owner@voiceclone.local",
        password="OwnerSuperPassword123!",
    )


@pytest.fixture
def verified_voice_profile(db, standard_user):
    """Verified voice profile for synthesis."""
    profile = VoiceProfile.objects.create(
        owner=standard_user,
        name="Standard Quota Voice",
        language="uz",
        speaker_embedding=b"dummy_emb_bytes",
    )
    ConsentRecord.objects.create(
        voice_profile=profile,
        user=standard_user,
        consent_text="Legal declaration of ownership.",
        status=ConsentRecord.STATUS_VERIFIED,
    )
    return profile


# =========================================================================
# Model Logic Tests
# =========================================================================


@pytest.mark.django_db
def test_quota_model_properties_standard_user(standard_user):
    """Verify standard user quota calculation and balance."""
    assert not standard_user.is_owner_or_unlimited
    assert standard_user.remaining_seconds == 300.0
    assert standard_user.has_available_quota(10.0) is True
    assert standard_user.has_available_quota(301.0) is False

    standard_user.audio_seconds_used = 295.0
    assert standard_user.remaining_seconds == 5.0
    assert standard_user.has_available_quota(5.0) is True
    assert standard_user.has_available_quota(5.1) is False


@pytest.mark.django_db
def test_owner_and_vip_unlimited_properties(owner_admin_user, vip_unlimited_user):
    """Verify owner and VIP users bypass all limits permanently."""
    assert owner_admin_user.is_owner_or_unlimited is True
    assert owner_admin_user.remaining_seconds == -1.0
    assert owner_admin_user.has_available_quota(999999.0) is True

    assert vip_unlimited_user.is_owner_or_unlimited is True
    assert vip_unlimited_user.remaining_seconds == -1.0
    assert vip_unlimited_user.has_available_quota(999999.0) is True


# =========================================================================
# Quota Gate Enforcement on API Submission
# =========================================================================


# =========================================================================
# Quota Gate Enforcement on API Submission
# =========================================================================


@pytest.mark.django_db
def test_quota_exhausted_user_rejected_on_submission(api_client, exhausted_user):
    """Exhausted user receives a 400 validation error stating quota is reached."""
    profile = VoiceProfile.objects.create(
        owner=exhausted_user,
        name="Exhausted Voice Profile",
        language="uz",
        speaker_embedding=b"dummy_emb_bytes",
    )
    ConsentRecord.objects.create(
        voice_profile=profile,
        user=exhausted_user,
        consent_text="Legal declaration of ownership.",
        status=ConsentRecord.STATUS_VERIFIED,
    )

    api_client.force_authenticate(user=exhausted_user)
    payload = {
        "voice_profile": str(profile.id),
        "model_id": "openvoice_v2",
        "language": "uz",
        "input_text": "Salom, bu mening sinov audiodir.",
    }
    resp = api_client.post("/api/v1/generations/jobs/", payload, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert "quota" in data["details"]
    assert "Quota limit reached" in data["details"]["quota"][0]


@pytest.mark.django_db
def test_unlimited_user_bypasses_quota_gate(api_client, vip_unlimited_user):
    """VIP or Owner user with is_unlimited=True can submit without quota restrictions."""
    profile = VoiceProfile.objects.create(
        owner=vip_unlimited_user,
        name="VIP Voice Profile",
        language="uz",
        speaker_embedding=b"dummy_emb_bytes",
    )
    ConsentRecord.objects.create(
        voice_profile=profile,
        user=vip_unlimited_user,
        consent_text="Legal declaration of ownership.",
        status=ConsentRecord.STATUS_VERIFIED,
    )

    api_client.force_authenticate(user=vip_unlimited_user)
    payload = {
        "voice_profile": str(profile.id),
        "model_id": "openvoice_v2",
        "language": "uz",
        "input_text": "VIP foydalanuvchi uchun cheksiz sintez tekshiruvi.",
    }
    with patch("apps.generations.tasks.process_speech_synthesis_job.delay"):
        resp = api_client.post("/api/v1/generations/jobs/", payload, format="json")
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["status"] == "PENDING"


# =========================================================================
# Ledger Accounting in Synthesis Tasks
# =========================================================================


@pytest.mark.django_db
def test_synthesis_task_debits_quota_for_standard_user(standard_user, verified_voice_profile):
    """Standard user has seconds debited and SYNTHESIS_DEBIT written to UsageLedger."""
    from apps.generations.tasks import process_speech_synthesis_job

    job = GenerationJob.objects.create(
        user=standard_user,
        voice_profile=verified_voice_profile,
        model_id="mock_voice_adapter",
        language="uz",
        input_text="Salom dunyo",
        status=GenerationJob.STATUS_PENDING,
    )

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
        "duration_sec": 8.5,
        "sample_rate": 24000,
    }

    with patch("httpx.Client.post", return_value=fake_resp):
        res = process_speech_synthesis_job(str(job.id))

    assert res["status"] == "SUCCEEDED"
    standard_user.refresh_from_db()
    assert standard_user.audio_seconds_used == 8.5
    assert standard_user.remaining_seconds == 291.5

    # Check UsageLedger entry
    ledger = UsageLedger.objects.filter(user=standard_user).first()
    assert ledger is not None
    assert ledger.operation == UsageLedger.OPERATION_DEBIT
    assert ledger.delta_seconds == -8.5
    assert ledger.balance_after_seconds == 291.5


@pytest.mark.django_db
def test_synthesis_task_unlimited_bypass_ledger(vip_unlimited_user):
    """VIP unlimited user records UNLIMITED_BYPASS in ledger without debiting seconds."""
    from apps.generations.tasks import process_speech_synthesis_job

    profile = VoiceProfile.objects.create(
        owner=vip_unlimited_user,
        name="VIP Voice Profile",
        language="uz",
        speaker_embedding=b"dummy_emb_bytes",
    )
    ConsentRecord.objects.create(
        voice_profile=profile,
        user=vip_unlimited_user,
        consent_text="Legal declaration of ownership.",
        status=ConsentRecord.STATUS_VERIFIED,
    )

    job = GenerationJob.objects.create(
        user=vip_unlimited_user,
        voice_profile=profile,
        model_id="mock_voice_adapter",
        language="uz",
        input_text="VIP cheksiz generatsiya",
        status=GenerationJob.STATUS_PENDING,
    )

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
        "duration_sec": 15.0,
        "sample_rate": 24000,
    }

    with patch("httpx.Client.post", return_value=fake_resp):
        res = process_speech_synthesis_job(str(job.id))

    assert res["status"] == "SUCCEEDED"
    vip_unlimited_user.refresh_from_db()
    assert vip_unlimited_user.audio_seconds_used == 0.0  # Unchanged

    ledger = UsageLedger.objects.filter(user=vip_unlimited_user).first()
    assert ledger is not None
    assert ledger.operation == UsageLedger.OPERATION_UNLIMITED_BYPASS
    assert ledger.delta_seconds == 0.0


# =========================================================================
# Quota API Endpoints & Admin Granting Tests
# =========================================================================


@pytest.mark.django_db
def test_quota_status_endpoint(api_client, standard_user):
    """Authenticated user can fetch their plan, quota, remaining seconds, and ledger."""
    api_client.force_authenticate(user=standard_user)
    resp = api_client.get("/api/v1/accounts/quota/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["username"] == standard_user.username
    assert data["plan"] == "FREE"
    assert data["audio_seconds_quota"] == 300
    assert data["remaining_seconds"] == 300.0
    assert data["is_owner_or_unlimited"] is False
    assert isinstance(data["recent_ledger"], list)


@pytest.mark.django_db
def test_admin_can_grant_unlimited_access_to_user(api_client, owner_admin_user, standard_user):
    """Owner/Admin can promote any user to VIP unlimited status or upgrade quota."""
    url = f"/api/v1/accounts/users/{standard_user.id}/plan/"

    # 1. Non-admin cannot access (403 Forbidden)
    api_client.force_authenticate(user=standard_user)
    resp_forbidden = api_client.patch(url, {"is_unlimited": True})
    assert resp_forbidden.status_code == status.HTTP_403_FORBIDDEN

    # 2. Owner/Admin upgrades user to UNLIMITED plan and sets is_unlimited=True
    api_client.force_authenticate(user=owner_admin_user)
    payload = {
        "plan": User.PLAN_UNLIMITED,
        "is_unlimited": True,
        "note": "Owner granted permanent unlimited testing pass",
    }
    resp_admin = api_client.patch(url, payload, format="json")
    assert resp_admin.status_code == status.HTTP_200_OK
    data = resp_admin.json()
    assert data["status"] == "success"
    assert data["user"]["is_unlimited"] is True
    assert data["user"]["is_owner_or_unlimited"] is True

    # 3. Check target user state in DB
    standard_user.refresh_from_db()
    assert standard_user.is_unlimited is True
    assert standard_user.plan == User.PLAN_UNLIMITED

    # 4. Check UsageLedger audit record
    ledger = UsageLedger.objects.filter(
        user=standard_user, operation=UsageLedger.OPERATION_OVERRIDE
    ).first()
    assert ledger is not None
    assert "Owner granted permanent unlimited testing pass" in ledger.notes
