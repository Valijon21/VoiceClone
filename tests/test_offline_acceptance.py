"""Offline Acceptance and Local Packaging Tests (VC-080 to VC-084)."""

import socket
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from inference.app.core.hardware import detect_hardware_capabilities
from inference.app.core.model_manager import (
    ModelChecksumError,
    ModelManager,
    ModelWeightsNotFoundError,
)
from inference.app.core.text_normalizer import UzbekTextNormalizer
from inference.app.main import app

client = TestClient(app)
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def test_hardware_detection_and_diagnostics():
    """VC-083: Test hardware detection inspects GPU/CPU and provides friendly diagnostics."""
    info = detect_hardware_capabilities()
    assert "accelerator" in info
    assert "device_name" in info
    assert "vram_total_mb" in info
    assert "recommended_device" in info
    assert "warnings" in info

    # Test /hardware FastAPI endpoint
    resp = client.get("/hardware")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"
    assert "accelerator" in data


def test_model_manager_checksum_and_cache_integrity():
    """VC-081: Test model weights manager computes hashes, verifies checksums, and detects corruption."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = ModelManager(cache_dir=Path(tmp_dir))

        # 1. Create a dummy model weights file
        test_weights = manager.cache_dir / "test_model.pth"
        test_weights.write_bytes(b"PYTORCH_WEIGHTS_VERSION_1_0_DUMMY_BINARY_DATA")

        # 2. Checksum computation
        computed_hash = manager.compute_sha256(test_weights)
        assert len(computed_hash) == 64

        # 3. Valid checksum verification
        assert manager.verify_weights(test_weights, expected_sha256=computed_hash) is True

        # 4. Checksum mismatch raises ModelChecksumError
        with pytest.raises(ModelChecksumError) as exc_info:
            manager.verify_weights(test_weights, expected_sha256="deadbeef" * 8)
        assert "Integrity check failed" in str(exc_info.value)

        # 5. Missing weights raises ModelWeightsNotFoundError
        missing_weights = manager.cache_dir / "nonexistent.pth"
        with pytest.raises(ModelWeightsNotFoundError):
            manager.verify_weights(missing_weights)

        # 6. Listing cached models
        cached = manager.list_cached_models()
        assert "test_model.pth" in cached
        assert cached["test_model.pth"]["suffix"] == ".pth"


def test_offline_acceptance_scenario_no_internet_calls():
    """VC-082: Verify synthesis operates fully offline with ZERO external internet network calls."""

    # Guard against any outbound socket connections
    def guarded_connect(*args, **kwargs):
        raise ConnectionRefusedError(
            "Offline acceptance test: outbound internet connection attempted!"
        )

    with patch.object(socket, "create_connection", side_effect=guarded_connect):
        # 1. Test offline text normalizer
        raw_text = "Bugun 2026-yil 12-oktabr! O'zbekiston 100% tayyor."
        normalized = UzbekTextNormalizer.normalize(raw_text, language="uz")
        assert "ikki ming yigirma olti" in normalized
        assert "o‘n ikki" in normalized or "o'n ikki" in normalized

        # 2. Test local mock speech synthesis without internet
        resp = client.post(
            "/synthesize",
            json={
                "text": "Salom, bu to'liq offline acceptance test.",
                "language": "uz",
                "adapter_id": "mock_voice_adapter",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["duration_sec"] > 0
        assert data["audio_base64"]


def test_local_startup_scripts_exist_and_configured():
    """VC-080: Verify unified local startup scripts exist and contain required environment parameters."""
    ps1_script = SCRIPTS_DIR / "start_local.ps1"
    sh_script = SCRIPTS_DIR / "start_local.sh"

    assert ps1_script.is_file()
    assert sh_script.is_file()

    ps1_content = ps1_script.read_text(encoding="utf-8")
    assert "start_local.ps1" in ps1_content
    assert "HF_HOME" in ps1_content
    assert "manage.py" in ps1_content

    sh_content = sh_script.read_text(encoding="utf-8")
    assert "HF_HOME" in sh_content
    assert "manage.py" in sh_content
