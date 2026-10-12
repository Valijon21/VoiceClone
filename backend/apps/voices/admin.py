"""Django admin configuration for voices app (Consent & Voice Profiles)."""

from django.contrib import admin

from .models import ConsentRecord, VoiceProfile


@admin.register(VoiceProfile)
class VoiceProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "language", "is_active", "has_verified_consent", "created_at")
    list_filter = ("language", "is_active", "created_at")
    search_fields = ("name", "owner__username", "owner__email")
    ordering = ("-created_at",)


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "voice_profile", "user", "status", "consented_at", "revoked_at")
    list_filter = ("status", "consented_at")
    search_fields = ("user__username", "voice_profile__name", "consent_text")
    ordering = ("-consented_at",)
