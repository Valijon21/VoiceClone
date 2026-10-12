"""Tests for project environment hygiene, license configuration, and directory layout."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def test_monorepo_directories_exist():
    """Verify that all core monorepo services and docs exist with READMEs."""
    expected_dirs = ["backend", "frontend", "inference", "infra", "docs"]
    for dir_name in expected_dirs:
        dir_path = BASE_DIR / dir_name
        assert dir_path.is_dir(), f"Expected directory '{dir_name}' not found."
        readme_path = dir_path / "README.md"
        assert readme_path.is_file(), f"Missing README.md in '{dir_name}'."


def test_env_example_has_critical_keys():
    """Ensure .env.example contains essential configuration keys."""
    env_example = BASE_DIR / ".env.example"
    assert env_example.is_file(), ".env.example does not exist"

    content = env_example.read_text(encoding="utf-8")
    critical_keys = [
        "DJANGO_SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "INFERENCE_BASE_URL",
        "MEDIA_ROOT",
        "CONSENT_STRICT_MODE",
    ]
    for key in critical_keys:
        assert f"{key}=" in content, f"Key '{key}' is missing in .env.example"


def test_gitignore_protects_secrets_and_weights():
    """Ensure .gitignore prevents committing secrets, virtual environments, and weights."""
    gitignore = BASE_DIR / ".gitignore"
    assert gitignore.is_file(), ".gitignore does not exist"

    content = gitignore.read_text(encoding="utf-8")
    critical_patterns = [".env", ".venv", "*.pth", "*.safetensors", ".cache"]
    for pattern in critical_patterns:
        assert pattern in content, f"Pattern '{pattern}' missing in .gitignore"


def test_model_licenses_file_exists():
    """Ensure MODEL_LICENSES.md exists and contains verified license gates."""
    licenses_file = BASE_DIR / "MODEL_LICENSES.md"
    assert licenses_file.is_file(), "MODEL_LICENSES.md not found"

    content = licenses_file.read_text(encoding="utf-8")
    assert "OpenVoice" in content
    assert "MIT" in content
