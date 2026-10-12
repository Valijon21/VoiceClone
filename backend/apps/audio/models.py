"""AudioAsset metadata model representing audio files in storage abstraction."""

import uuid

from django.conf import settings
from django.db import models


class AudioAsset(models.Model):
    """Metadata and storage reference for audio assets."""

    TYPE_REFERENCE = "REFERENCE_VOICE"
    TYPE_GENERATED = "GENERATED_OUTPUT"
    TYPE_CONSENT = "CONSENT_RECORDING"

    TYPE_CHOICES = [
        (TYPE_REFERENCE, "Reference Voice Sample"),
        (TYPE_GENERATED, "Generated Output Audio"),
        (TYPE_CONSENT, "Consent Voice Declaration"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="audio_assets",
    )
    file = models.FileField(upload_to="audio/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    duration_sec = models.FloatField(default=0.0)
    sample_rate = models.PositiveIntegerField(default=24000)
    channels = models.PositiveSmallIntegerField(default=1)
    sha256_checksum = models.CharField(max_length=64, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    asset_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_REFERENCE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audio_asset"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.duration_sec}s) - {self.asset_type}"
