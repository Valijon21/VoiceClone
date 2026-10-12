from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Public serialized user profile."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_verified", "created_at"]
        read_only_fields = ["id", "is_verified", "created_at"]


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
