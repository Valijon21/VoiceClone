"""Storage abstraction decoupling views from file storage backends (Local vs S3)."""

import hashlib

from django.core.files.base import ContentFile

from .models import AudioAsset


class AudioStorageService:
    """Service handling asset creation, checksum computation, and storage retrieval."""

    @classmethod
    def save_audio_bytes(
        cls,
        user,
        filename: str,
        audio_bytes: bytes,
        duration_sec: float = 0.0,
        sample_rate: int = 24000,
        channels: int = 1,
        asset_type: str = AudioAsset.TYPE_REFERENCE,
    ) -> AudioAsset:
        """Save raw audio bytes into configured storage backend and create metadata record."""
        checksum = hashlib.sha256(audio_bytes).hexdigest()
        content_file = ContentFile(audio_bytes, name=filename)

        asset = AudioAsset.objects.create(
            owner=user,
            file=content_file,
            original_filename=filename,
            duration_sec=duration_sec,
            sample_rate=sample_rate,
            channels=channels,
            sha256_checksum=checksum,
            size_bytes=len(audio_bytes),
            asset_type=asset_type,
        )
        return asset

    @classmethod
    def get_download_url(cls, asset: AudioAsset) -> str:
        """Return public or signed URL for audio download."""
        if not asset.file:
            return ""
        return asset.file.url
