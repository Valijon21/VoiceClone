from rest_framework import serializers

from .models import ConsentRecord, VoiceProfile


class ConsentRecordSerializer(serializers.ModelSerializer):
    """Serializer for user consent agreements."""

    class Meta:
        model = ConsentRecord
        fields = [
            "id",
            "voice_profile",
            "consent_text",
            "status",
            "consented_at",
            "revoked_at",
            "is_valid",
        ]
        read_only_fields = ["id", "consented_at", "revoked_at", "is_valid"]


class VoiceProfileSerializer(serializers.ModelSerializer):
    """Serializer for voice profiles."""

    has_consent = serializers.BooleanField(source="has_verified_consent", read_only=True)
    consent = ConsentRecordSerializer(read_only=True)

    class Meta:
        model = VoiceProfile
        fields = [
            "id",
            "name",
            "language",
            "is_active",
            "has_consent",
            "consent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "has_consent", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
