"""Django admin configuration for generations app."""

from django.contrib import admin

from .models import GeneratedAudio, GenerationJob


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "voice_profile",
        "model_id",
        "language",
        "status",
        "progress_percent",
        "created_at",
    )
    list_filter = ("status", "model_id", "language", "created_at")
    search_fields = ("user__username", "input_text", "idempotency_key")
    ordering = ("-created_at",)


@admin.register(GeneratedAudio)
class GeneratedAudioAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "duration_sec", "quality_rating", "created_at")
    list_filter = ("quality_rating", "created_at")
    search_fields = ("job__id", "job__user__username")
    ordering = ("-created_at",)
