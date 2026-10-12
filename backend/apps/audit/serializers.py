from rest_framework import serializers

from .models import AbuseReport, AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    """Read-only serializer for security audit trail."""

    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "actor",
            "actor_username",
            "action",
            "ip_address",
            "target_model",
            "target_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class AbuseReportSerializer(serializers.ModelSerializer):
    """Detailed serializer for abuse complaints and compliance status."""

    reporter_username = serializers.CharField(source="reporter.username", read_only=True)

    class Meta:
        model = AbuseReport
        fields = [
            "id",
            "reporter",
            "reporter_username",
            "reported_voice_id",
            "reported_job_id",
            "reason",
            "details",
            "status",
            "resolution_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reporter", "reporter_username", "created_at", "updated_at"]


class CreateAbuseReportSerializer(serializers.ModelSerializer):
    """Input serializer for filing an ethical abuse / infringement report."""

    class Meta:
        model = AbuseReport
        fields = [
            "id",
            "reported_voice_id",
            "reported_job_id",
            "reason",
            "details",
        ]
        read_only_fields = ["id"]

    def validate_reason(self, value):
        reason = value.strip()
        if not reason:
            raise serializers.ValidationError("Reason cannot be blank.")
        return reason

    def create(self, validated_data):
        validated_data["reporter"] = self.context["request"].user
        return super().create(validated_data)
