"""Django admin configuration for audio assets."""

from django.contrib import admin

from .models import AudioAsset


@admin.register(AudioAsset)
class AudioAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "original_filename", "asset_type", "duration_sec", "created_at")
    list_filter = ("asset_type", "created_at")
    search_fields = ("owner__username", "original_filename")
    ordering = ("-created_at",)
