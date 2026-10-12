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
    ACTION_AUDIO_UPLOADED = "AUDIO_UPLOADED"
    ACTION_AUDIO_DELETED = "AUDIO_DELETED"
    ACTION_GENERATION_DISPATCHED = "GENERATION_DISPATCHED"
    ACTION_USER_BLOCKED = "USER_BLOCKED"
    ACTION_USER_UNBLOCKED = "USER_UNBLOCKED"
    ACTION_REPORT_SUBMITTED = "REPORT_SUBMITTED"
    ACTION_REPORT_RESOLVED = "REPORT_RESOLVED"

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


class AbuseReport(models.Model):
    """User report and complaint workflow against non-consensual voice usage or impersonation."""

    STATUS_PENDING = "PENDING"
    STATUS_UNDER_REVIEW = "UNDER_REVIEW"
    STATUS_RESOLVED = "RESOLVED"
    STATUS_DISMISSED = "DISMISSED"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_DISMISSED, "Dismissed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reported_abuses",
    )
    reported_voice_id = models.CharField(max_length=64, blank=True)
    reported_job_id = models.CharField(max_length=64, blank=True)
    reason = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "abuse_report"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Report {self.id} [{self.status}] by {self.reporter}"


class OperationalMetric(models.Model):
    """
    Privacy-preserving telemetry record for speech synthesis jobs (VC-090).
    Captures operational performance, latency, RTF, and failure categories
    WITHOUT storing any private speech content or text prompts.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    model_id = models.CharField(max_length=80, db_index=True)
    language = models.CharField(max_length=10, db_index=True)
    status = models.CharField(max_length=20, db_index=True)  # SUCCEEDED, FAILED, CANCELLED

    char_count = models.PositiveIntegerField(default=0)
    audio_duration_sec = models.FloatField(default=0.0)
    queue_latency_ms = models.FloatField(default=0.0)
    compute_latency_ms = models.FloatField(default=0.0)
    total_latency_ms = models.FloatField(default=0.0)
    rtf = models.FloatField(null=True, blank=True)  # Real-Time Factor: compute_sec / audio_sec

    error_category = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_operational_metric"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Metric [{self.status}] job={self.job_id} rtf={self.rtf}"
