"""Model Cache, Download and Checksum Verification Manager (VC-081)."""

import hashlib
import logging
import os
from pathlib import Path

logger = logging.getLogger("voiceclone.inference.model_manager")


class ModelChecksumError(Exception):
    """Raised when model weights fail SHA-256 integrity verification."""

    pass


class ModelWeightsNotFoundError(FileNotFoundError):
    """Raised when required model checkpoint is missing from local cache."""

    pass


class ModelManager:
    """Manages model weights caching, integrity verification, and local offline readiness."""

    def __init__(self, cache_dir: Path | None = None):
        if cache_dir is None:
            raw_path = os.getenv("MODEL_CACHE_DIR", "d:/Proyekt/voiceclone/.cache/models")
            self.cache_dir = Path(raw_path).resolve()
        else:
            self.cache_dir = Path(cache_dir).resolve()

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute the SHA-256 checksum of a file in 64KB chunks."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()

    def verify_weights(self, weights_path: Path, expected_sha256: str | None = None) -> bool:
        """Verify presence and cryptographic checksum of a model file."""
        if not weights_path.exists():
            raise ModelWeightsNotFoundError(
                f"Model checkpoint not found at: {weights_path}. Run model download procedure first."
            )

        if expected_sha256:
            actual_sha256 = self.compute_sha256(weights_path)
            if actual_sha256.lower() != expected_sha256.lower():
                raise ModelChecksumError(
                    f"Integrity check failed for {weights_path.name}!\n"
                    f"Expected SHA256: {expected_sha256}\n"
                    f"Actual SHA256:   {actual_sha256}\n"
                    "Corrupted file detected. Please re-download the model weights."
                )

        return True

    def get_model_path(self, model_filename: str) -> Path:
        """Return absolute path for a model checkpoint inside local cache."""
        return self.cache_dir / model_filename

    def list_cached_models(self) -> dict[str, dict]:
        """List all valid weight files currently available in local cache."""
        models = {}
        for p in self.cache_dir.glob("*"):
            if p.is_file() and p.suffix in [".pth", ".pt", ".bin", ".safetensors", ".onnx"]:
                models[p.name] = {
                    "path": str(p),
                    "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
                    "suffix": p.suffix,
                }
        return models
