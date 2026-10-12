"""GenerationJob and GeneratedAudio domain models."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from .state_machine import validate_transition


class GenerationJob(models.Model):
    """Asynchronous speech synthesis task tracking lifecycle and worker output."""

    STATUS_PENDING = "PENDING"
    STATUS_RUNNING = "RUNNING"
    STATUS_SUCCEEDED = "SUCCEEDED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Queue"),
        (STATUS_RUNNING, "In Progress"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generation_jobs",
    )
    voice_profile = models.ForeignKey(
        "voices.VoiceProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generation_jobs",
    )
    model_id = models.CharField(max_length=80, default="openvoice_v2")
    language = models.CharField(max_length=10, default="uz")
    input_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    idempotency_key = models.CharField(max_length=120, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "generations_job"
        ordering = ["-created_at"]

    def transition_to(self, new_status: str, error: str = "") -> None:
        """Safely transition job status via state machine."""
        validate_transition(self.status, new_status)
        self.status = new_status
        if error:
            self.error_message = error
        if new_status == self.STATUS_RUNNING and not self.started_at:
            self.started_at = timezone.now()
        elif new_status == self.STATUS_SUCCEEDED:
            self.progress_percent = 100
            self.completed_at = timezone.now()
        elif new_status in (self.STATUS_FAILED, self.STATUS_CANCELLED):
            self.completed_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "error_message",
                "progress_percent",
                "started_at",
                "completed_at",
                "updated_at",
            ]
        )


class GeneratedAudio(models.Model):
    """Final rendered audio asset associated with a successful GenerationJob."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name="result_audio",
    )
    asset = models.OneToOneField(
        "audio.AudioAsset",
        on_delete=models.CASCADE,
        related_name="generation_result",
    )
    duration_sec = models.FloatField(default=0.0)
    quality_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "generations_audio"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Audio for Job {self.job.id} ({self.duration_sec}s)"
