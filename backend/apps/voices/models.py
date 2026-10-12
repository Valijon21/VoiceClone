"""VoiceProfile and ConsentRecord models enforcing the strict Consent Gate."""

import uuid

from django.conf import settings
from django.db import models


class VoiceProfile(models.Model):
    """User-owned voice profile containing speaker metadata and feature embeddings."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="voice_profiles",
    )
    name = models.CharField(max_length=120, help_text="Friendly label for the voice profile")
    language = models.CharField(
        max_length=10, default="uz", help_text="Primary spoken language (uz, en, ru)"
    )
    speaker_embedding = models.BinaryField(
        null=True, blank=True, help_text="Tone color or speaker vector bytes"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "voices_voice_profile"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.language}) by {self.owner.username}"

    @property
    def has_verified_consent(self) -> bool:
        """Return True if voice has an active, verified consent record."""
        return hasattr(self, "consent") and self.consent.is_valid


class ConsentRecord(models.Model):
    """Immutable audit record proving explicit user consent to synthesize and clone voice."""

    STATUS_PENDING = "PENDING"
    STATUS_VERIFIED = "VERIFIED"
    STATUS_REVOKED = "REVOKED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Verification"),
        (STATUS_VERIFIED, "Verified & Active"),
        (STATUS_REVOKED, "Revoked by User"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    voice_profile = models.OneToOneField(
        VoiceProfile,
        on_delete=models.CASCADE,
        related_name="consent",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consent_records",
    )
    consent_text = models.TextField(
        help_text="Exact legal text presented to and agreed by the user.",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_VERIFIED,
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    consented_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "voices_consent_record"
        ordering = ["-consented_at"]

    def __str__(self) -> str:
        return f"Consent for {self.voice_profile.name} [{self.status}]"

    @property
    def is_valid(self) -> bool:
        return self.status == self.STATUS_VERIFIED and self.revoked_at is None
