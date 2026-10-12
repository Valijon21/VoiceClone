"""Django admin configuration for audit and abuse reports."""

from django.contrib import admin

from .models import AbuseReport, AuditEvent, OperationalMetric


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("id", "actor", "action", "target_model", "target_id", "created_at")
    list_filter = ("action", "target_model", "created_at")
    search_fields = ("actor__username", "action", "target_id")
    ordering = ("-created_at",)


@admin.register(AbuseReport)
class AbuseReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reporter__username", "reason", "reported_voice_id", "reported_job_id")
    ordering = ("-created_at",)


@admin.register(OperationalMetric)
class OperationalMetricAdmin(admin.ModelAdmin):
    list_display = (
        "job_id",
        "user_id",
        "model_id",
        "language",
        "status",
        "audio_duration_sec",
        "compute_latency_ms",
        "rtf",
        "created_at",
    )
    list_filter = ("status", "model_id", "language", "error_category")
    search_fields = ("job_id", "user_id")
    ordering = ("-created_at",)
