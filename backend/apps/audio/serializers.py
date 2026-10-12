from rest_framework import serializers

from .models import AudioAsset


class AudioAssetSerializer(serializers.ModelSerializer):
    """Public serialized representation of AudioAsset."""

    download_url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = AudioAsset
        fields = [
            "id",
            "original_filename",
            "download_url",
            "duration_sec",
            "sample_rate",
            "channels",
            "size_bytes",
            "asset_type",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "download_url",
            "duration_sec",
            "sample_rate",
            "channels",
            "size_bytes",
            "created_at",
        ]
