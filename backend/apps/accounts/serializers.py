from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Public serialized user profile including quota and subscription details (VC-100)."""

    remaining_seconds = serializers.FloatField(read_only=True)
    is_owner_or_unlimited = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_verified",
            "plan",
            "is_unlimited",
            "audio_seconds_quota",
            "audio_seconds_used",
            "remaining_seconds",
            "is_owner_or_unlimited",
            "is_staff",
            "is_superuser",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "plan",
            "is_unlimited",
            "audio_seconds_quota",
            "audio_seconds_used",
            "remaining_seconds",
            "is_owner_or_unlimited",
            "is_staff",
            "is_superuser",
            "created_at",
        ]


class UsageLedgerSerializer(serializers.ModelSerializer):
    """Immutable audit trail serializer for quota operations."""

    class Meta:
        from .models import UsageLedger

        model = UsageLedger
        fields = [
            "id",
            "operation",
            "delta_seconds",
            "balance_after_seconds",
            "job_id",
            "notes",
            "created_at",
        ]
        read_only_fields = fields


class AdminPlanUpdateSerializer(serializers.Serializer):
    """Owner/Admin serializer to grant unlimited access, upgrade plans, or adjust quota."""

    plan = serializers.ChoiceField(choices=User.PLAN_CHOICES, required=False)
    is_unlimited = serializers.BooleanField(required=False)
    audio_seconds_quota = serializers.IntegerField(min_value=0, required=False)
    bonus_seconds = serializers.IntegerField(min_value=0, required=False)
    note = serializers.CharField(max_length=255, default="Admin quota adjustment")


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user
