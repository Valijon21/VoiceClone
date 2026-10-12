"""Frontend Architecture, Types and Smoke Verification Tests (VC-060 to VC-069)."""

import json
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def test_frontend_config_and_manifest_files():
    """Verify all vital frontend config and manifest files exist and are valid (VC-060)."""
    assert (FRONTEND_DIR / "package.json").is_file()
    assert (FRONTEND_DIR / "tsconfig.json").is_file()
    assert (FRONTEND_DIR / "vite.config.ts").is_file()
    assert (FRONTEND_DIR / "index.html").is_file()

    with open(FRONTEND_DIR / "package.json", encoding="utf-8") as f:
        pkg = json.load(f)
        assert pkg["name"] == "voiceclone-frontend"
        assert "react" in pkg["dependencies"]
        assert "typescript" in pkg["devDependencies"]

    with open(FRONTEND_DIR / "index.html", encoding="utf-8") as f:
        html = f.read()
        assert 'id="root"' in html
        assert 'src="/src/main.tsx"' in html
        assert "VoiceClone AI" in html


def test_frontend_type_definitions():
    """Verify TypeScript type definitions align with backend domain models (VC-060, VC-061)."""
    types_file = FRONTEND_DIR / "src" / "types" / "index.ts"
    assert types_file.is_file()

    content = types_file.read_text(encoding="utf-8")
    expected_interfaces = [
        "interface User",
        "interface ConsentRecord",
        "interface VoiceProfile",
        "interface AudioAsset",
        "interface GeneratedAudio",
        "interface GenerationJob",
        "interface ApprovedModel",
    ]
    for iface in expected_interfaces:
        assert iface in content, f"Missing TypeScript interface: {iface}"


def test_frontend_api_client_methods():
    """Verify frontend API client provides all necessary endpoint connectors (VC-060, VC-062, VC-065)."""
    client_file = FRONTEND_DIR / "src" / "api" / "client.ts"
    assert client_file.is_file()

    content = client_file.read_text(encoding="utf-8")
    expected_methods = [
        "register(",
        "login(",
        "logout(",
        "getMe(",
        "getVoices(",
        "createVoice(",
        "provideConsent(",
        "deleteVoice(",
        "uploadAudio(",
        "getApprovedModels(",
        "getJobs(",
        "createJob(",
        "getJobById(",
    ]
    for method in expected_methods:
        assert method in content, f"Missing API method: {method}"


def test_frontend_component_coverage():
    """Verify all required UI components exist and contain core domain logic (VC-061 to VC-068)."""
    components_dir = FRONTEND_DIR / "src" / "components"
    assert components_dir.is_dir()

    expected_components = {
        "Navbar.tsx": ["Consent Gate: STRICT", "VoiceClone AI"],
        "AuthModal.tsx": ["Tizimga kirish", "Ro‘yxatdan o‘tish", "api.login", "api.register"],
        "ConsentModal.tsx": ["Rozilik Deklaratsiyasi", "hasAgreed", "provideConsent"],
        "VoiceRecorder.tsx": ["MediaRecorder", "startRecording", "stopRecording", "uploadAudio"],
        "SynthesisForm.tsx": ["O‘zbekcha (Lotin", "createJob", "idempotencyKey"],
        "JobProgressBar.tsx": ["getJobById", "progress_percent", "SUCCEEDED", "FAILED"],
        "AudioPlayer.tsx": ["<audio", "waveform", "WAV yuklab olish"],
        "VoiceProfilesList.tsx": ["deleteVoice", "has_consent", "O‘chirish"],
        "GenerationHistory.tsx": ["input_text", "download_url", "Sintezlangan audio tarixi"],
    }

    for comp_name, markers in expected_components.items():
        comp_file = components_dir / comp_name
        assert comp_file.is_file(), f"Component file missing: {comp_name}"
        comp_content = comp_file.read_text(encoding="utf-8")
        for marker in markers:
            assert marker in comp_content, f"Marker '{marker}' missing in {comp_name}"


def test_frontend_app_and_main_entrypoint():
    """Verify App.tsx and main.tsx assemble the dashboard (VC-060, VC-069)."""
    app_file = FRONTEND_DIR / "src" / "App.tsx"
    main_file = FRONTEND_DIR / "src" / "main.tsx"
    assert app_file.is_file()
    assert main_file.is_file()

    app_content = app_file.read_text(encoding="utf-8")
    assert "Navbar" in app_content
    assert "SynthesisForm" in app_content
    assert "VoiceRecorder" in app_content
    assert "JobProgressBar" in app_content
    assert "AudioPlayer" in app_content
    assert "VoiceProfilesList" in app_content
    assert "GenerationHistory" in app_content

    main_content = main_file.read_text(encoding="utf-8")
    assert "createRoot" in main_content
    assert "<App />" in main_content


@pytest.mark.django_db
def test_django_login_and_logout_endpoints():
    """Verify backend login and logout endpoints work with frontend authentication flow (VC-062)."""
    user = User.objects.create_user(
        username="frontend_user",
        email="frontend@example.com",
        password="ValidPassword123!",
    )

    client = APIClient()

    # 1. Login with bad credentials
    bad_login = client.post(
        "/api/v1/accounts/login/", {"username": "frontend_user", "password": "wrong"}
    )
    assert bad_login.status_code == 401

    # 2. Login with valid credentials
    login_resp = client.post(
        "/api/v1/accounts/login/",
        {"username": "frontend_user", "password": "ValidPassword123!"},
    )
    assert login_resp.status_code == 200
    assert login_resp.data["username"] == "frontend_user"

    # 3. Access authenticated endpoint
    me_resp = client.get("/api/v1/accounts/me/")
    assert me_resp.status_code == 200
    assert me_resp.data["id"] == str(user.id)

    # 4. Logout
    logout_resp = client.post("/api/v1/accounts/logout/")
    assert logout_resp.status_code == 200
    assert logout_resp.data["status"] == "logged_out"
