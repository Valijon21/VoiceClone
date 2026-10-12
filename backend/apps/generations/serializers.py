from rest_framework import serializers

from apps.audio.serializers import AudioAssetSerializer

from .models import GeneratedAudio, GenerationJob

APPROVED_MODELS = {"openvoice_v2", "mock_voice_adapter", "anadil_uzbek_tts"}


class GeneratedAudioSerializer(serializers.ModelSerializer):
    """Output audio serializer with asset metadata."""

    asset = AudioAssetSerializer(read_only=True)

    class Meta:
        model = GeneratedAudio
        fields = ["id", "asset", "duration_sec", "quality_rating", "created_at"]


class GenerationJobSerializer(serializers.ModelSerializer):
    """Serializer representing synthesis job status and result."""

    result_audio = GeneratedAudioSerializer(read_only=True)

    class Meta:
        model = GenerationJob
        fields = [
            "id",
            "voice_profile",
            "model_id",
            "language",
            "input_text",
            "status",
            "progress_percent",
            "error_message",
            "idempotency_key",
            "result_audio",
            "created_at",
            "started_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "progress_percent",
            "error_message",
            "result_audio",
            "created_at",
            "started_at",
            "completed_at",
        ]


class CreateGenerationJobSerializer(serializers.ModelSerializer):
    """Input serializer enforcing the Consent Gate and Model License Gate."""

    class Meta:
        model = GenerationJob
        fields = [
            "id",
            "voice_profile",
            "model_id",
            "language",
            "input_text",
            "idempotency_key",
        ]
        read_only_fields = ["id"]

    def validate_model_id(self, value):
        """Enforce Model License Gate on submission."""
        if value not in APPROVED_MODELS:
            raise serializers.ValidationError(
                f"Model '{value}' is not approved for production use. Check MODEL_LICENSES.md."
            )
        return value

    def validate_input_text(self, value):
        """Enforce input text boundaries."""
        text = value.strip()
        if not text:
            raise serializers.ValidationError("Input text cannot be blank or whitespace only.")
        if len(text) > 1000:
            raise serializers.ValidationError(
                "Input text exceeds maximum limit of 1000 characters."
            )
        return text

    def validate(self, attrs):
        user = self.context["request"].user
        voice_profile = attrs.get("voice_profile")

        # Consent Gate Enforcement:
        if voice_profile:
            if voice_profile.owner != user:
                raise serializers.ValidationError(
                    {"voice_profile": "You do not own this voice profile."}
                )
            if not voice_profile.has_verified_consent:
                raise serializers.ValidationError(
                    {
                        "voice_profile": "Voice profile does not have an active, verified consent record."
                    }
                )

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        idempotency_key = validated_data.get("idempotency_key")

        # Idempotency Gate
        if idempotency_key:
            existing = GenerationJob.objects.filter(
                user=user, idempotency_key=idempotency_key
            ).first()
            if existing:
                return existing

        validated_data["user"] = user
        return super().create(validated_data)
