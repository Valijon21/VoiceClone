"""Security and compliance audit event models."""

import uuid

from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Immutable audit trail for consent declarations, deletions, and high-privilege actions."""

    ACTION_CONSENT_GRANTED = "CONSENT_GRANTED"
    ACTION_CONSENT_REVOKED = "CONSENT_REVOKED"
    ACTION_VOICE_CREATED = "VOICE_CREATED"
    ACTION_VOICE_DELETED = "VOICE_DELETED"
    ACTION_GENERATION_DISPATCHED = "GENERATION_DISPATCHED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=64, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    target_model = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_event"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.created_at}] {self.action} by {self.actor}"
